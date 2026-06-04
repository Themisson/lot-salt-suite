#include "salt/SaltCreepTimeBridge.hpp"

#include <algorithm>
#include <cmath>
#include <memory>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "constitutive/elastic_isotropic.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "physics/stress_utils.hpp"
#include "solver/Assembler.hpp"
#include "solver/StressSampler.hpp"
#include "solver/TimeIntegrator.hpp"
#include "solver/WallPressureField.hpp"
#include "thermal/profile_field.hpp"

namespace lss::salt {
namespace {

void require_finite(double value, const std::string& field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument("SaltCreepTimeBridge: " + field +
                                " must be finite");
  }
}

void validate_wall_pressure(double wall_pressure_Pa) {
  require_finite(wall_pressure_Pa, "wall_pressure_Pa");
  if (wall_pressure_Pa < 0.0) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: wall_pressure_Pa must be non-negative");
  }
}

SaltCreepTimeBridgeConfig validate_config(
    SaltCreepTimeBridgeConfig config) {
  require_finite(config.inner_radius_m, "inner_radius_m");
  require_finite(config.outer_radius_m, "outer_radius_m");
  require_finite(config.height_m, "height_m");
  require_finite(config.elastic_modulus_Pa, "elastic_modulus_Pa");
  require_finite(config.poisson_ratio, "poisson_ratio");
  require_finite(config.temperature_K, "temperature_K");
  require_finite(config.reference_temperature_K, "reference_temperature_K");
  require_finite(config.alpha_thermal_1_K, "alpha_thermal_1_K");
  require_finite(config.wall_pressure_Pa, "wall_pressure_Pa");
  require_finite(config.geostatic_radial_stress_Pa,
                 "geostatic_radial_stress_Pa");
  require_finite(config.geostatic_hoop_stress_Pa,
                 "geostatic_hoop_stress_Pa");
  require_finite(config.geostatic_vertical_stress_Pa,
                 "geostatic_vertical_stress_Pa");

  if (config.inner_radius_m <= 0.0) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: inner_radius_m must be positive");
  }
  if (config.outer_radius_m <= config.inner_radius_m) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: outer_radius_m must exceed inner_radius_m");
  }
  if (config.height_m <= 0.0) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: height_m must be positive");
  }
  if (config.radial_elements <= 0) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: radial_elements must be positive");
  }
  if (config.elastic_modulus_Pa <= 0.0) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: elastic_modulus_Pa must be positive");
  }
  if (config.poisson_ratio <= -1.0 || config.poisson_ratio >= 0.5) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: poisson_ratio must be in (-1, 0.5)");
  }
  if (config.temperature_K <= 0.0 || config.reference_temperature_K <= 0.0) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: temperatures must be positive Kelvin values");
  }
  validate_wall_pressure(config.wall_pressure_Pa);
  return config;
}

std::vector<Stress> build_geostatic_vector(const Mesh& mesh,
                                           const Element& element,
                                           const SaltCreepTimeBridgeConfig& config) {
  const int total_gp =
      mesh.n_elements * static_cast<int>(element.gauss_points().size());
  if (!config.geostatic_enabled) {
    return std::vector<Stress>(total_gp, Stress::Zero());
  }

  const Stress stress{config.geostatic_radial_stress_Pa,
                      config.geostatic_hoop_stress_Pa,
                      config.geostatic_vertical_stress_Pa,
                      0.0};
  return std::vector<Stress>(total_gp, stress);
}

std::vector<int> build_fixed_dofs(const Mesh& mesh,
                                  const SaltCreepTimeBridgeConfig& config) {
  if (!config.fix_outer_wall && !config.geostatic_enabled) {
    return {};
  }
  return {mesh.dof_index(mesh.n_nodes - 1, 0)};
}

double positive_closure(double wall_displacement_m) {
  require_finite(wall_displacement_m, "wall_displacement_m");
  return std::max(0.0, -wall_displacement_m);
}

