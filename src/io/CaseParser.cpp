#include "io/CaseParser.hpp"

#include <cmath>
#include <stdexcept>
#include <string>
#include <unordered_set>

#include <yaml-cpp/yaml.h>

#include "lot/FractureModelSelector.hpp"
#include "lot/LeakoffCouplingMode.hpp"
#include "lot/SaltDisplacementMode.hpp"
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

bool optional_bool(const YAML::Node& node, const std::string& path,
                   const bool fallback = false) {
  const YAML::Node value = node[path];
  return value ? value.as<bool>() : fallback;
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

std::string fracture_model_source_text(
    lss::lot::FractureModelSelectionSource source) {
  switch (source) {
    case lss::lot::FractureModelSelectionSource::Defaulted:
      return "DEFAULTED";
    case lss::lot::FractureModelSelectionSource::Explicit:
      return "EXPLICIT";
  }
  throw std::runtime_error("FractureModelSelector: fonte de selecao invalida");
}

void apply_fracture_model_selection(
    const lss::lot::FractureModelSelectionResult& selection,
    lss::core::LotConfig& lot) {
  lot.fracture_model = selection.canonical_name;
  lot.fracture_model_selection_source =
      fracture_model_source_text(selection.source);
  lot.fracture_model_route = selection.route;
  lot.fracture_model_diagnostic_only = selection.diagnostic_only;
  lot.fracture_model_physically_validated = selection.physically_validated;
  lot.fracture_model_legacy_equivalent = selection.legacy_equivalent;
  lot.fracture_model_runtime_supported_now = selection.runtime_supported_now;
  lot.fracture_model_requires_fracture_initiation_gate =
      selection.requires_fracture_initiation_gate;
  lot.fracture_model_runtime_dispatch_enabled = false;
  lot.fracture_model_sigma_theta_initial_state_audit_required = true;
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

void parse_apb_lot_modern_modes(const YAML::Node& root,
                                lss::core::CaseData& data) {
  const YAML::Node apb_lot = root["apb_lot"];
  if (!apb_lot) {
    return;
  }

  data.apb_lot.output_format =
      optional_string(apb_lot, "output_format", "json");
  data.apb_lot.legacy_dat_output_enabled =
      optional_bool(apb_lot, "legacy_dat_output_enabled", true);
  data.apb_lot.leakoff_coupling_mode =
      optional_string(apb_lot, "leakoff_coupling_mode", "volume_balance");
  data.apb_lot.salt_displacement_mode =
      optional_string(apb_lot, "salt_displacement_mode", "pre_iterative");

  if (data.apb_lot.output_format != "json" &&
      data.apb_lot.output_format != "legacy_dat") {
    throw std::runtime_error(
        "Validacao falhou: apb_lot.output_format exige json ou legacy_dat");
  }
  (void)lss::lot::parse_leakoff_coupling_mode(
      data.apb_lot.leakoff_coupling_mode);
  (void)lss::lot::parse_salt_displacement_mode(
      data.apb_lot.salt_displacement_mode);
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

void parse_sigma_theta_runtime_geometry(
    const YAML::Node& initiation,
    lss::core::SigmaThetaFractureCriterionData& criterion) {
  const YAML::Node geometry = initiation["sigma_theta_runtime_geometry"];
  if (!geometry) {
    return;
  }

  auto& runtime = criterion.runtime_geometry;
  runtime.enabled = true;
  runtime.mode =
      require_as<std::string>(geometry["mode"],
                              "lot.fracture.initiation.sigma_theta_runtime_geometry.mode");
  runtime.outer_radius_m = parse_value_unit(
      geometry["outer_radius"],
      "lot.fracture.initiation.sigma_theta_runtime_geometry.outer_radius",
      "length");
  runtime.radial_elements =
      require_as<int>(geometry["radial_elements"],
                      "lot.fracture.initiation.sigma_theta_runtime_geometry.radial_elements");
  runtime.ratio =
      require_as<double>(geometry["ratio"],
                         "lot.fracture.initiation.sigma_theta_runtime_geometry.ratio");
  runtime.integration_order =
      require_as<int>(geometry["integration_order"],
                      "lot.fracture.initiation.sigma_theta_runtime_geometry.integration_order");

  const YAML::Node sampling =
      require_node(geometry["sampling"],
                   "lot.fracture.initiation.sigma_theta_runtime_geometry.sampling");
  runtime.sampling_mode =
      require_as<std::string>(
          sampling["mode"],
          "lot.fracture.initiation.sigma_theta_runtime_geometry.sampling.mode");
  runtime.sampling_source = optional_string(sampling, "source");
  runtime.consumption_status =
      optional_string(geometry, "consumption_status",
                      "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED");
}

void parse_fracture_gate_diagnostics(const YAML::Node& fracture,
                                     lss::core::LotConfig& lot) {
  const YAML::Node diagnostics = fracture["fracture_gate_diagnostics"];
  if (!diagnostics) {
    return;
  }

  auto& config = lot.fracture_gate_diagnostics;
  config.enabled = require_as<bool>(
      diagnostics["enabled"],
      "lot.fracture.fracture_gate_diagnostics.enabled");
  config.mode = optional_string(diagnostics, "mode", "pre_runner");
  config.dispatch_runtime_enabled =
      optional_bool(diagnostics, "dispatch_runtime_enabled", false);

  if (!config.enabled) {
    return;
  }

  if (config.mode != "pre_runner" && config.mode != "diagnostic_only" &&
      config.mode != "limited_gate") {
    throw std::runtime_error(
        "Validacao falhou: fracture_gate_diagnostics.mode exige pre_runner "
        "diagnostic_only ou limited_gate");
  }
  if (config.dispatch_runtime_enabled) {
    throw std::runtime_error(
        "Validacao falhou: fracture_gate_diagnostics.dispatch_runtime_enabled "
        "deve ser false nesta fase");
  }
}

void parse_sigma_theta_diagnostic_input(const YAML::Node& fracture,
                                          lss::core::LotConfig& lot) {
  const YAML::Node node = fracture["sigma_theta_diagnostic_input"];
  if (!node) {
    return;
  }

  auto& input = lot.sigma_theta_diagnostic_input;
  input.enabled = require_as<bool>(
      node["enabled"],
      "lot.fracture.sigma_theta_diagnostic_input.enabled");
  if (!input.enabled) {
    return;
  }

  input.source = require_as<std::string>(
      node["source"],
      "lot.fracture.sigma_theta_diagnostic_input.source");
  input.sigma_theta_initial_compression_positive_Pa = require_as<double>(
      node["sigma_theta_initial_compression_positive_Pa"],
      "lot.fracture.sigma_theta_diagnostic_input.sigma_theta_initial_compression_positive_Pa");
  input.sigma_theta_current_compression_positive_Pa = require_as<double>(
      node["sigma_theta_current_compression_positive_Pa"],
      "lot.fracture.sigma_theta_diagnostic_input.sigma_theta_current_compression_positive_Pa");
  input.sign_convention = require_as<std::string>(
      node["sign_convention"],
      "lot.fracture.sigma_theta_diagnostic_input.sign_convention");
  input.reference_frame = require_as<std::string>(
      node["reference_frame"],
      "lot.fracture.sigma_theta_diagnostic_input.reference_frame");
  input.state_time = require_as<std::string>(
      node["state_time"],
      "lot.fracture.sigma_theta_diagnostic_input.state_time");
  input.physically_validated = require_as<bool>(
      node["physically_validated"],
      "lot.fracture.sigma_theta_diagnostic_input.physically_validated");
  input.legacy_equivalent = require_as<bool>(
      node["legacy_equivalent"],
      "lot.fracture.sigma_theta_diagnostic_input.legacy_equivalent");

  if (input.source != "EXPLICIT_DIAGNOSTIC_INPUT" &&
      input.source != "SYNTHETIC_FIXTURE") {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input.source exige "
        "EXPLICIT_DIAGNOSTIC_INPUT ou SYNTHETIC_FIXTURE");
  }
  if (!std::isfinite(input.sigma_theta_initial_compression_positive_Pa) ||
      input.sigma_theta_initial_compression_positive_Pa <= 0.0) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input exige "
        "sigma_theta_initial_compression_positive_Pa finito e > 0");
  }
  if (!std::isfinite(input.sigma_theta_current_compression_positive_Pa)) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input exige "
        "sigma_theta_current_compression_positive_Pa finito");
  }
  if (input.sign_convention != "COMPRESSION_POSITIVE") {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input.sign_convention exige "
        "COMPRESSION_POSITIVE");
  }
  if (input.reference_frame != "WELLBORE_WALL_TOTAL_STRESS") {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input.reference_frame exige "
        "WELLBORE_WALL_TOTAL_STRESS");
  }
  if (input.state_time != "POST_DRILLING_BEFORE_LOT") {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input.state_time exige "
        "POST_DRILLING_BEFORE_LOT");
  }
  if (input.physically_validated) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input.physically_validated "
        "deve ser false");
  }
  if (input.legacy_equivalent) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_diagnostic_input.legacy_equivalent "
        "deve ser false");
  }
}

