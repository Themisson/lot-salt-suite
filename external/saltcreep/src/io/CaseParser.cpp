#include "io/CaseParser.hpp"
#include <yaml-cpp/yaml.h>
#include <stdexcept>
#include <iostream>
#include <filesystem>
#include <algorithm>

namespace fs = std::filesystem;

namespace {

double req_double(const YAML::Node& n, const std::string& key,
                  const std::string& ctx = "") {
    if (!n[key])
        throw std::runtime_error("Missing field: " +
                                 (ctx.empty() ? key : ctx + "." + key));
    return n[key].as<double>();
}

int req_int(const YAML::Node& n, const std::string& key,
            const std::string& ctx = "") {
    if (!n[key])
        throw std::runtime_error("Missing field: " +
                                 (ctx.empty() ? key : ctx + "." + key));
    return n[key].as<int>();
}

struct LitologiaData { DMParams dm; EdmtParams edmt; };

LithologyLayer make_lithology_layer(double z_top_m,
                                    double z_bottom_m,
                                    const std::string& material,
                                    const std::string& label = "") {
    if (z_bottom_m <= z_top_m)
        throw std::runtime_error("lithology.layers z_bottom_m must exceed z_top_m");
    LithologyLayer layer;
    layer.z_top_m = z_top_m;
    layer.z_bottom_m = z_bottom_m;
    layer.material = material;
    layer.label = label.empty() ? material : label;
    return layer;
}

void append_primary_gap(std::vector<LithologyLayer>& layers,
                        double z_top_m,
                        double z_bottom_m,
                        const std::string& primary) {
    constexpr double eps = 1.0e-12;
    if (z_bottom_m > z_top_m + eps)
        layers.push_back(make_lithology_layer(z_top_m, z_bottom_m, primary, primary));
}

std::vector<LithologyLayer> parse_lithology_layers(const YAML::Node& litho,
                                                   const std::string& primary,
                                                   double layer_thickness_m) {
    std::vector<LithologyLayer> layers;
    if (!litho)
        return layers;

    if (litho["layers"]) {
        for (const auto& node : litho["layers"]) {
            const std::string material = node["material"]
                ? node["material"].as<std::string>()
                : primary;
            const std::string label = node["label"]
                ? node["label"].as<std::string>()
                : material;
            layers.push_back(make_lithology_layer(
                req_double(node, "z_top_m", "lithology.layers"),
                req_double(node, "z_bottom_m", "lithology.layers"),
                material,
                label));
        }
        std::sort(layers.begin(), layers.end(), [](const auto& a, const auto& b) {
            return a.z_top_m < b.z_top_m;
        });
        return layers;
    }

    if (!litho["intercalations"])
        return layers;

    std::vector<LithologyLayer> inclusions;
    for (const auto& node : litho["intercalations"]) {
        const std::string material = node["material"]
            ? node["material"].as<std::string>()
            : primary;
        const double thickness = req_double(node, "thickness_m", "lithology.intercalations");
        double z_top = 0.0;
        if (node["z_top_m"]) {
            z_top = node["z_top_m"].as<double>();
        } else {
            const std::string position = node["position"]
                ? node["position"].as<std::string>()
                : "center";
            if (position == "top") {
                z_top = 0.0;
            } else if (position == "bottom") {
                z_top = layer_thickness_m - thickness;
            } else {
                z_top = 0.5 * (layer_thickness_m - thickness);
            }
        }
        inclusions.push_back(make_lithology_layer(
            z_top,
            z_top + thickness,
            material,
            node["label"] ? node["label"].as<std::string>() : material));
    }
    std::sort(inclusions.begin(), inclusions.end(), [](const auto& a, const auto& b) {
        return a.z_top_m < b.z_top_m;
    });

    double cursor = 0.0;
    for (const auto& layer : inclusions) {
        append_primary_gap(layers, cursor, layer.z_top_m, primary);
        layers.push_back(layer);
        cursor = std::max(cursor, layer.z_bottom_m);
    }
    append_primary_gap(layers, cursor, layer_thickness_m, primary);
    return layers;
}

Wang2004Params default_wang_params_for_lithology(const std::string& lithology) {
    Wang2004Params params;
    if (lithology == "taquidrita") {
        params.A_d = 3.5e-8;
        params.m_d = 2.8;
        params.p_d = 1.2;
        params.n_d = 2.0;
        params.D_max = 0.99;
    }
    return params;
}

LitologiaData load_litologia(const fs::path& litologia_yaml) {
    YAML::Node root;
    try {
        root = YAML::LoadFile(litologia_yaml.string());
    } catch (const YAML::Exception& e) {
        throw std::runtime_error("Cannot load litologia " +
                                 litologia_yaml.string() + ": " + e.what());
    }
    auto dm_node = root["dm"];
    if (!dm_node)
        throw std::runtime_error("No 'dm' section in " + litologia_yaml.string());

    const double R_SI = 8.314;
    double Q_J_mol = req_double(dm_node, "Q_J_mol");

    DMParams dm;
    dm.e0_s     = req_double(dm_node, "e0_1_s");
    dm.sig0     = req_double(dm_node, "sig0_Pa");
    dm.T0       = req_double(dm_node, "T0_K");
    dm.n1       = req_double(dm_node, "n1");
    dm.n2       = req_double(dm_node, "n2");
    dm.Q_over_R = Q_J_mol / R_SI;

    EdmtParams edmt;
    auto edmt_node = root["edmt"];
    if (edmt_node) {
        edmt.K1 = edmt_node["K1"] ? edmt_node["K1"].as<double>() : 0.0;
        edmt.K2 = edmt_node["K2"] ? edmt_node["K2"].as<double>() : 0.0;
    }
    return {dm, edmt};
}

} // namespace

