#pragma once

#include <memory>
#include <string>

#include "lot/InjectionSchedule.hpp"
#include "lot/LeakoffModel.hpp"
#include "lot/SigmaThetaProvider.hpp"

namespace lss::lot {

enum class PknPressureModel { PknDirect, VolumetricBalance };

enum class FractureSinkTiming { SameStep, NextStep };

struct BreakdownConfig {
  BreakdownMethod method = BreakdownMethod::PressureThreshold;
  double pressure_Pa = 0.0;
};

enum class FractureInitiationCriterion {
  ConstantPressure,
  SigmaThetaStatic,
  SigmaThetaProviderRuntime,
};

struct SigmaThetaFractureCriterion {
  bool enabled = false;
  std::string layer_id;
  double influence_depth_m = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  std::string source;
  std::string pressure_source;
  std::string comparison;
  std::string mapping_status;
};

struct VolumetricComplianceConfig {
  bool enabled = false;
  std::string model = "none";
  double geometric_compressibility_per_Pa = 0.0;
  double total_compressibility_per_Pa = 0.0;
  double inner_radius_m = 0.0;
  double outer_radius_m = 0.0;
  double inner_wall_thickness_m = 0.0;
  double inner_young_modulus_Pa = 0.0;
  double inner_poisson_ratio = 0.0;
  double formation_young_modulus_Pa = 0.0;
  double formation_poisson_ratio = 0.0;
  std::string mechanical_compliance_status = "none";
  std::string source;
  std::string caveat;
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
  VolumetricComplianceConfig volumetric_compliance;
  double initial_pressure_Pa = 0.0;
  FractureSinkTiming sink_timing = FractureSinkTiming::SameStep;
  FractureInitiationCriterion fracture_initiation =
      FractureInitiationCriterion::ConstantPressure;
  SigmaThetaFractureCriterion sigma_theta_fracture;
  std::shared_ptr<const SigmaThetaProvider> sigma_theta_provider;
};

}  // namespace lss::lot