void parse_sigma_theta_provider(const YAML::Node& fracture,
                                lss::core::LotConfig& lot) {
  const YAML::Node node = fracture["sigma_theta_provider"];
  if (!node) {
    return;
  }

  auto& provider = lot.sigma_theta_provider;
  provider.enabled = require_as<bool>(
      node["enabled"], "lot.fracture.sigma_theta_provider.enabled");
  if (!provider.enabled) {
    return;
  }

  provider.source = require_as<std::string>(
      node["source"], "lot.fracture.sigma_theta_provider.source");
  provider.far_field_stress_compression_positive_Pa = require_as<double>(
      node["far_field_stress_compression_positive_Pa"],
      "lot.fracture.sigma_theta_provider.far_field_stress_compression_positive_Pa");
  provider.wellbore_pressure_Pa = require_as<double>(
      node["wellbore_pressure_Pa"],
      "lot.fracture.sigma_theta_provider.wellbore_pressure_Pa");
  provider.tensile_strength_Pa =
      node["tensile_strength_Pa"] ? node["tensile_strength_Pa"].as<double>()
                                  : 0.0;
  provider.physically_validated = require_as<bool>(
      node["physically_validated"],
      "lot.fracture.sigma_theta_provider.physically_validated");
  provider.legacy_equivalent = require_as<bool>(
      node["legacy_equivalent"],
      "lot.fracture.sigma_theta_provider.legacy_equivalent");

  if (provider.source != "ELASTIC_INITIAL_WELLBORE_STATE" &&
      provider.source != "AXISYMMETRIC_ELASTIC_WELLBORE_STATE") {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider.source exige "
        "ELASTIC_INITIAL_WELLBORE_STATE ou "
        "AXISYMMETRIC_ELASTIC_WELLBORE_STATE");
  }
  if (!std::isfinite(provider.far_field_stress_compression_positive_Pa) ||
      provider.far_field_stress_compression_positive_Pa <= 0.0) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider exige "
        "far_field_stress_compression_positive_Pa finito e > 0");
  }
  if (!std::isfinite(provider.wellbore_pressure_Pa) ||
      provider.wellbore_pressure_Pa < 0.0) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider exige "
        "wellbore_pressure_Pa finito e >= 0");
  }
  if (!std::isfinite(provider.tensile_strength_Pa) ||
      provider.tensile_strength_Pa < 0.0) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider exige "
        "tensile_strength_Pa finito e >= 0");
  }
  if (provider.physically_validated) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider.physically_validated "
        "deve ser false");
  }
  if (provider.legacy_equivalent) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider.legacy_equivalent "
        "deve ser false");
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

  parse_apb_lot_modern_modes(root, data);

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
  lss::lot::FractureModelSelectionInput fracture_model_input;
  fracture_model_input.has_fracture_model_field =
      static_cast<bool>(fracture["fracture_model"]);
  if (fracture_model_input.has_fracture_model_field) {
    fracture_model_input.fracture_model_value =
        require_as<std::string>(fracture["fracture_model"],
                                "lot.fracture.fracture_model");
  }
  apply_fracture_model_selection(
      lss::lot::select_fracture_model(fracture_model_input), data.lot);
  parse_fracture_gate_diagnostics(fracture, data.lot);
  parse_sigma_theta_provider(fracture, data.lot);
  parse_sigma_theta_diagnostic_input(fracture, data.lot);
  if (data.lot.sigma_theta_provider.enabled &&
      data.lot.sigma_theta_diagnostic_input.enabled) {
    throw std::runtime_error(
        "Validacao falhou: sigma_theta_provider e "
        "sigma_theta_diagnostic_input nao podem estar enabled simultaneamente");
  }
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
    } else if (data.lot.sigma_theta_fracture.type == "sigma_theta_time_series") {
      data.lot.sigma_theta_fracture.enabled = true;
      data.lot.sigma_theta_fracture.pressure_source =
          require_as<std::string>(initiation["pressure_source"],
                                  "lot.fracture.initiation.pressure_source");
      data.lot.sigma_theta_fracture.comparison =
          require_as<std::string>(initiation["comparison"],
                                  "lot.fracture.initiation.comparison");
      const YAML::Node series =
          require_node(initiation["sigma_theta_series"],
                       "lot.fracture.initiation.sigma_theta_series");
      data.lot.sigma_theta_fracture.source =
          require_as<std::string>(series["source"],
                                  "lot.fracture.initiation.sigma_theta_series.source");
      data.lot.sigma_theta_fracture.interpolation =
          require_as<std::string>(
              series["interpolation"],
              "lot.fracture.initiation.sigma_theta_series.interpolation");
      data.lot.sigma_theta_fracture.out_of_range =
          require_as<std::string>(
              series["out_of_range"],
              "lot.fracture.initiation.sigma_theta_series.out_of_range");
      data.lot.sigma_theta_fracture.mapping_status =
          optional_string(series, "mapping_status",
                          "TIME_SERIES_FROM_LEGACY_TRACE");
      const YAML::Node values =
          require_node(series["values"],
                       "lot.fracture.initiation.sigma_theta_series.values");
      for (std::size_t i = 0; i < values.size(); ++i) {
        const YAML::Node value = values[i];
        lss::core::SigmaThetaFractureCriterionData::TimeSeriesPoint point;
        point.time_s =
            parse_value_unit(value["time"],
                             "lot.fracture.initiation.sigma_theta_series.values[].time",
                             "time");
        point.sigma_theta_compression_positive_Pa = parse_value_unit(
            value["sigma_theta_compression_positive"],
            "lot.fracture.initiation.sigma_theta_series.values[].sigma_theta_compression_positive",
            "pressure");
        point.layer_id = optional_string(value, "layer_id");
        if (value["influence_depth"]) {
          point.influence_depth_m = parse_value_unit(
              value["influence_depth"],
              "lot.fracture.initiation.sigma_theta_series.values[].influence_depth",
              "length");
        }
        data.lot.sigma_theta_fracture.time_series.push_back(point);
      }
    } else if (data.lot.sigma_theta_fracture.type != "constant_pressure") {
      throw std::runtime_error(
          "lot.fracture.initiation.type invalido: " +
          data.lot.sigma_theta_fracture.type);
    }
    parse_sigma_theta_runtime_geometry(initiation, data.lot.sigma_theta_fracture);
  }
  if (fracture["balance"] && fracture["balance"]["sink_timing"]) {
    data.lot.fracture_sink_timing =
        require_as<std::string>(fracture["balance"]["sink_timing"],
                                "lot.fracture.balance.sink_timing");
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
      if (criterion.type == "sigma_theta_static" &&
          criterion.pressure_source != "wellbore_pressure_Pa") {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_static exige pressure_source wellbore_pressure_Pa");
      }
      if (criterion.type == "sigma_theta_time_series" &&
          criterion.pressure_source != "wellbore_pressure_trial_Pa") {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta_time_series exige pressure_source wellbore_pressure_trial_Pa");
      }
      if (criterion.comparison != "legacy_algebra") {
        throw std::runtime_error(
            "Validacao falhou: sigma_theta exige comparison legacy_algebra");
      }
      if (criterion.runtime_geometry.enabled) {
        const auto& geometry = criterion.runtime_geometry;
        if (geometry.mode != "apbsalt1d_legacy_equivalent") {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry exige mode "
              "apbsalt1d_legacy_equivalent");
        }
        if (!std::isfinite(geometry.outer_radius_m) ||
            geometry.outer_radius_m <= 0.0) {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry exige outer_radius > 0");
        }
        if (geometry.radial_elements <= 0) {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry exige radial_elements > 0");
        }
        if (!std::isfinite(geometry.ratio) || geometry.ratio <= 0.0) {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry exige ratio > 0");
        }
        if (geometry.integration_order != 3) {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry legado exige integration_order 3");
        }
        if (geometry.sampling_mode != "legacy_elem0_sig_2_0") {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry exige sampling mode "
              "legacy_elem0_sig_2_0");
        }
        if (geometry.consumption_status !=
            "APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED") {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_runtime_geometry consumption_status "
              "suportado e APBSALT1D_CONFIG_DECLARED_NOT_CONSUMED");
        }
      }
      if (criterion.type == "sigma_theta_static") {
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
      if (criterion.type == "sigma_theta_time_series") {
        if (criterion.interpolation != "linear") {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_time_series exige interpolation linear");
        }
        if (criterion.out_of_range != "clamp") {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_time_series exige out_of_range clamp");
        }
        if (criterion.time_series.size() < 2) {
          throw std::runtime_error(
              "Validacao falhou: sigma_theta_time_series exige ao menos 2 pontos");
        }
        for (std::size_t i = 0; i < criterion.time_series.size(); ++i) {
          const auto& point = criterion.time_series[i];
          if (!std::isfinite(point.time_s) || point.time_s < 0.0) {
            throw std::runtime_error(
                "Validacao falhou: sigma_theta_time_series exige time >= 0");
          }
          if (i > 0 && point.time_s <= criterion.time_series[i - 1].time_s) {
            throw std::runtime_error(
                "Validacao falhou: sigma_theta_time_series exige tempos crescentes");
          }
          if (!std::isfinite(point.sigma_theta_compression_positive_Pa) ||
              point.sigma_theta_compression_positive_Pa <= 0.0) {
            throw std::runtime_error(
                "Validacao falhou: sigma_theta_time_series exige sigma_theta > 0");
          }
        }
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
    if (data.lot.fracture_sink_timing != "same_step" &&
        data.lot.fracture_sink_timing != "next_step") {
      throw std::runtime_error(
          "Validacao falhou: lot.fracture.balance.sink_timing exige same_step ou next_step");
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
