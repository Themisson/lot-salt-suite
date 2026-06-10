#include "io/CaseParser.hpp"

#include <cmath>
#include <stdexcept>
#include <string>
#include <unordered_set>

#include <yaml-cpp/yaml.h>

#include "units/units.hpp"

namespace {

const YAML::Node require_node(const YAML::Node& node, const std::string& path) {
  if (!node) {
    throw std::runtime_error("Campo obrigatorio ausente: " + path);
  }
  return node;
}

template <typename T>
T require_as(const YAML::Node& node, const std::string& path) {
  return require_node(node, path).as<T>();
}

std::string optional_string(const YAML::Node& node, const std::string& path,
                            const std::string& fallback = "") {
  const YAML::Node value = node[path];
  return value ? value.as<std::string>() : fallback;
}

lss::core::FluidData::Mode parse_fluid_mode(const std::string& mode) {
  if (mode == "constant") {
    return lss::core::FluidData::Mode::Constant;
  }
  if (mode == "hydrostatic_depth_profile") {
    return lss::core::FluidData::Mode::HydrostaticDepthProfile;
  }
  throw std::runtime_error("fluid.mode invalido: " + mode);
}

lss::core::RockData::Model parse_rock_model(const std::string& model) {
  if (model == "elastic_isotropic") {
    return lss::core::RockData::Model::ElasticIsotropic;
  }
  if (model == "double_mechanism") {
    return lss::core::RockData::Model::DoubleMechanism;
  }
  throw std::runtime_error("rocks[].model invalido: " + model);
}

lss::core::TimeConfig::Scheme parse_time_scheme(const std::string& scheme) {
  if (scheme == "explicit") {
    return lss::core::TimeConfig::Scheme::Explicit;
  }
  if (scheme == "implicit_adaptive") {
    return lss::core::TimeConfig::Scheme::ImplicitAdaptive;
  }
  throw std::runtime_error("time.scheme invalido: " + scheme);
}

double parse_viscosity_Pa_s(const YAML::Node& node, const std::string& path) {
  if (node["viscosity_cP"]) {
    return units::cP_to_Pa_s(node["viscosity_cP"].as<double>());
  }
  return require_as<double>(node["viscosity_Pa_s"], path + ".viscosity_Pa_s");
}

double parse_value_unit(const YAML::Node& node, const std::string& path,
                        const std::string& quantity) {
  const double value = require_as<double>(node["value"], path + ".value");
  const std::string unit = require_as<std::string>(node["unit"], path + ".unit");

  if (quantity == "rate") {
    if (unit == "m3_s") {
      return value;
    }
    if (unit == "m3_min") {
      return value / 60.0;
    }
    if (unit == "m3_h") {
      return value / 3600.0;
    }
    if (unit == "bbl_min" || unit == "bpm") {
      return value * 0.158987294928 / 60.0;
    }
  }

  if (quantity == "time") {
    if (unit == "s") {
      return value;
    }
    if (unit == "min") {
      return value * 60.0;
    }
    if (unit == "h") {
      return value * 3600.0;
    }
  }

  if (quantity == "length") {
    if (unit == "m") {
      return value;
    }
    if (unit == "in") {
      return units::in_to_m(value);
    }
  }

  if (quantity == "pressure") {
    if (unit == "Pa") {
      return value;
    }
    if (unit == "bar") {
      return units::bar_to_Pa(value);
    }
    if (unit == "psi") {
      return units::psi_to_Pa(value);
    }
  }

  if (quantity == "compressibility") {
    if (unit == "1/Pa") {
      return value;
    }
  }

  throw std::runtime_error("Unidade invalida em " + path + ": " + unit);
}

void validate_nonempty(bool condition, const std::string& field) {
  if (!condition) {
    throw std::runtime_error("Validacao falhou: " + field + " deve conter ao menos 1 item");
  }
}

void parse_wellbore(const YAML::Node& root, lss::core::CaseData& data) {
  const YAML::Node wellbore = require_node(root["wellbore"], "wellbore");
  data.wellbore.airgap_m = require_as<double>(wellbore["airgap_m"], "wellbore.airgap_m");
  data.wellbore.water_depth_m =
      require_as<double>(wellbore["water_depth_m"], "wellbore.water_depth_m");
  data.wellbore.total_depth_m =
      require_as<double>(wellbore["total_depth_m"], "wellbore.total_depth_m");
  data.wellbore.shoe_depth_m =
      require_as<double>(wellbore["shoe_depth_m"], "wellbore.shoe_depth_m");

  if (!wellbore["drill_pipe"]) {
    return;
  }

  const YAML::Node drill_pipe = require_node(wellbore["drill_pipe"], "wellbore.drill_pipe");
  data.wellbore.drill_pipe.present = true;
  data.wellbore.drill_pipe.outer_diameter_m = parse_value_unit(
      drill_pipe["outer_diameter"], "wellbore.drill_pipe.outer_diameter", "length");
  data.wellbore.drill_pipe.inner_diameter_m = parse_value_unit(
      drill_pipe["inner_diameter"], "wellbore.drill_pipe.inner_diameter", "length");
  data.wellbore.drill_pipe.depth_m =
      parse_value_unit(drill_pipe["depth"], "wellbore.drill_pipe.depth", "length");

  const auto& dp = data.wellbore.drill_pipe;
  if (!std::isfinite(dp.outer_diameter_m) || !std::isfinite(dp.inner_diameter_m) ||
      !std::isfinite(dp.depth_m)) {
    throw std::runtime_error("Validacao falhou: wellbore.drill_pipe exige valores finitos");
  }
  if (dp.outer_diameter_m <= 0.0 || dp.inner_diameter_m < 0.0 ||
      dp.outer_diameter_m <= dp.inner_diameter_m) {
    throw std::runtime_error(
        "Validacao falhou: wellbore.drill_pipe exige outer_diameter > inner_diameter >= 0");
  }
  if (dp.depth_m < 0.0) {
    throw std::runtime_error("Validacao falhou: wellbore.drill_pipe.depth deve ser >= 0");
  }
}

void validate_references(const lss::core::CaseData& data) {
  std::unordered_set<std::string> fluid_ids;
  for (const auto& fluid : data.fluids) {
    fluid_ids.insert(fluid.id);
  }

  for (const auto& annular : data.annulars) {
    if (!fluid_ids.contains(annular.fluid_id)) {
      throw std::runtime_error("Validacao falhou: annulars[].fluid '" +
                               annular.fluid_id + "' nao existe em fluids[].id");
    }
  }

  std::unordered_set<std::string> rock_ids;
  for (const auto& rock : data.rocks) {
    rock_ids.insert(rock.id);
  }

  for (const auto& layer : data.layers) {
    if (!rock_ids.contains(layer.rock_id)) {
      throw std::runtime_error("Validacao falhou: layers[].rock '" +
                               layer.rock_id + "' nao existe em rocks[].id");
    }
  }
}

}  // namespace