SaltWallStressSample convert_wall_stress_sample(
    const StressSample& sample) {
  SaltWallStressSample out;
  out.gp_id = sample.gp_id;
  out.element_id = sample.element_id;
  out.local_gp_id = sample.local_gp_id;
  out.r_m = sample.r_m;
  out.z_m = sample.z_m;
  out.depth_m = sample.depth_m;
  out.sigma_rr_Pa = sample.sigma[0];
  out.sigma_theta_Pa = sample.sigma[1];
  out.sigma_theta_compression_positive_Pa =
      stress_utils::sigma_theta_compression_positive(sample.sigma);
  out.sigma_zz_Pa = sample.sigma[2];
  out.sigma_rz_Pa = sample.sigma[3];
  out.mean_stress_Pa = sample.mean_stress_Pa;
  out.j2_Pa2 = sample.J2_Pa2;
  out.von_mises_effective_stress_Pa = sample.sigma_ef_Pa;
  return out;
}

class StepWallPressureField final : public WallPressureField {
 public:
  explicit StepWallPressureField(double initial_pressure_Pa)
      : previous_pressure_Pa_(initial_pressure_Pa),
        active_pressure_Pa_(initial_pressure_Pa) {}

  void prepare_step(double switch_time_s, double next_pressure_Pa) {
    validate_wall_pressure(next_pressure_Pa);
    previous_pressure_Pa_ = active_pressure_Pa_;
    active_pressure_Pa_ = next_pressure_Pa;
    switch_time_s_ = switch_time_s;
  }

  void commit_step() {
    previous_pressure_Pa_ = active_pressure_Pa_;
  }

  double pressure_at(const Eigen::Vector2d&, double time_s) const override {
    return time_s <= switch_time_s_ ? previous_pressure_Pa_
                                    : active_pressure_Pa_;
  }

 private:
  double previous_pressure_Pa_ = 0.0;
  double active_pressure_Pa_ = 0.0;
  double switch_time_s_ = 0.0;
};

}  // namespace

struct SaltCreepTimeBridge::Impl {
  explicit Impl(SaltCreepTimeBridgeConfig input_config)
      : config(validate_config(std::move(input_config))),
        model(config.elastic_modulus_Pa, config.poisson_ratio),
        mesh(build_mesh_L3(config.inner_radius_m,
                           config.outer_radius_m,
                           config.radial_elements,
                           config.height_m)),
        thermal(ProfileField::make_constant(config.temperature_K,
                                            config.alpha_thermal_1_K,
                                            config.reference_temperature_K)),
        wall_pressure(
            std::make_shared<StepWallPressureField>(config.wall_pressure_Pa)),
        fixed_dofs(build_fixed_dofs(mesh, config)),
        integrator(make_integrator()) {}

  [[nodiscard]] std::unique_ptr<TimeIntegrator> make_integrator() {
    auto K = Assembler::assemble_K(mesh, element, model);
    auto f = Assembler::assemble_boundary_pressure(
        mesh, element, *wall_pressure, current_time_s, 0.0);
    auto sigma_geo = build_geostatic_vector(mesh, element, config);
    return std::make_unique<TimeIntegrator>(mesh,
                                            element,
                                            model,
                                            thermal,
                                            std::move(K),
                                            std::move(f),
                                            std::move(sigma_geo),
                                            fixed_dofs,
                                            PerformanceStats{},
                                            wall_pressure);
  }

  [[nodiscard]] SaltCreepTimeBridgeResult result() const {
    const double wall_displacement_m = integrator->wall_displacement_m();
    const double closure_m = positive_closure(wall_displacement_m);
    return {
        current_time_s,
        step_count,
        wall_displacement_m,
        closure_m,
        closure_m / config.inner_radius_m * 100.0,
        true,
    };
  }

  [[nodiscard]] SaltWallStressDiagnostics wall_stress_diagnostics() const {
    SaltWallStressDiagnostics diagnostics;
    const auto samples = stress_sampler::sample_wall_gauss_points(
        mesh, element, integrator->state(), 0.0);
    diagnostics.wall_samples.reserve(samples.size());
    for (const auto& sample : samples) {
      diagnostics.wall_samples.push_back(convert_wall_stress_sample(sample));
    }
    diagnostics.valid = !diagnostics.wall_samples.empty();
    return diagnostics;
  }

