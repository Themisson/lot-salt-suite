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

struct TimeConfig {
  enum class Scheme { Explicit, ImplicitAdaptive };

  double total_h = 0.0;
  double dt_h = 0.0;
  double tol_pressure_bar = 0.0;
  double tol_eq = 0.0;
  double stabilization_h = 0.0;
  Scheme scheme = Scheme::Explicit;
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
  double fracture_height_m = 0.0;
  double fracture_initial_width_m = 0.0;
  std::string breakdown_method;
  double breakdown_pressure_Pa = 0.0;
  bool leakoff_enabled = false;
  std::string leakoff_model;
  double leakoff_coefficient_m_sqrt_s = 0.0;
  double leakoff_constant_rate_m3_s = 0.0;
  std::string detection_method;
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