namespace lss::io {

lss::core::CaseData parse_yaml(const std::filesystem::path& path) {
  const YAML::Node root = YAML::LoadFile(path.string());
  lss::core::CaseData data;

  const YAML::Node metadata = require_node(root["metadata"], "metadata");
  data.name = require_as<std::string>(metadata["name"], "metadata.name");
  data.version = require_as<std::string>(metadata["version"], "metadata.version");
  data.mode = require_as<std::string>(metadata["mode"], "metadata.mode");
  data.legacy_source = optional_string(metadata, "legacy_source");
  if (root["simulation"] && root["simulation"]["mode"]) {
    data.mode = root["simulation"]["mode"].as<std::string>();
  }

  parse_wellbore(root, data);

  for (const auto& node : require_node(root["casings"], "casings")) {
    lss::core::CasingData casing;
    casing.id = require_as<std::string>(node["id"], "casings[].id");
    casing.top_m = require_as<double>(node["top_m"], "casings[].top_m");
    casing.base_m = require_as<double>(node["base_m"], "casings[].base_m");
    casing.di_m = units::in_to_m(require_as<double>(node["di_in"], "casings[].di_in"));
    casing.de_m = units::in_to_m(require_as<double>(node["de_in"], "casings[].de_in"));
    casing.E_Pa = require_as<double>(node["E_Pa"], "casings[].E_Pa");
    casing.nu = require_as<double>(node["nu"], "casings[].nu");
    data.casings.push_back(casing);
  }

  for (const auto& node : require_node(root["cements"], "cements")) {
    lss::core::CementData cement;
    cement.id = require_as<std::string>(node["id"], "cements[].id");
    cement.top_m = require_as<double>(node["top_m"], "cements[].top_m");
    cement.base_m = require_as<double>(node["base_m"], "cements[].base_m");
    cement.di_m = units::in_to_m(require_as<double>(node["di_in"], "cements[].di_in"));
    cement.de_m = units::in_to_m(require_as<double>(node["de_in"], "cements[].de_in"));
    cement.E_Pa = require_as<double>(node["E_Pa"], "cements[].E_Pa");
    cement.nu = require_as<double>(node["nu"], "cements[].nu");
    data.cements.push_back(cement);
  }

  for (const auto& node : require_node(root["fluids"], "fluids")) {
    lss::core::FluidData fluid;
    fluid.id = require_as<std::string>(node["id"], "fluids[].id");
    fluid.mode = parse_fluid_mode(require_as<std::string>(node["mode"], "fluids[].mode"));
    fluid.density_kg_m3 =
        units::ppg_to_kg_m3(require_as<double>(node["density_ppg"], "fluids[].density_ppg"));
    fluid.viscosity_Pa_s = parse_viscosity_Pa_s(node, "fluids[]");
    fluid.compressibility_per_Pa =
        require_as<double>(node["compressibility_per_Pa"],
                           "fluids[].compressibility_per_Pa");
    if (fluid.mode == lss::core::FluidData::Mode::HydrostaticDepthProfile) {
      fluid.weight_lb_per_gal =
          require_as<double>(node["weight_lb_per_gal"], "fluids[].weight_lb_per_gal");
      fluid.surface_pressure_Pa =
          require_as<double>(node["surface_pressure_Pa"], "fluids[].surface_pressure_Pa");
    }
    data.fluids.push_back(fluid);
  }

  for (const auto& node : require_node(root["rocks"], "rocks")) {
    lss::core::RockData rock;
    rock.id = require_as<std::string>(node["id"], "rocks[].id");
    rock.model = parse_rock_model(require_as<std::string>(node["model"], "rocks[].model"));
    rock.E_Pa = require_as<double>(node["E_Pa"], "rocks[].E_Pa");
    rock.nu = require_as<double>(node["nu"], "rocks[].nu");
    rock.density_kg_m3 = require_as<double>(node["density_kg_m3"], "rocks[].density_kg_m3");
    if (rock.model == lss::core::RockData::Model::DoubleMechanism) {
      rock.e0_per_h = require_as<double>(node["e0_per_h"], "rocks[].e0_per_h");
      rock.e0_per_min = rock.e0_per_h / 60.0;
      rock.sig0_Pa = require_as<double>(node["sig0_Pa"], "rocks[].sig0_Pa");
      rock.T0_degC = require_as<double>(node["T0_degC"], "rocks[].T0_degC");
      rock.T0_K = units::degC_to_K(rock.T0_degC);
      rock.n1 = require_as<double>(node["n1"], "rocks[].n1");
      rock.n2 = require_as<double>(node["n2"], "rocks[].n2");
    }
    data.rocks.push_back(rock);
  }

  for (const auto& node : require_node(root["layers"], "layers")) {
    lss::core::LayerData layer;
    layer.id = require_as<std::string>(node["id"], "layers[].id");
    layer.top_m = require_as<double>(node["top_m"], "layers[].top_m");
    layer.base_m = require_as<double>(node["base_m"], "layers[].base_m");
    layer.rock_id = require_as<std::string>(node["rock"], "layers[].rock");
    data.layers.push_back(layer);
  }

  for (const auto& node : require_node(root["annulars"], "annulars")) {
    lss::core::AnnularData annular;
    annular.id = require_as<std::string>(node["id"], "annulars[].id");
    annular.fluid_id = require_as<std::string>(node["fluid"], "annulars[].fluid");
    annular.top_m = require_as<double>(node["top_m"], "annulars[].top_m");
    annular.base_m = require_as<double>(node["base_m"], "annulars[].base_m");
    data.annulars.push_back(annular);
  }

  const YAML::Node lot = require_node(root["lot"], "lot");
  data.lot.enabled = require_as<bool>(lot["enabled"], "lot.enabled");
  data.lot.shoe_depth_m = require_as<double>(lot["shoe_depth_m"], "lot.shoe_depth_m");
  data.lot.model = optional_string(lot, "model");
  const YAML::Node fracture = require_node(lot["fracture"], "lot.fracture");
  data.lot.fracture_geometry =
      require_as<std::string>(fracture["geometry"], "lot.fracture.geometry");
  if (data.lot.model.empty()) {
    data.lot.model = data.lot.fracture_geometry;
  }
  if (fracture["fluid_viscosity_cP"]) {
    data.lot.fracture_fluid_viscosity_cP =
        require_as<double>(fracture["fluid_viscosity_cP"],
                           "lot.fracture.fluid_viscosity_cP");
    data.lot.fracture_fluid_viscosity_Pa_s =
        units::cP_to_Pa_s(data.lot.fracture_fluid_viscosity_cP);
  }
  if (fracture["height"]) {
    data.lot.fracture_height_m =
        parse_value_unit(fracture["height"], "lot.fracture.height", "length");
  }
  if (fracture["initial_width"]) {
    data.lot.fracture_initial_width_m = parse_value_unit(
        fracture["initial_width"], "lot.fracture.initial_width", "length");
  }
  if (fracture["breakdown"]) {
    const YAML::Node breakdown = fracture["breakdown"];
    data.lot.breakdown_method =
        require_as<std::string>(breakdown["method"], "lot.fracture.breakdown.method");
    data.lot.breakdown_pressure_Pa = parse_value_unit(
        breakdown["pressure"], "lot.fracture.breakdown.pressure", "pressure");
  }
  if (fracture["initiation"]) {
    const YAML::Node initiation = fracture["initiation"];
    data.lot.sigma_theta_fracture.type =
        require_as<std::string>(initiation["type"], "lot.fracture.initiation.type");
    if (data.lot.sigma_theta_fracture.type == "sigma_theta_static") {
      data.lot.sigma_theta_fracture.enabled = true;
      data.lot.sigma_theta_fracture.source =
          require_as<std::string>(initiation["source"],
                                  "lot.fracture.initiation.source");
      data.lot.sigma_theta_fracture.pressure_source =
          require_as<std::string>(initiation["pressure_source"],
                                  "lot.fracture.initiation.pressure_source");
      data.lot.sigma_theta_fracture.comparison =
          require_as<std::string>(initiation["comparison"],
                                  "lot.fracture.initiation.comparison");
      const YAML::Node sigma_theta =
          require_node(initiation["sigma_theta"],
                       "lot.fracture.initiation.sigma_theta");
      const YAML::Node compression_positive =
          require_node(sigma_theta["compression_positive"],
                       "lot.fracture.initiation.sigma_theta.compression_positive");
      data.lot.sigma_theta_fracture.sigma_theta_compression_positive_Pa =
          parse_value_unit(compression_positive,
                           "lot.fracture.initiation.sigma_theta.compression_positive",
                           "pressure");
      data.lot.sigma_theta_fracture.layer_id =
          require_as<std::string>(sigma_theta["layer_id"],
                                  "lot.fracture.initiation.sigma_theta.layer_id");
      data.lot.sigma_theta_fracture.influence_depth_m =
          parse_value_unit(sigma_theta["influence_depth"],
                           "lot.fracture.initiation.sigma_theta.influence_depth",
                           "length");
      data.lot.sigma_theta_fracture.mapping_status =
          require_as<std::string>(sigma_theta["mapping_status"],
                                  "lot.fracture.initiation.sigma_theta.mapping_status");
    } else if (data.lot.sigma_theta_fracture.type != "constant_pressure") {
      throw std::runtime_error(
          "lot.fracture.initiation.type invalido: " +
          data.lot.sigma_theta_fracture.type);
    }
  }
  if (lot["injection"]) {
    const YAML::Node injection = lot["injection"];
    data.lot.injection_rate_m3_s =
        parse_value_unit(injection["rate"], "lot.injection.rate", "rate");
    const YAML::Node schedule = require_node(injection["schedule"], "lot.injection.schedule");
    data.lot.injection_total_time_s =
        parse_value_unit(schedule["total_time"], "lot.injection.schedule.total_time", "time");
    data.lot.injection_dt_s =
        parse_value_unit(schedule["dt"], "lot.injection.schedule.dt", "time");
    data.lot.injection_accommodation_time_s = parse_value_unit(
        schedule["accommodation_time"], "lot.injection.schedule.accommodation_time", "time");
    if (schedule["phases"]) {
      for (std::size_t i = 0; i < schedule["phases"].size(); ++i) {
        const YAML::Node phase_node = schedule["phases"][i];
        lss::core::InjectionPhaseData phase;
        phase.name = optional_string(phase_node, "name", "injection");
        phase.duration_s = parse_value_unit(
            phase_node["duration"],
            "lot.injection.schedule.phases[].duration", "time");
        phase.rate_m3_s = parse_value_unit(
            phase_node["rate"],
            "lot.injection.schedule.phases[].rate", "rate");
        data.lot.injection_phases.push_back(phase);
      }
    }
  }
  if (lot["initial_pressure"]) {
    data.lot.initial_pressure_Pa =
        parse_value_unit(lot["initial_pressure"], "lot.initial_pressure", "pressure");
  }
  if (lot["leakoff"]) {
    const YAML::Node leakoff = lot["leakoff"];
    data.lot.leakoff_enabled = require_as<bool>(leakoff["enabled"], "lot.leakoff.enabled");
    data.lot.leakoff_model = optional_string(leakoff, "model", "none");
    if (leakoff["coefficient_m_sqrt_s"]) {
      data.lot.leakoff_coefficient_m_sqrt_s =
          require_as<double>(leakoff["coefficient_m_sqrt_s"],
                             "lot.leakoff.coefficient_m_sqrt_s");
    }
    if (leakoff["constant_rate_m3_s"]) {
      data.lot.leakoff_constant_rate_m3_s =
          require_as<double>(leakoff["constant_rate_m3_s"],
                             "lot.leakoff.constant_rate_m3_s");
    }
  }
  if (lot["detection"]) {
    data.lot.detection_method =
        require_as<std::string>(lot["detection"]["method"], "lot.detection.method");
  }
  if (lot["pressure_model"]) {
    data.lot.pressure_model =
        require_as<std::string>(lot["pressure_model"]["type"],
                                "lot.pressure_model.type");
  }
  if (lot["volumetric_balance"] &&
      lot["volumetric_balance"]["compliance"]) {
    const YAML::Node compliance = lot["volumetric_balance"]["compliance"];
    data.lot.volumetric_compliance.enabled =
        require_as<bool>(compliance["enabled"],
                         "lot.volumetric_balance.compliance.enabled");
    data.lot.volumetric_compliance.model =
        optional_string(compliance, "model", "none");
    data.lot.volumetric_compliance.source =
        optional_string(compliance, "source");
    data.lot.volumetric_compliance.caveat =
        optional_string(compliance, "caveat");
    if (compliance["geometric_compressibility"]) {
      data.lot.volumetric_compliance.geometric_compressibility_per_Pa =
          parse_value_unit(compliance["geometric_compressibility"],
                           "lot.volumetric_balance.compliance.geometric_compressibility",
                           "compressibility");
    }
    if (compliance["total_compressibility"]) {
      data.lot.volumetric_compliance.total_compressibility_per_Pa =
          parse_value_unit(compliance["total_compressibility"],
                           "lot.volumetric_balance.compliance.total_compressibility",
                           "compressibility");
    }
    if (compliance["inner_boundary"]) {
      const YAML::Node inner = compliance["inner_boundary"];
      data.lot.volumetric_compliance.inner_radius_m =
          parse_value_unit(inner["radius"],
                           "lot.volumetric_balance.compliance.inner_boundary.radius",
                           "length");
      data.lot.volumetric_compliance.inner_wall_thickness_m =
          parse_value_unit(inner["wall_thickness"],
                           "lot.volumetric_balance.compliance.inner_boundary.wall_thickness",
                           "length");
      data.lot.volumetric_compliance.inner_young_modulus_Pa =
          parse_value_unit(inner["young_modulus"],
                           "lot.volumetric_balance.compliance.inner_boundary.young_modulus",
                           "pressure");
      data.lot.volumetric_compliance.inner_poisson_ratio =
          require_as<double>(inner["poisson_ratio"],
                             "lot.volumetric_balance.compliance.inner_boundary.poisson_ratio");
    }
    if (compliance["formation"]) {
      const YAML::Node formation = compliance["formation"];
      data.lot.volumetric_compliance.outer_radius_m =
          parse_value_unit(formation["radius"],
                           "lot.volumetric_balance.compliance.formation.radius",
                           "length");
      data.lot.volumetric_compliance.formation_young_modulus_Pa =
          parse_value_unit(formation["young_modulus"],
                           "lot.volumetric_balance.compliance.formation.young_modulus",
                           "pressure");
      data.lot.volumetric_compliance.formation_poisson_ratio =
          require_as<double>(formation["poisson_ratio"],
                             "lot.volumetric_balance.compliance.formation.poisson_ratio");
    }
    data.lot.volumetric_compliance.mechanical_compliance_status =
        optional_string(compliance, "mechanical_compliance_status");
  }

  const YAML::Node apb = require_node(root["apb"], "apb");
  data.apb.enabled = require_as<bool>(apb["enabled"], "apb.enabled");
  data.apb.top_packer_m = require_as<double>(apb["top_packer_m"], "apb.top_packer_m");
  data.apb.leakage_enabled =
      require_as<bool>(apb["leakage_enabled"], "apb.leakage_enabled");
  data.apb.venting_enabled =
      require_as<bool>(apb["venting_enabled"], "apb.venting_enabled");

  const YAML::Node time = require_node(root["time"], "time");
  data.time.total_h = require_as<double>(time["total_h"], "time.total_h");
  data.time.dt_h = require_as<double>(time["dt_h"], "time.dt_h");
  data.time.scheme = parse_time_scheme(require_as<std::string>(time["scheme"], "time.scheme"));
  const YAML::Node solver = require_node(time["solver"], "time.solver");
  data.time.tol_pressure_bar =
      require_as<double>(solver["tol_pressure_bar"], "time.solver.tol_pressure_bar");
  data.time.tol_eq = require_as<double>(solver["tol_eq"], "time.solver.tol_eq");
  data.time.stabilization_h =
      require_as<double>(solver["stabilization_h"], "time.solver.stabilization_h");

  if (data.lot.shoe_depth_m <= 0.0) {
    throw std::runtime_error("Validacao falhou: lot.shoe_depth_m deve ser > 0");
  }
  if (data.time.dt_h <= 0.0) {
    throw std::runtime_error("Validacao falhou: time.dt_h deve ser > 0");
  }
  if (data.time.tol_eq <= 0.0) {
    throw std::runtime_error("Validacao falhou: time.solver.tol_eq deve ser > 0");
  }
  if (data.mode == "lot-pkn") {
    if (data.lot.model != "pkn" || data.lot.fracture_geometry != "pkn") {
      throw std::runtime_error("Validacao falhou: simulation.mode lot-pkn exige lot.model/fracture.geometry pkn");
    }
    if (data.lot.injection_dt_s <= 0.0 || data.lot.injection_total_time_s <= 0.0) {
      throw std::runtime_error("Validacao falhou: lot.injection.schedule exige tempos > 0");
    }
    if (!std::isfinite(data.lot.initial_pressure_Pa) ||
        data.lot.initial_pressure_Pa < 0.0) {
      throw std::runtime_error("Validacao falhou: lot.initial_pressure exige pressao >= 0");
    }
    double phase_total_s = 0.0;
    bool has_positive_phase_rate = false;
    for (const auto& phase : data.lot.injection_phases) {
      if (phase.duration_s <= 0.0) {
        throw std::runtime_error(
            "Validacao falhou: lot.injection.schedule.phases exige duracao > 0");
      }
      if (phase.rate_m3_s < 0.0) {
        throw std::runtime_error(
            "Validacao falhou: lot.injection.schedule.phases exige vazao >= 0");
      }
      phase_total_s += phase.duration_s;
      has_positive_phase_rate = has_positive_phase_rate || phase.rate_m3_s > 0.0;
    }
    if (!data.lot.injection_phases.empty() && !has_positive_phase_rate) {
      throw std::runtime_error(
          "Validacao falhou: LOT/PKN exige ao menos uma fase com vazao positiva");
    }
    if (!data.lot.injection_phases.empty()) {
      data.lot.injection_total_time_s =
          data.lot.injection_accommodation_time_s + phase_total_s;
    }
    if (data.lot.fracture_height_m <= 0.0) {
      throw std::runtime_error("Validacao falhou: LOT/PKN exige altura de fratura > 0");
    }
    if (!std::isfinite(data.lot.breakdown_pressure_Pa) ||
        data.lot.breakdown_pressure_Pa < 0.0) {
      throw std::runtime_error(
          "Validacao falhou: LOT/PKN exige pressao de breakdown >= 0 quando definida");
    }
    if (data.lot.sigma_theta_fracture.enabled) {
      const auto& criterion = data.lot.sigma_theta_fracture;
      if (criterion.pressure_source != "wellbore_pressure_Pa") {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_static exige pressure_source wellbore_pressure_Pa");
      }
      if (criterion.comparison != "legacy_algebra") {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_static exige comparison legacy_algebra");
      }
      if (criterion.layer_id.empty()) {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_static exige layer_id nao vazio");
      }
      if (!std::isfinite(criterion.influence_depth_m) ||
          criterion.influence_depth_m <= 0.0) {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_static exige influence_depth > 0");
      }
      if (!std::isfinite(criterion.sigma_theta_compression_positive_Pa) ||
          criterion.sigma_theta_compression_positive_Pa <= 0.0) {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_static exige sigma_theta > 0");
      }
    }
    if (data.lot.fracture_fluid_viscosity_Pa_s <= 0.0) {
      throw std::runtime_error("Validacao falhou: LOT/PKN exige viscosidade de fratura > 0");
    }
    if (data.lot.leakoff_coefficient_m_sqrt_s < 0.0) {
      throw std::runtime_error("Validacao falhou: LOT/PKN exige coeficiente de leakoff >= 0");
    }
    if (data.lot.leakoff_constant_rate_m3_s < 0.0) {
      throw std::runtime_error("Validacao falhou: LOT/PKN exige taxa constante de leakoff >= 0");
    }
    if (data.lot.pressure_model != "pkn_direct" &&
        data.lot.pressure_model != "volumetric_balance") {
      throw std::runtime_error(
          "Validacao falhou: LOT/PKN exige pressure_model.type pkn_direct ou volumetric_balance");
    }
    if (data.lot.volumetric_compliance.enabled) {
      const auto& compliance = data.lot.volumetric_compliance;
      if (data.lot.pressure_model != "volumetric_balance") {
        throw std::runtime_error(
            "Validacao falhou: compliance geometrica exige pressure_model volumetric_balance");
      }
      if (compliance.model != "constant_geometric" &&
          compliance.model != "elastic_annular_simple") {
        throw std::runtime_error(
            "Validacao falhou: compliance geometrica suporta constant_geometric ou elastic_annular_simple");
      }
      if (compliance.total_compressibility_per_Pa != 0.0) {
        throw std::runtime_error(
            "Validacao falhou: total_compressibility nao e suportado nesta fase");
      }
      if (compliance.model == "constant_geometric") {
        if (!std::isfinite(compliance.geometric_compressibility_per_Pa) ||
            compliance.geometric_compressibility_per_Pa < 0.0) {
          throw std::runtime_error(
              "Validacao falhou: geometric_compressibility deve ser >= 0");
        }
      } else {
        if (!std::isfinite(compliance.inner_radius_m) ||
            !std::isfinite(compliance.outer_radius_m) ||
            compliance.inner_radius_m <= 0.0 ||
            compliance.outer_radius_m <= compliance.inner_radius_m) {
          throw std::runtime_error(
              "Validacao falhou: elastic_annular_simple exige outer_radius > inner_radius > 0");
        }
        if (!std::isfinite(compliance.inner_wall_thickness_m) ||
            compliance.inner_wall_thickness_m <= 0.0) {
          throw std::runtime_error(
              "Validacao falhou: elastic_annular_simple exige inner wall_thickness > 0");
        }
        if (!std::isfinite(compliance.inner_young_modulus_Pa) ||
            !std::isfinite(compliance.formation_young_modulus_Pa) ||
            compliance.inner_young_modulus_Pa <= 0.0 ||
            compliance.formation_young_modulus_Pa <= 0.0) {
          throw std::runtime_error(
              "Validacao falhou: elastic_annular_simple exige Young modulus > 0");
        }
        if (!std::isfinite(compliance.inner_poisson_ratio) ||
            !std::isfinite(compliance.formation_poisson_ratio) ||
            compliance.inner_poisson_ratio < 0.0 ||
            compliance.formation_poisson_ratio < 0.0 ||
            compliance.inner_poisson_ratio >= 0.5 ||
            compliance.formation_poisson_ratio >= 0.5) {
          throw std::runtime_error(
              "Validacao falhou: elastic_annular_simple exige Poisson em [0, 0.5)");
        }
      }
      if (compliance.source.empty()) {
        throw std::runtime_error(
            "Validacao falhou: compliance geometrica exige source");
      }
    }
  }
  validate_nonempty(!data.casings.empty(), "casings");
  validate_nonempty(!data.fluids.empty(), "fluids");
  validate_nonempty(!data.rocks.empty(), "rocks");
  validate_nonempty(!data.layers.empty(), "layers");
  validate_references(data);

  return data;
}

}  // namespace lss::io
