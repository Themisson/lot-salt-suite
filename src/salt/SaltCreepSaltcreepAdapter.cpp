#include "salt/SaltCreepSaltcreepAdapter.hpp"

#include <algorithm>
#include <cmath>
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

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter()
    : SaltCreepSaltcreepAdapter(make_default_salt_creep_adapter_config()) {}

SaltCreepSaltcreepAdapter::SaltCreepSaltcreepAdapter(
    SaltCreepAdapterConfig config)
    : config_(std::move(config)) {
  config_.validate();
  state_.initialize(config_.time.initial_time_s,
                    config_.wall_pressure.initial_wall_pressure_Pa);
}

bool SaltCreepSaltcreepAdapter::is_available() const {
  return backend_minimum_supported(config_);
}

const SaltCreepAdapterConfig& SaltCreepSaltcreepAdapter::config() const {
  return config_;
}

const SaltCreepAdapterState& SaltCreepSaltcreepAdapter::state() const {
  return state_;
}

SaltCreepResponse SaltCreepSaltcreepAdapter::evaluate_wall_response(
    const SaltCreepQuery& query) const {
  validate_query(query);
  if (!is_available()) {
    throw std::logic_error(
        "SaltCreepSaltcreepAdapter: minimum backend is unavailable for config");
  }

  AxisymL3 element;
  ElasticIsotropic model(config_.material.elastic_modulus_Pa,
                         config_.material.poisson_ratio);
  Mesh1D mesh = build_mesh_L3(config_.geometry.inner_radius_m,
                              config_.geometry.outer_radius_m,
                              config_.mesh.radial_elements,
                              1.0);
  auto wall_pressure =
      std::make_shared<ConstantWallPressureField>(query.wall_pressure_Pa);

  auto K = Assembler::assemble_K(mesh, element, model);
  auto f = Assembler::assemble_boundary_pressure(
      mesh, element, *wall_pressure, query.time_s, 0.0);
  const auto sigma_geo = build_geostatic_vector(mesh, element, config_);
  if (config_.geostatic.enabled) {
    f -= Assembler::assemble_geostatic_force(mesh, element, sigma_geo);
  }

  std::vector<int> fixed_dofs;
  if (config_.geostatic.enabled) {
    fixed_dofs.push_back(mesh.dof_index(mesh.n_nodes - 1, 0));
  }

  const auto solver_result =
      ElasticSolver{}.solve(std::move(K), std::move(f), fixed_dofs);
  const double radial_displacement_m =
      solver_result.u[mesh.dof_index(0, 0)];

  SaltCreepResponse response;
  response.radial_displacement_m = radial_displacement_m;
  response.radial_closure_m =
      radial_closure_from_displacement(response.radial_displacement_m);
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
