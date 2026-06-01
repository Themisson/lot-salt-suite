#include "io/CaseParser.hpp"

#include <stdexcept>
#include <string>

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
  const YAML::Node fracture = require_node(lot["fracture"], "lot.fracture");
  data.lot.fracture_geometry =
      require_as<std::string>(fracture["geometry"], "lot.fracture.geometry");
  data.lot.fracture_fluid_viscosity_cP =
      require_as<double>(fracture["fluid_viscosity_cP"],
                         "lot.fracture.fluid_viscosity_cP");

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

  return data;
}

}  // namespace lss::io
