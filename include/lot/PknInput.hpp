#pragma once

#include "lot/InjectionSchedule.hpp"
#include "lot/LeakoffModel.hpp"

namespace lss::lot {

enum class PknPressureModel { PknDirect, VolumetricBalance };

struct BreakdownConfig {
  BreakdownMethod method = BreakdownMethod::PressureThreshold;
  double pressure_Pa = 0.0;
};

struct PknInput {
  InjectionSchedule injection;
  LeakoffConfig leakoff;
  BreakdownConfig breakdown;
  double fracture_height_m = 0.0;
  double initial_width_m = 0.0;
  double net_pressure_Pa = 0.0;
  double plane_strain_modulus_Pa = 0.0;
  double fluid_viscosity_Pa_s = 0.0;
  double leakoff_coefficient_m_sqrt_s = 0.0;
  double leakoff_constant_rate_m3_s = 0.0;
  PknPressureModel pressure_model = PknPressureModel::PknDirect;
  double annular_volume_m3 = 0.0;
  double fluid_compressibility_per_Pa = 0.0;
};

}  // namespace lss::lot