CaseData parse_case(const fs::path& yaml_path, const fs::path& data_dir_hint) {
    YAML::Node root;
    try {
        root = YAML::LoadFile(yaml_path.string());
    } catch (const YAML::Exception& e) {
        throw std::runtime_error("YAML parse error in " + yaml_path.string() +
                                 ": " + e.what());
    }

    CaseData cd;
    cd.name = root["name"] ? root["name"].as<std::string>()
                           : yaml_path.stem().string();

    // geometry
    auto geom = root["geometry"];
    if (!geom) throw std::runtime_error("Missing section: geometry");
    cd.geom.Ri           = req_double(geom, "well_radius_m",      "geometry");
    cd.geom.outer_factor = req_double(geom, "outer_radius_factor", "geometry");
    cd.geom.layer_thickness_m =
        geom["layer_thickness_m"] ? geom["layer_thickness_m"].as<double>() : 1.0;
    if (cd.geom.layer_thickness_m <= 0.0)
        throw std::runtime_error("geometry.layer_thickness_m must be positive");

    // mesh
    auto mesh = root["mesh"];
    if (!mesh) throw std::runtime_error("Missing section: mesh");
    cd.mesh.n_radial = req_int   (mesh, "n_elements_radial", "mesh");
    cd.mesh.ratio    = req_double(mesh, "ratio",              "mesh");

    cd.mesh.n_axial = mesh["n_elements_axial"] ? mesh["n_elements_axial"].as<int>() : 1;
    cd.mesh.adaptive = mesh["adaptive"] && mesh["adaptive"].as<bool>();
    cd.mesh.error_threshold =
        mesh["error_threshold"] ? mesh["error_threshold"].as<double>() : 0.10;
    cd.mesh.max_refinement_levels =
        mesh["max_refinement_levels"] ? mesh["max_refinement_levels"].as<int>() : 3;
    cd.mesh.damage_refinement_threshold =
        mesh["damage_refinement_threshold"] ? mesh["damage_refinement_threshold"].as<double>() : -1.0;
    if (cd.mesh.error_threshold < 0.0)
        throw std::runtime_error("mesh.error_threshold must be non-negative");
    if (cd.mesh.max_refinement_levels < 0)
        throw std::runtime_error("mesh.max_refinement_levels must be >= 0");
    if (cd.mesh.damage_refinement_threshold > 0.99)
        throw std::runtime_error("mesh.damage_refinement_threshold must be <= 0.99");

    // element
    auto elem = root["element"];
    cd.element_type = (elem && elem["type"])
                      ? elem["type"].as<std::string>()
                      : "axisym_1d_L3";

    if (cd.mesh.n_axial > 1 && cd.element_type == "axisym_1d_L3")
        throw std::runtime_error("axisym_1d_L3 requires n_elements_axial == 1");

    // depths
    auto deps = root["depths"];
    cd.depths.burial_m      = (deps && deps["burial_m"])      ? deps["burial_m"].as<double>()      : 0.0;
    cd.depths.water_depth_m = (deps && deps["water_depth_m"]) ? deps["water_depth_m"].as<double>() : 0.0;
    cd.depths.salt_above_m  = (deps && deps["salt_above_m"])  ? deps["salt_above_m"].as<double>()  : 0.0;

    // fluid pressure
    auto fluid = root["fluid"];
    if (!fluid) throw std::runtime_error("Missing section: fluid");
    cd.fluid.mode = fluid["mode"] ? fluid["mode"].as<std::string>() : "constant";
    cd.fluid.surface_pressure_Pa =
        fluid["surface_pressure_Pa"] ? fluid["surface_pressure_Pa"].as<double>() : 0.0;
    const double depth_origin =
        cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    if (fluid["pressure_Pa"]) {
        cd.fluid_Pa = fluid["pressure_Pa"].as<double>();
        cd.fluid.pressure_Pa = cd.fluid_Pa;
    } else {
        double ppg = req_double(fluid, "weight_lb_per_gal", "fluid");
        cd.fluid.weight_lb_per_gal = ppg;
        cd.fluid_Pa = cd.fluid.surface_pressure_Pa + ppg * 119.826 * 9.80665 * depth_origin;
        cd.fluid.pressure_Pa = cd.fluid_Pa;
    }
    if (cd.fluid.mode != "constant" && cd.fluid.mode != "hydrostatic_depth_profile")
        throw std::runtime_error("fluid.mode must be constant or hydrostatic_depth_profile");
    if (cd.fluid.mode == "hydrostatic_depth_profile" && cd.fluid.weight_lb_per_gal <= 0.0)
        throw std::runtime_error("fluid.mode hydrostatic_depth_profile requires fluid.weight_lb_per_gal");

    // stress
    auto stress = root["stress"];
    cd.k0 = (stress && stress["k0"]) ? stress["k0"].as<double>() : 1.0;
    cd.geostatic_mode =
        (stress && stress["geostatic_mode"]) ? stress["geostatic_mode"].as<std::string>() : "constant";
    if (cd.geostatic_mode != "constant" && cd.geostatic_mode != "depth_profile")
        throw std::runtime_error("stress.geostatic_mode must be constant or depth_profile");

    // overburden gradient — Pa/m; default typical offshore Brazil ~21 kPa/m
    cd.overburden_grad_Pa_per_m =
        (stress && stress["overburden_grad_Pa_per_m"])
        ? stress["overburden_grad_Pa_per_m"].as<double>()
        : 21000.0;

    // lithology + litologia file
    auto litho = root["lithology"];
    cd.lithology = litho ? (litho["primary"] ? litho["primary"].as<std::string>() : "halita")
                         : "halita";
    cd.lithology_layers = parse_lithology_layers(
        litho, cd.lithology, cd.geom.layer_thickness_m);
    if (!cd.lithology_layers.empty()) {
        const double z_bottom = cd.lithology_layers.back().z_bottom_m;
        if (z_bottom > cd.geom.layer_thickness_m)
            cd.geom.layer_thickness_m = z_bottom;
    }

    // Locate data/litologias/ directory
    fs::path data_dir = data_dir_hint;
    if (data_dir.empty()) {
        // Walk up from the absolute path of the YAML file, looking for data/litologias/
        // Using absolute() ensures the walk-up terminates at the filesystem root.
        fs::path p = fs::absolute(yaml_path).parent_path();
        for (int tries = 0; tries < 10; ++tries) {
            if (fs::exists(p / "data" / "litologias")) {
                data_dir = p / "data";
                break;
            }
            fs::path parent = p.parent_path();
            if (parent == p) break;  // reached filesystem root
            p = parent;
        }
    }
    if (data_dir.empty())
        throw std::runtime_error("Cannot find data/litologias/ relative to " +
                                 yaml_path.string());

    fs::path litologia_yaml = data_dir / "litologias" / (cd.lithology + ".yaml");
    auto lit = load_litologia(litologia_yaml);
    cd.dm   = lit.dm;
    cd.edmt = lit.edmt;  // K1=0, K2=0 if no 'edmt' section in litologia file
    cd.wang_2004 = default_wang_params_for_lithology(cd.lithology);

    // Always load elastic constants from litologia file, then override if case YAML has them
    {
        YAML::Node lr = YAML::LoadFile(litologia_yaml.string());
        cd.E_Pa = lr["elastic"]["E_Pa"].as<double>();
        cd.nu   = lr["elastic"]["nu"].as<double>();
    }
    auto mat = root["material"];
    if (mat) {
        if (mat["E_Pa"]) cd.E_Pa = mat["E_Pa"].as<double>();
        if (mat["nu"])   cd.nu   = mat["nu"].as<double>();
    }

    // thermal
    auto therm = root["thermal"];
    cd.thermal.enabled = therm && therm["enabled"] && therm["enabled"].as<bool>();
    if (therm && therm["mode"]) {
        cd.thermal.mode = therm["mode"].as<std::string>();
    } else {
        cd.thermal.mode = "constant";
    }
    if (cd.thermal.mode == "constant") {
        cd.thermal.T_K = (therm && therm["T_K"]) ? therm["T_K"].as<double>() : 370.88;
    } else if (cd.thermal.mode == "profile") {
        // profile mode
        cd.thermal.seabed_temp_C = (therm && therm["seabed_temp_C"])
                                   ? therm["seabed_temp_C"].as<double>() : 4.0;
        if (therm && therm["geothermal_gradient_C_per_m"])
            cd.thermal.grad_C_per_m = therm["geothermal_gradient_C_per_m"].as<double>();
        else
            cd.thermal.grad_C_per_m = (therm && therm["grad_C_per_m"])
                                      ? therm["grad_C_per_m"].as<double>() : 0.01442;
        // Compute T_K for this depth (used internally; 1D axisym gives uniform T per layer)
        double depth_total = cd.depths.burial_m + cd.depths.water_depth_m;
        cd.thermal.T_K = (cd.thermal.seabed_temp_C +
                          cd.thermal.grad_C_per_m * depth_total) + 273.15;
    } else if (cd.thermal.mode == "conduction_1d" || cd.thermal.mode == "conduction_2d") {
        cd.thermal.T_K = (therm && therm["T_K"]) ? therm["T_K"].as<double>() : 370.88;
    } else {
        throw std::runtime_error("thermal.mode must be constant, profile, conduction_1d, or conduction_2d");
    }
    cd.thermal.alpha_thermal =
        (therm && therm["alpha_thermal"]) ? therm["alpha_thermal"].as<double>() : 0.0;
    cd.thermal.T_reference_K =
        (therm && therm["T_reference_C"]) ? therm["T_reference_C"].as<double>() + 273.15
                                          : 298.15;
    if (therm && therm["initial_temp_C"])
        cd.thermal.initial_T_K = therm["initial_temp_C"].as<double>() + 273.15;
    else
        cd.thermal.initial_T_K = cd.thermal.T_K;
    cd.thermal.inner_wall_T_K =
        (therm && therm["inner_wall_temp_C"]) ? therm["inner_wall_temp_C"].as<double>() + 273.15
                                              : cd.thermal.initial_T_K;
    cd.thermal.outer_T_K =
        (therm && therm["outer_temp_C"]) ? therm["outer_temp_C"].as<double>() + 273.15
                                         : cd.thermal.initial_T_K;
    cd.thermal.top_T_K =
        (therm && therm["top_temp_C"]) ? therm["top_temp_C"].as<double>() + 273.15
                                       : cd.thermal.initial_T_K;
    cd.thermal.bottom_T_K =
        (therm && therm["bottom_temp_C"]) ? therm["bottom_temp_C"].as<double>() + 273.15
                                          : cd.thermal.initial_T_K;
    cd.thermal.outer_bc =
        (therm && therm["outer_bc"]) ? therm["outer_bc"].as<std::string>() : "prescribed";
    cd.thermal.top_bc =
        (therm && therm["top_bc"]) ? therm["top_bc"].as<std::string>() : "flux_zero";
    cd.thermal.bottom_bc =
        (therm && therm["bottom_bc"]) ? therm["bottom_bc"].as<std::string>() : "flux_zero";
    cd.thermal.k_W_m_K =
        (therm && therm["k_W_m_K"]) ? therm["k_W_m_K"].as<double>() : 2.5;
    cd.thermal.rho_kg_m3 =
        (therm && therm["rho_kg_m3"]) ? therm["rho_kg_m3"].as<double>() : 2160.0;
    cd.thermal.cp_J_kg_K =
        (therm && therm["cp_J_kg_K"]) ? therm["cp_J_kg_K"].as<double>() : 900.0;
    cd.thermal.dt_thermal_s =
        (therm && therm["dt_thermal_h"]) ? therm["dt_thermal_h"].as<double>() * 3600.0
                                         : -1.0;
    cd.thermal.beta =
        (therm && therm["beta"]) ? therm["beta"].as<double>() : 0.5;
    if (cd.thermal.outer_bc != "prescribed" && cd.thermal.outer_bc != "flux_zero")
        throw std::runtime_error("thermal.outer_bc must be prescribed or flux_zero");
    if (cd.thermal.top_bc != "prescribed" && cd.thermal.top_bc != "flux_zero")
        throw std::runtime_error("thermal.top_bc must be prescribed or flux_zero");
    if (cd.thermal.bottom_bc != "prescribed" && cd.thermal.bottom_bc != "flux_zero")
        throw std::runtime_error("thermal.bottom_bc must be prescribed or flux_zero");
    if (therm && therm["layers"]) {
        cd.thermal.layers.clear();
        for (const auto& node : therm["layers"]) {
            ThermalLayer layer;
            layer.z_top_m = req_double(node, "z_top_m", "thermal.layers");
            layer.z_bottom_m = req_double(node, "z_bottom_m", "thermal.layers");
            layer.k_W_m_K = req_double(node, "k_W_per_mK", "thermal.layers");
            layer.rho_kg_m3 = node["rho_kg_per_m3"]
                ? node["rho_kg_per_m3"].as<double>() : cd.thermal.rho_kg_m3;
            layer.cp_J_kg_K = node["cp_J_per_kgK"]
                ? node["cp_J_per_kgK"].as<double>() : cd.thermal.cp_J_kg_K;
            if (layer.z_bottom_m <= layer.z_top_m)
                throw std::runtime_error("thermal.layers z_bottom_m must exceed z_top_m");
            if (layer.k_W_m_K <= 0.0 || layer.rho_kg_m3 <= 0.0 || layer.cp_J_kg_K <= 0.0)
                throw std::runtime_error("thermal.layers properties must be positive");
            cd.thermal.layers.push_back(layer);
        }
    }

    // time
    auto time = root["time"];
    if (time) {
        double total_h = time["total_h"] ? time["total_h"].as<double>() : 360.0;
        double dt_h    = time["dt_h"]    ? time["dt_h"].as<double>()    : 1.0;
        cd.time.total_s  = total_h * 3600.0;
        cd.time.dt_s     = dt_h    * 3600.0;
        cd.time.scheme   = time["scheme"] ? time["scheme"].as<std::string>() : "explicit";
        cd.time.tol_local = time["tol_local"] ? time["tol_local"].as<double>() : 1.0e-10;
        cd.time.tol_global = time["tol_global"] ? time["tol_global"].as<double>() : 1.0e-4;
        cd.time.dt_min_s = (time["dt_min_h"] ? time["dt_min_h"].as<double>() : 1.0e-12) * 3600.0;
        cd.time.dt_max_s = (time["dt_max_h"] ? time["dt_max_h"].as<double>() : 10.0) * 3600.0;

        // Variable dt schedule: time.steps: [{until_h: X, dt_h: Y}, ...]
        if (time["steps"]) {
            for (const auto& seg : time["steps"]) {
                TimeSegment ts;
                ts.until_s = seg["until_h"].as<double>() * 3600.0;
                ts.dt_s    = seg["dt_h"].as<double>()    * 3600.0;
                cd.time.steps.push_back(ts);
            }
        }
    } else {
        cd.time.total_s = 360.0 * 3600.0;
        cd.time.dt_s    = 1.0   * 3600.0;
        cd.time.scheme  = "explicit";
        cd.time.tol_local = 1.0e-10;
        cd.time.tol_global = 1.0e-4;
        cd.time.dt_min_s = 1.0e-12 * 3600.0;
        cd.time.dt_max_s = 10.0 * 3600.0;
    }
    if (cd.thermal.dt_thermal_s < 0.0)
        cd.thermal.dt_thermal_s = cd.time.dt_s;

    // creep flags
    auto creep = root["creep"];
    cd.creep.elastic_only = creep && creep["elastic_only"] && creep["elastic_only"].as<bool>();
    cd.creep.secondary    = creep && creep["secondary"]    && creep["secondary"].as<bool>();
    cd.creep.primary      = creep && creep["primary"]      && creep["primary"].as<bool>();
    cd.creep.tertiary     = creep && creep["tertiary"]     && creep["tertiary"].as<bool>();
    cd.creep.damage       = creep && creep["damage"]       && creep["damage"].as<bool>();
    if (creep && creep["primary_model"])
        cd.creep.primary_model = creep["primary_model"].as<std::string>();
    if (creep && creep["tertiary_model"])
        cd.creep.tertiary_model = creep["tertiary_model"].as<std::string>();
    if (creep && creep["dilatancy_envelope"])
        cd.creep.dilatancy_envelope = creep["dilatancy_envelope"].as<std::string>();

    if (creep && creep["motta_v1"]) {
        auto node = creep["motta_v1"];
        if (node["n_d"]) cd.motta_v1.n_d = node["n_d"].as<double>();
        if (node["A_d"]) cd.motta_v1.A_d = node["A_d"].as<double>();
        if (node["m_d"]) cd.motta_v1.m_d = node["m_d"].as<double>();
        if (node["p_d"]) cd.motta_v1.p_d = node["p_d"].as<double>();
        if (node["D_max"]) cd.motta_v1.D_max = node["D_max"].as<double>();
    }
    if (creep && creep["isv_sh_dm"]) {
        auto node = creep["isv_sh_dm"];
        if (node["e0_s"]) cd.isv_sh_dm.e0_s = node["e0_s"].as<double>();
        if (node["sig_ref"]) cd.isv_sh_dm.sig_ref = node["sig_ref"].as<double>();
        if (node["n"]) cd.isv_sh_dm.n = node["n"].as<double>();
        if (node["Q_J_mol"]) cd.isv_sh_dm.Q_J_mol = node["Q_J_mol"].as<double>();
        if (node["T0"]) cd.isv_sh_dm.T0 = node["T0"].as<double>();
        if (node["K_h"]) cd.isv_sh_dm.K_h = node["K_h"].as<double>();
    }
    if (creep && creep["wang_2004"]) {
        auto node = creep["wang_2004"];
        if (node["n_d"]) cd.wang_2004.n_d = node["n_d"].as<double>();
        if (node["A_d"]) cd.wang_2004.A_d = node["A_d"].as<double>();
        if (node["m_d"]) cd.wang_2004.m_d = node["m_d"].as<double>();
        if (node["p_d"]) cd.wang_2004.p_d = node["p_d"].as<double>();
        if (node["D_max"]) cd.wang_2004.D_max = node["D_max"].as<double>();
    }
    if (creep && creep["aubertin_isv_sh_d"]) {
        auto node = creep["aubertin_isv_sh_d"];
        if (node["e0_s"]) cd.aubertin_isv_sh_d.e0_s = node["e0_s"].as<double>();
        if (node["sig0"]) cd.aubertin_isv_sh_d.sig0 = node["sig0"].as<double>();
        if (node["n"]) cd.aubertin_isv_sh_d.n = node["n"].as<double>();
        if (node["Q_J_mol"]) cd.aubertin_isv_sh_d.Q_J_mol = node["Q_J_mol"].as<double>();
        if (node["T0"]) cd.aubertin_isv_sh_d.T0 = node["T0"].as<double>();
        if (node["K1"]) cd.aubertin_isv_sh_d.K1 = node["K1"].as<double>();
        if (node["K2"]) cd.aubertin_isv_sh_d.K2 = node["K2"].as<double>();
        if (node["A_d"]) cd.aubertin_isv_sh_d.A_d = node["A_d"].as<double>();
        if (node["m_d"]) cd.aubertin_isv_sh_d.m_d = node["m_d"].as<double>();
        if (node["n_d"]) cd.aubertin_isv_sh_d.n_d = node["n_d"].as<double>();
        if (node["p_d"]) cd.aubertin_isv_sh_d.p_d = node["p_d"].as<double>();
        if (node["D_max"]) cd.aubertin_isv_sh_d.D_max = node["D_max"].as<double>();
    }
    if (creep && creep["spier"]) {
        auto node = creep["spier"];
        if (node["a"]) cd.spier.a = node["a"].as<double>();
        if (node["b_Pa"]) cd.spier.b_Pa = node["b_Pa"].as<double>();
    }
    if (creep && creep["ratigan"]) {
        auto node = creep["ratigan"];
        if (node["c"]) cd.ratigan.c = node["c"].as<double>();
        if (node["d_Pa"]) cd.ratigan.d_Pa = node["d_Pa"].as<double>();
        if (node["m"]) cd.ratigan.m = node["m"].as<double>();
    }
    if (creep && creep["devries"]) {
        auto node = creep["devries"];
        if (node["e_Pa"]) cd.devries.e_Pa = node["e_Pa"].as<double>();
        if (node["f"]) cd.devries.f = node["f"].as<double>();
        if (node["sigma0_Pa"]) cd.devries.sigma0_Pa = node["sigma0_Pa"].as<double>();
    }
    if (creep && creep["hunsche"]) {
        auto node = creep["hunsche"];
        if (node["g_Pa"]) cd.hunsche.g_Pa = node["g_Pa"].as<double>();
        if (node["I1_ref_Pa"]) cd.hunsche.I1_ref_Pa = node["I1_ref_Pa"].as<double>();
        if (node["h"]) cd.hunsche.h = node["h"].as<double>();
    }

    if (cd.creep.elastic_only)
        std::cerr << "[info] elastic_only=true — time loop skipped\n";
    if (cd.creep.secondary && cd.time.scheme == "explicit" && cd.lithology == "taquidrita")
        std::cerr << "[warn] taquidrita with explicit scheme: consider implicit_adaptive\n";
    if (cd.creep.primary && !cd.creep.secondary)
        std::cerr << "[warn] primary-only: transient decays to zero, not DM. "
                     "Use secondary:true for physically correct steady state.\n";
    if (cd.creep.primary &&
        cd.creep.primary_model != "EDMT" &&
        cd.creep.primary_model != "isv_sh_dm")
        throw std::runtime_error("primary:true requires primary_model:EDMT or primary_model:isv_sh_dm");
    if (cd.creep.primary && cd.creep.primary_model == "isv_sh_dm" && !cd.creep.secondary)
        std::cerr << "[warn] isv_sh_dm primary-only decays to zero; use secondary:true for DM saturation.\n";
    if (cd.creep.tertiary) {
        const bool known_envelope =
            cd.creep.dilatancy_envelope == "Spier" ||
            cd.creep.dilatancy_envelope == "Ratigan" ||
            cd.creep.dilatancy_envelope == "DeVries" ||
            cd.creep.dilatancy_envelope == "Hunsche" ||
            cd.creep.dilatancy_envelope == "Huensche";
        const bool is_motta = cd.creep.tertiary_model == "MottaV1" && known_envelope;
        const bool is_wang = cd.creep.tertiary_model == "wang_2004";
        const bool is_aubertin = cd.creep.tertiary_model == "aubertin_isv_sh_d";
        if (!is_motta && !is_wang && !is_aubertin)
            throw std::runtime_error("tertiary:true currently requires tertiary_model:MottaV1 + dilatancy_envelope:Spier|Ratigan|DeVries|Hunsche, tertiary_model:wang_2004, or tertiary_model:aubertin_isv_sh_d");
        if (is_wang && !cd.creep.damage)
            throw std::runtime_error("tertiary_model:wang_2004 requires creep.damage:true");
    }

    // output
    auto output = root["output"];
    if (output) {
        cd.output.every_n_steps =
            output["every_n_steps"] ? output["every_n_steps"].as<int>() : 10;
        cd.output.vtu =
            output["vtu"] && output["vtu"].as<bool>();
        cd.output.vtu_every_n_steps =
            output["vtu_every_n_steps"] ? output["vtu_every_n_steps"].as<int>() : 10;
        cd.output.revolve_3d =
            output["revolve_3d"] && output["revolve_3d"].as<bool>();
        cd.output.damage_tracking =
            output["damage_tracking"] && output["damage_tracking"].as<bool>();
        if (output["damage_thresholds"]) {
            cd.output.damage_thresholds.clear();
            for (const auto& value : output["damage_thresholds"])
                cd.output.damage_thresholds.push_back(value.as<double>());
        }
        cd.output.failure_D_critical =
            output["failure_D_critical"] ? output["failure_D_critical"].as<double>() : 0.5;
        cd.output.creep_rate_multiplier_threshold =
            output["creep_rate_multiplier_threshold"]
                ? output["creep_rate_multiplier_threshold"].as<double>() : 10.0;
    }
    if (cd.output.damage_thresholds.empty())
        cd.output.damage_thresholds = {0.1, 0.3, 0.5, 0.8};
    if (cd.output.every_n_steps <= 0)
        throw std::runtime_error("output.every_n_steps must be positive");
    if (cd.output.vtu_every_n_steps <= 0)
        throw std::runtime_error("output.vtu_every_n_steps must be positive");
    if (cd.output.failure_D_critical <= 0.0 || cd.output.failure_D_critical >= 1.0)
        throw std::runtime_error("output.failure_D_critical must be in (0,1)");
    if (cd.output.creep_rate_multiplier_threshold <= 0.0)
        throw std::runtime_error("output.creep_rate_multiplier_threshold must be positive");

    return cd;
}
