#pragma once

#include <memory>

namespace lss::salt {

struct SaltCreepTimeBridgeConfig {
  double inner_radius_m = 0.1556;
  double outer_radius_m = 1.556;
  double height_m = 1.0;
  int radial_elements = 40;

  double elastic_modulus_Pa = 25.0e9;
  double poisson_ratio = 0.30;

  double temperature_K = 350.0;
  double reference_temperature_K = 350.0;
  double alpha_thermal_1_K = 0.0;

  double wall_pressure_Pa = 10.0e6;

  bool geostatic_enabled = false;
  double geostatic_radial_stress_Pa = 0.0;
  double geostatic_hoop_stress_Pa = 0.0;
  double geostatic_vertical_stress_Pa = 0.0;
  bool fix_outer_wall = false;
};

struct SaltCreepTimeBridgeResult {
  double current_time_s = 0.0;
  int step_count = 0;
  double wall_displacement_m = 0.0;
  double radial_closure_m = 0.0;
  double wall_closure_pct = 0.0;
  bool valid = false;
};

class SaltCreepTimeBridge {
 public:
  SaltCreepTimeBridge();
  explicit SaltCreepTimeBridge(SaltCreepTimeBridgeConfig config);
  ~SaltCreepTimeBridge();

  SaltCreepTimeBridge(const SaltCreepTimeBridge&) = delete;
  SaltCreepTimeBridge& operator=(const SaltCreepTimeBridge&) = delete;
  SaltCreepTimeBridge(SaltCreepTimeBridge&&) noexcept;
  SaltCreepTimeBridge& operator=(SaltCreepTimeBridge&&) noexcept;

  [[nodiscard]] bool is_available() const;
  [[nodiscard]] const SaltCreepTimeBridgeConfig& config() const;
  [[nodiscard]] SaltCreepTimeBridgeResult result() const;

  [[nodiscard]] SaltCreepTimeBridgeResult advance_by(double dt_s);
  [[nodiscard]] SaltCreepTimeBridgeResult advance_to(double target_time_s);

 private:
  struct Impl;

  std::unique_ptr<Impl> impl_;
};

}  // namespace lss::salt
