#include "salt/SaltCreepSaltcreepAdapter.hpp"

#include <algorithm>
#include <cmath>
#include <Eigen/Sparse>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "solver/Assembler.hpp"
#include "solver/ElasticSolver.hpp"
#include "solver/WallPressureField.hpp"

namespace lss::salt {
namespace {

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("SaltCreepSaltcreepAdapter: " + field +
                                " must be finite");
  }
}

void validate_query(const SaltCreepQuery& query) {
  require_finite(query.time_s, "time_s");
  require_finite(query.wall_pressure_Pa, "wall_pressure_Pa");
  require_finite(query.temperature_K, "temperature_K");
  require_finite(query.radial_position_m, "radial_position_m");

  if (query.time_s < 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: time_s must be non-negative");
  }
  if (query.wall_pressure_Pa < 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: wall_pressure_Pa must be non-negative");
  }
  if (query.temperature_K <= 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: temperature_K must be positive");
  }
  if (query.radial_position_m < 0.0) {
    throw std::invalid_argument(
        "SaltCreepSaltcreepAdapter: radial_position_m must be non-negative");
  }
}

bool backend_minimum_supported(const SaltCreepAdapterConfig& config) {
  return config.geometry.axisymmetric && config.geometry.plane_strain &&
         config.mesh.axial_elements == 1;
}

std::vector<Stress> build_geostatic_vector(const Mesh& mesh,
                                           const Element& element,
                                           const SaltCreepAdapterConfig& config) {
  const int total_gp =
      mesh.n_elements * static_cast<int>(element.gauss_points().size());
  if (!config.geostatic.enabled) {
    return std::vector<Stress>(total_gp, Stress::Zero());
  }

  const Stress stress{config.geostatic.radial_stress_Pa,
                      config.geostatic.hoop_stress_Pa,
                      config.geostatic.vertical_stress_Pa,
                      0.0};
  return std::vector<Stress>(total_gp, stress);
}

}  // namespace

struct SaltCreepSaltcreepAdapter::BackendCache {
  explicit BackendCache(const SaltCreepAdapterConfig& config)
      : model(config.material.elastic_modulus_Pa,
              config.material.poisson_ratio),
        mesh(build_mesh_L3(config.geometry.inner_radius_m,
                           config.geometry.outer_radius_m,
                           config.mesh.radial_elements,
                           1.0)),
        stiffness(Assembler::assemble_K(mesh, element, model)),
        geostatic_force(Eigen::VectorXd::Zero(mesh.total_dofs())),
        geostatic_enabled(config.geostatic.enabled) {
    if (geostatic_enabled) {
      const auto sigma_geo = build_geostatic_vector(mesh, element, config);
      geostatic_force =
          Assembler::assemble_geostatic_force(mesh, element, sigma_geo);
      fixed_dofs.push_back(mesh.dof_index(mesh.n_nodes - 1, 0));
    }
  }

  AxisymL3 element;
  ElasticIsotropic model;
  Mesh1D mesh;
  Eigen::SparseMatrix<double> stiffness;
  Eigen::VectorXd geostatic_force;
  std::vector<int> fixed_dofs;
  bool geostatic_enabled = false;
};

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter()
    : SaltCreepSaltcreepAdapter(make_default_salt_creep_adapter_config()) {}

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter(
    SaltCreepAdapterConfig config)
    : config_(std::move(config)) {
  config_.validate();
  state_.initialize(config_.time.initial_time_s,
                    config_.wall_pressure.initial_wall_pressure_Pa);
}

SaltCreepSaltcreepAdapter::~SaltCreepSaltcreepAdapter() = default;

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter(
    SaltCreepSaltcreepAdapter&&) noexcept = default;

SaltCreepSaltcreepAdapter& SaltCreepSaltcreepAdapter::operator=(
    SaltCreepSaltcreepAdapter&&) noexcept = default;

bool SaltCreepSaltcreepAdapter::is_available() const {
  return backend_minimum_supported(config_);
}

const SaltCreepAdapterConfig& SaltCreepSaltcreepAdapter::config() const {
  return config_;
}

const SaltCreepAdapterState& SaltCreepSaltcreepAdapter::state() const {
  return state_;
}

int SaltCreepSaltcreepAdapter::backend_build_count() const {
  return backend_build_count_;
}

const SaltCreepSaltcreepAdapter::BackendCache&
SaltCreepSaltcreepAdapter::backend() const {
  if (!backend_cache_) {
    backend_cache_ = std::make_unique<BackendCache>(config_);
    ++backend_build_count_;
  }
  return *backend_cache_;
}

SaltCreepResponse SaltCreepSaltcreepAdapter::evaluate_wall_response(
    const SaltCreepQuery& query) const {
  validate_query(query);
  if (!is_available()) {
    throw std::logic_error(
        "SaltCreepSaltcreepAdapter: minimum backend is unavailable for config");
  }

  const auto& cached_backend = backend();
  const ConstantWallPressureField wall_pressure(query.wall_pressure_Pa);

  auto K = cached_backend.stiffness;
  auto f = Assembler::assemble_boundary_pressure(
      cached_backend.mesh,
      cached_backend.element,
      wall_pressure,
      query.time_s,
      0.0);
  if (cached_backend.geostatic_enabled) {
    f -= cached_backend.geostatic_force;
  }

  const auto solver_result =
      ElasticSolver{}.solve(std::move(K),
                            std::move(f),
                            cached_backend.fixed_dofs);
  const double radial_displacement_m =
      solver_result.u[cached_backend.mesh.dof_index(0, 0)];

  SaltCreepResponse response;
  response.radial_displacement_m = radial_displacement_m;
  response.radial_closure_m =
      radial_closure_from_displacement(response.radial_displacement_m);
  // This is a wall hoop-strain proxy (u/r_i) kept for the minimum backend
  // contract until a future temporal/creep adapter exposes a true du/dr field.
  response.radial_strain =
      response.radial_displacement_m / config_.geometry.inner_radius_m;
  response.effective_closure_pressure_Pa = 0.0;
  response.valid = true;
  state_.record_response(query.time_s, query.wall_pressure_Pa, response);
  return response;
}

double SaltCreepSaltcreepAdapter::radial_closure_from_displacement(
    double radial_displacement_m) {
  require_finite(radial_displacement_m, "radial_displacement_m");
  return std::max(0.0, -radial_displacement_m);
}

}  // namespace lss::salt
