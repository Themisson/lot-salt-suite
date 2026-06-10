#pragma once

#include <string>
#include <vector>

namespace lss::core {

// Tensoes usam a convencao geomecanica do legado: compressao positiva.
struct CasingData {
  std::string id;
  double top_m = 0.0;
  double base_m = 0.0;
  double di_m = 0.0;
  double de_m = 0.0;
  double E_Pa = 0.0;
  double nu = 0.0;
};

struct CementData {
  std::string id;
  double top_m = 0.0;
  double base_m = 0.0;
  double di_m = 0.0;
  double de_m = 0.0;
  double E_Pa = 0.0;
  double nu = 0.0;
};

struct FluidData {
  enum class Mode { Constant, HydrostaticDepthProfile };

  std::string id;
  Mode mode = Mode::Constant;
  double density_kg_m3 = 0.0;
  double viscosity_Pa_s = 0.0;
  double compressibility_per_Pa = 0.0;
  double weight_lb_per_gal = 0.0;
  double surface_pressure_Pa = 0.0;
};

struct RockData {
  enum class Model { ElasticIsotropic, DoubleMechanism };

  std::string id;
  Model model = Model::ElasticIsotropic;
  double E_Pa = 0.0;
  double nu = 0.0;
  double density_kg_m3 = 0.0;
  double e0_per_min = 0.0;
  double e0_per_h = 0.0;
  double sig0_Pa = 0.0;
  double T0_degC = 0.0;
  double T0_K = 0.0;
  double n1 = 0.0;
  double n2 = 0.0;
};

struct LayerData {
  std::string id;
  std::string rock_id;
  double top_m = 0.0;
  double base_m = 0.0;
};

struct AnnularData {
  std::string id;
  std::string fluid_id;
  double top_m = 0.0;
  double base_m = 0.0;
};

struct DrillPipeData {
  bool present = false;
  double outer_diameter_m = 0.0;
  double inner_diameter_m = 0.0;
  double depth_m = 0.0;
};

struct WellboreData {
  double airgap_m = 0.0;
  double water_depth_m = 0.0;
  double total_depth_m = 0.0;
  double shoe_depth_m = 0.0;
  DrillPipeData drill_pipe;
};

struct TimeConfig {
  enum class Scheme { Explicit, ImplicitAdaptive };

  double total_h = 0.0;
  double dt_h = 0.0;
  double tol_pressure_bar = 0.0;
  double tol_eq = 0.0;
  double stabilization_h = 0.0;
  Scheme scheme = Scheme::Explicit;
};

struct InjectionPhaseData {
  std::string name = "injection";
  double duration_s = 0.0;
  double rate_m3_s = 0.0;
};

struct SigmaThetaFractureCriterionData {
  bool enabled = false;
  std::string type;
  std::string layer_id;
  double influence_depth_m = 0.0;
  double sigma_theta_compression_positive_Pa = 0.0;
  std::string source;
  std::string pressure_source;
  std::string comparison;
  std::string mapping_status;
};

struct LotConfig {
  bool enabled = false;
  double shoe_depth_m = 0.0;
  std::string model;
  std::string fracture_geometry;
  double fracture_fluid_viscosity_cP = 0.0;
  double fracture_fluid_viscosity_Pa_s = 0.0;
  double injection_rate_m3_s = 0.0;
  double injection_total_time_s = 0.0;
  double injection_dt_s = 0.0;
  double injection_accommodation_time_s = 0.0;
  std::vector<InjectionPhaseData> injection_phases;
  double initial_pressure_Pa = 0.0;
  double fracture_height_m = 0.0;
  double fracture_initial_width_m = 0.0;
  std::string breakdown_method;
  double breakdown_pressure_Pa = 0.0;
  SigmaThetaFractureCriterionData sigma_theta_fracture;
  bool leakoff_enabled = false;
  std::string leakoff_model;
  double leakoff_coefficient_m_sqrt_s = 0.0;
  double leakoff_constant_rate_m3_s = 0.0;
  std::string detection_method;
  std::string pressure_model = "pkn_direct";
};

struct ApbConfig {
  bool enabled = false;
  double top_packer_m = 0.0;
  bool leakage_enabled = false;
  bool venting_enabled = false;
};

struct CaseData {
  std::string name;
  std::string version;
  std::string mode;
  std::string legacy_source;
  WellboreData wellbore;
  std::vector<CasingData> casings;
  std::vector<CementData> cements;
  std::vector<FluidData> fluids;
  std::vector<RockData> rocks;
  std::vector<LayerData> layers;
  std::vector<AnnularData> annulars;
  TimeConfig time;
  LotConfig lot;
  ApbConfig apb;
};

}  // namespace lss::core