  SaltCreepTimeBridgeResult advance_by(double dt_s) {
    return advance_by(dt_s, config.wall_pressure_Pa);
  }

  SaltCreepTimeBridgeResult advance_by(double dt_s, double wall_pressure_Pa) {
    require_finite(dt_s, "dt_s");
    validate_wall_pressure(wall_pressure_Pa);
    if (dt_s < 0.0) {
      throw std::invalid_argument(
          "SaltCreepTimeBridge: dt_s must be non-negative");
    }
    if (dt_s == 0.0) {
      wall_pressure->prepare_step(current_time_s, wall_pressure_Pa);
      wall_pressure->commit_step();
      config.wall_pressure_Pa = wall_pressure_Pa;
      return result();
    }
    wall_pressure->prepare_step(current_time_s, wall_pressure_Pa);
    integrator->advance(dt_s);
    current_time_s += dt_s;
    ++step_count;
    wall_pressure->commit_step();
    config.wall_pressure_Pa = wall_pressure_Pa;
    return result();
  }

  SaltCreepTimeBridgeConfig config;
  AxisymL3 element;
  ElasticIsotropic model;
  Mesh1D mesh;
  ProfileField thermal;
  std::shared_ptr<StepWallPressureField> wall_pressure;
  std::vector<int> fixed_dofs;
  double current_time_s = 0.0;
  int step_count = 0;
  std::unique_ptr<TimeIntegrator> integrator;
};

SaltCreepTimeBridge::SaltCreepTimeBridge()
    : SaltCreepTimeBridge(SaltCreepTimeBridgeConfig{}) {}

SaltCreepTimeBridge::SaltCreepTimeBridge(SaltCreepTimeBridgeConfig config)
    : impl_(std::make_unique<Impl>(std::move(config))) {}

SaltCreepTimeBridge::~SaltCreepTimeBridge() = default;

SaltCreepTimeBridge::SaltCreepTimeBridge(SaltCreepTimeBridge&&) noexcept =
    default;

SaltCreepTimeBridge& SaltCreepTimeBridge::operator=(
    SaltCreepTimeBridge&&) noexcept = default;

bool SaltCreepTimeBridge::is_available() const {
  return impl_ != nullptr;
}

const SaltCreepTimeBridgeConfig& SaltCreepTimeBridge::config() const {
  return impl_->config;
}

SaltCreepTimeBridgeResult SaltCreepTimeBridge::result() const {
  return impl_->result();
}

SaltWallStressDiagnostics SaltCreepTimeBridge::wall_stress_diagnostics()
    const {
  return impl_->wall_stress_diagnostics();
}

SaltCreepTimeBridgeResult SaltCreepTimeBridge::advance_by(double dt_s) {
  return impl_->advance_by(dt_s);
}

SaltCreepTimeBridgeResult SaltCreepTimeBridge::advance_by(
    double dt_s,
    double wall_pressure_Pa) {
  return impl_->advance_by(dt_s, wall_pressure_Pa);
}

SaltCreepTimeBridgeResult SaltCreepTimeBridge::advance_to(
    double target_time_s) {
  require_finite(target_time_s, "target_time_s");
  if (target_time_s < impl_->current_time_s) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: target_time_s must be nondecreasing");
  }
  return impl_->advance_by(target_time_s - impl_->current_time_s);
}

SaltCreepTimeBridgeResult SaltCreepTimeBridge::advance_to(
    double target_time_s,
    double wall_pressure_Pa) {
  require_finite(target_time_s, "target_time_s");
  validate_wall_pressure(wall_pressure_Pa);
  if (target_time_s < impl_->current_time_s) {
    throw std::invalid_argument(
        "SaltCreepTimeBridge: target_time_s must be nondecreasing");
  }
  return impl_->advance_by(target_time_s - impl_->current_time_s,
                           wall_pressure_Pa);
}

}  // namespace lss::salt
