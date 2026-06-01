#include <iostream>
#include <fstream>
#include <filesystem>
#include <vector>
#include <algorithm>
#include <cmath>
#include <memory>
#include <chrono>
#include <string>

#include "io/CaseParser.hpp"
#include "elements/ElementFactory.hpp"
#include "constitutive/elastic_isotropic.hpp"
#include "constitutive/double_mechanism.hpp"
#include "constitutive/edmt.hpp"
#include "constitutive/isv_sh_dm.hpp"
#include "constitutive/dilatancy_envelope.hpp"
#include "constitutive/motta_v1.hpp"
#include "constitutive/wang_2004.hpp"
#include "constitutive/aubertin_isv_sh_d.hpp"
#include "thermal/profile_field.hpp"
#include "thermal/conduction_1d_field.hpp"
#include "thermal/conduction_2d_field.hpp"
#include "solver/Assembler.hpp"
#include "solver/DamageDiagnostics.hpp"
#include "solver/ElasticSolver.hpp"
#include "solver/TimeIntegrator.hpp"
#include "solver/ImplicitAdaptiveIntegrator.hpp"
#include "solver/PerformanceStats.hpp"
#include "solver/WallPressureField.hpp"
#include "io/VtuWriter.hpp"
#include "mesh/error_estimator.hpp"
#include "mesh/mesh_refiner.hpp"

namespace fs = std::filesystem;
namespace {
constexpr double kMetersToInches = 39.37007874015748;
}

// ── Helper: compute geostatic stress at each Gauss point ─────────────────────
// tension-positive convention: compressive stresses are negative.
// sigma_v = -overburden_grad * depth  (compression → negative)
// sigma_h = k0 * sigma_v
static std::vector<Stress> build_geostatic(const Mesh&     mesh,
                                            const Element&  element,
                                            double          k0,
                                            double          overburden_grad,
                                            double          depth_m,
                                            bool            depth_profile = false) {
    const int n_gp = static_cast<int>(element.gauss_points().size());
    std::vector<Stress> geo(mesh.n_elements * n_gp);

    double sigma_v = -overburden_grad * depth_m;   // compressive → negative
    double sigma_h = k0 * sigma_v;

    const int nne = element.n_nodes();
    const auto gps = element.gauss_points();
    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        for (int i = 0; i < nne; ++i)
            coords[i] = mesh.nodes[mesh.elem_nodes[nne * e + i]];
        for (int g = 0; g < n_gp; ++g) {
            if (depth_profile) {
                std::vector<double> N(nne);
                element.shape_functions(gps[g], coords, N);
                double z_gp = 0.0;
                for (int i = 0; i < nne; ++i)
                    z_gp += N[i] * coords[i].z;
                sigma_v = -overburden_grad * (depth_m + z_gp);
                sigma_h = k0 * sigma_v;
            }
            geo[e * n_gp + g] = Stress{sigma_h, sigma_h, sigma_v, 0.0};
        }
    }

    return geo;
}

// ── CSV output for elastic-only results ──────────────────────────────────────
static void write_elastic_csv(const fs::path& out_dir,
                               const Mesh& mesh,
                               const Element& elem,
                               const Eigen::VectorXd& u,
                               const Eigen::Matrix4d& D) {
    fs::create_directories(out_dir);
    std::ofstream csv(out_dir / "displacements.csv");
    csv << "r_m,u_r_m,sigma_rr_Pa,sigma_tt_Pa,sigma_zz_Pa\n";

    const int nne = elem.n_nodes();
    const int ndpn = elem.n_dofs_per_node();
    std::vector<double> srr(mesh.n_nodes, 0), stt(mesh.n_nodes, 0);
    std::vector<double> szz(mesh.n_nodes, 0), cnt(mesh.n_nodes, 0);

    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        Eigen::VectorXd ue(nne * ndpn);
        for (int i = 0; i < nne; ++i) {
            int gn = mesh.elem_nodes[nne * e + i];
            coords[i] = mesh.nodes[gn];
            for (int d = 0; d < ndpn; ++d)
                ue[i * ndpn + d] = u[mesh.dof_index(gn, d)];
        }
        for (const auto& gp : elem.gauss_points()) {
            Eigen::MatrixXd B = elem.B_matrix(gp, coords);
            Eigen::Vector4d sigma = D * B * ue;
            for (int i = 0; i < nne; ++i) {
                int gn = mesh.elem_nodes[nne * e + i];
                srr[gn] += sigma[0]; stt[gn] += sigma[1];
                szz[gn] += sigma[2]; cnt[gn] += 1.0;
            }
        }
    }
    for (int n = 0; n < mesh.n_nodes; ++n) {
        double sc = std::max(cnt[n], 1.0);
        csv << mesh.nodes[n].r << "," << u[mesh.dof_index(n, 0)] << ","
            << srr[n]/sc << "," << stt[n]/sc << "," << szz[n]/sc << "\n";
    }
    std::cout << "Output: " << (out_dir / "displacements.csv") << "\n";
}

static std::vector<Stress> compute_elastic_sigma_gp(const Mesh& mesh,
                                                    const Element& elem,
                                                    const Eigen::VectorXd& u,
                                                    const Eigen::Matrix4d& D) {
    const int nne = elem.n_nodes();
    const int ndpn = elem.n_dofs_per_node();
    const int n_gp = static_cast<int>(elem.gauss_points().size());
    std::vector<Stress> sigma_gp(mesh.n_elements * n_gp, Stress::Zero());

    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        Eigen::VectorXd ue(nne * ndpn);
        for (int i = 0; i < nne; ++i) {
            const int gn = mesh.elem_nodes[nne * e + i];
            coords[i] = mesh.nodes[gn];
            for (int d = 0; d < ndpn; ++d)
                ue[i * ndpn + d] = u[mesh.dof_index(gn, d)];
        }
        for (int g = 0; g < n_gp; ++g) {
            Eigen::MatrixXd B = elem.B_matrix(elem.gauss_points()[g], coords);
            sigma_gp[e * n_gp + g] = D * B * ue;
        }
    }
    return sigma_gp;
}

static TimeState compute_initial_time_state(const Mesh& mesh,
                                            const Element& elem,
                                            const ConstitutiveModel& model,
                                            const Eigen::SparseMatrix<double>& K,
                                            const Eigen::VectorXd& f_external,
                                            const std::vector<Stress>& sigma_geo,
                                            const std::vector<int>& fixed_dofs) {
    Eigen::VectorXd f_net = f_external -
        Assembler::assemble_geostatic_force(mesh, elem, sigma_geo);
    ElasticSolver solver;
    SolverResult result = solver.solve(K, f_net, fixed_dofs);

    const int n_gp = static_cast<int>(elem.gauss_points().size());
    const int total_gp = mesh.n_elements * n_gp;
    TimeState state;
    state.u_total = result.u;
    state.eps_v_gp.assign(total_gp, Strain::Zero());
    state.eps_th_gp.assign(total_gp, Strain::Zero());
    state.state_gp.assign(total_gp, InternalState{});
    state.sigma_gp.assign(total_gp, Stress::Zero());

    const Eigen::Matrix4d D = model.D_elastic();
    const int nne = elem.n_nodes();
    const int ndpn = elem.n_dofs_per_node();
    for (int e = 0; e < mesh.n_elements; ++e) {
        std::vector<Node> coords(nne);
        Eigen::VectorXd ue(nne * ndpn);
        for (int i = 0; i < nne; ++i) {
            const int node = mesh.elem_nodes[nne * e + i];
            coords[i] = mesh.nodes[node];
            for (int d = 0; d < ndpn; ++d)
                ue[i * ndpn + d] = state.u_total[mesh.dof_index(node, d)];
        }
        for (int g = 0; g < n_gp; ++g) {
            const int idx = e * n_gp + g;
            state.sigma_gp[idx] = D * (elem.B_matrix(elem.gauss_points()[g], coords) * ue)
                                  + sigma_geo[idx];
        }
    }
    return state;
}

static VtuOutputOptions make_vtu_options(const CaseData& cd) {
    VtuOutputOptions options;
    options.enabled = cd.output.vtu;
    options.every_n_steps = cd.output.vtu_every_n_steps;
    options.revolve_3d = cd.output.revolve_3d;
    options.case_name = cd.name;
    options.well_radius_m = cd.geom.Ri;
    options.depth_origin_m = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    return options;
}

static DamageTrackingOptions make_damage_options(const CaseData& cd) {
    DamageTrackingOptions options;
    const bool intrinsic_damage = cd.creep.tertiary_model == "aubertin_isv_sh_d";
    options.enabled = cd.output.damage_tracking && (cd.creep.damage || intrinsic_damage);
    options.damage_thresholds = cd.output.damage_thresholds;
    options.failure_D_critical = cd.output.failure_D_critical;
    options.creep_rate_multiplier_threshold = cd.output.creep_rate_multiplier_threshold;
    if (cd.creep.tertiary_model == "wang_2004")
        options.D_max = cd.wang_2004.D_max;
    else if (cd.creep.tertiary_model == "aubertin_isv_sh_d")
        options.D_max = cd.aubertin_isv_sh_d.D_max;
    else
        options.D_max = cd.motta_v1.D_max;
    options.dm = cd.dm;
    options.E_Pa = cd.E_Pa;
    options.nu = cd.nu;
    options.has_dm_reference = true;
    return options;
}

static std::shared_ptr<const WallPressureField> make_wall_pressure_field(
    const CaseData& cd,
    double depth_origin_m) {
    if (cd.fluid.mode == "hydrostatic_depth_profile") {
        return std::make_shared<HydrostaticMudPressureField>(
            cd.fluid.weight_lb_per_gal,
            depth_origin_m,
            cd.fluid.surface_pressure_Pa);
    }
    return std::make_shared<ConstantWallPressureField>(cd.fluid_Pa);
}

static bool is_axisym_2d_element(const std::string& element_type) {
    return element_type == "axisym_2d_Q4" ||
           element_type == "axisym_2d_T3" ||
           element_type == "axisym_2d_Q8" ||
           element_type == "axisym_2d_Q9" ||
           element_type == "axisym_2d_AQ9" ||
           element_type == "axisym_2d_T6";
}

static std::vector<int> build_fixed_dofs(const Mesh& mesh) {
    if (mesh.dofs_per_node == 1)
        return {mesh.dof_index(mesh.n_nodes - 1, 0)};

    const auto max_it = std::max_element(
        mesh.nodes.begin(), mesh.nodes.end(),
        [](const Node& a, const Node& b) { return a.r < b.r; });
    const double Re = max_it->r;
    const double tol = 1.0e-10 * std::max(1.0, std::abs(Re));

    std::vector<int> fixed;
    fixed.reserve(static_cast<size_t>(mesh.n_nodes * 2));
    for (int n = 0; n < mesh.n_nodes; ++n) {
        fixed.push_back(mesh.dof_index(n, 1));
        if (std::abs(mesh.nodes[n].r - Re) <= tol)
            fixed.push_back(mesh.dof_index(n, 0));
    }
    std::sort(fixed.begin(), fixed.end());
    fixed.erase(std::unique(fixed.begin(), fixed.end()), fixed.end());
    return fixed;
}

static int adapt_mesh_if_requested(const CaseData& cd,
                                   Mesh2D& mesh,
                                   const Element& elem,
                                   const ConstitutiveModel& model,
                                   const WallPressureField& wall_pressure,
                                   double depth_m) {
    if (!cd.mesh.adaptive)
        return 0;

    ErrorEstimator estimator;
    MeshRefiner refiner;
    std::vector<int> levels(mesh.n_elements, 0);
    int iterations = 0;

    for (int iter = 0; iter < cd.mesh.max_refinement_levels; ++iter) {
        auto K = Assembler::assemble_K(mesh, elem, model);
        auto f_ext = Assembler::assemble_boundary_pressure(mesh, elem, wall_pressure, 0.0);
        auto sigma_geo = build_geostatic(mesh, elem, cd.k0,
                                         cd.overburden_grad_Pa_per_m, depth_m,
                                         cd.geostatic_mode == "depth_profile");
        auto fixed_dofs = build_fixed_dofs(mesh);
        TimeState state = compute_initial_time_state(
            mesh, elem, model, K, f_ext, sigma_geo, fixed_dofs);

        ErrorEstimatorOptions options;
        options.error_threshold = cd.mesh.error_threshold;
        options.damage_refinement_threshold = cd.mesh.damage_refinement_threshold;
        auto errors = estimator.compute_errors(mesh, elem, model, state);
        auto marked = estimator.mark_for_refinement(errors, options);

        for (int e = 0; e < mesh.n_elements; ++e) {
            if (levels[e] >= cd.mesh.max_refinement_levels)
                marked[e] = 0;
        }
        const int n_marked = static_cast<int>(
            std::count(marked.begin(), marked.end(), static_cast<char>(1)));
        if (n_marked == 0)
            break;
        if (elem.n_nodes() != 3 && elem.n_nodes() != 4) {
            throw std::runtime_error(
                "mesh.adaptive can estimate error for this element, but refinement is currently available only for axisym_2d_Q4 and axisym_2d_T3");
        }

        RefinedMesh refined = refiner.refine_elements(mesh, elem, marked, levels);
        FieldTransferResult transfer = refiner.interpolate_fields(
            mesh, refined.mesh, elem, elem, state.u_total, state,
            refined.parent_element);
        (void)transfer;

        mesh = std::move(refined.mesh);
        levels = std::move(refined.refinement_level);
        ++iterations;

        std::cout << "[adapt] iteration " << iterations
                  << ": marked=" << n_marked
                  << " elements=" << mesh.n_elements
                  << " dofs=" << mesh.total_dofs() << "\n";
    }
    return iterations;
}

static void write_metadata_json(const fs::path& out_dir,
                                const CaseData& cd,
                                const Mesh& mesh,
                                double wall_time_s,
                                const PerformanceStats& stats,
                                int adaptive_iterations = 0) {
    auto escape_json = [](const std::string& value) {
        std::string escaped;
        escaped.reserve(value.size());
        for (char c : value) {
            if (c == '\\' || c == '"')
                escaped.push_back('\\');
            escaped.push_back(c);
        }
        return escaped;
    };

    fs::create_directories(out_dir);
    std::ofstream json(out_dir / "metadata.json");
    const double depth_origin_m = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    const double well_diameter_m = 2.0 * cd.geom.Ri;
    json << "{\n";
    json << "  \"case_name\": \"" << escape_json(cd.name) << "\",\n";
    json << "  \"element_type\": \"" << escape_json(cd.element_type) << "\",\n";
    json << "  \"well_radius_m\": " << cd.geom.Ri << ",\n";
    json << "  \"well_diameter_m\": " << well_diameter_m << ",\n";
    json << "  \"well_diameter_in\": " << well_diameter_m * kMetersToInches << ",\n";
    json << "  \"outer_radius_m\": " << cd.geom.Ri * cd.geom.outer_factor << ",\n";
    json << "  \"depth_origin_m\": " << depth_origin_m << ",\n";
    json << "  \"layer_thickness_m\": " << cd.geom.layer_thickness_m << ",\n";
    json << "  \"fluid_mode\": \"" << escape_json(cd.fluid.mode) << "\",\n";
    json << "  \"fluid_pressure_Pa\": " << cd.fluid_Pa << ",\n";
    json << "  \"fluid_weight_lb_per_gal\": " << cd.fluid.weight_lb_per_gal << ",\n";
    json << "  \"fluid_surface_pressure_Pa\": " << cd.fluid.surface_pressure_Pa << ",\n";
    json << "  \"geostatic_mode\": \"" << escape_json(cd.geostatic_mode) << "\",\n";
    json << "  \"n_elements_radial\": " << cd.mesh.n_radial << ",\n";
    json << "  \"n_elements_axial\": " << cd.mesh.n_axial << ",\n";
    json << "  \"mesh_ratio\": " << cd.mesh.ratio << ",\n";
    json << "  \"mesh_adaptive\": " << (cd.mesh.adaptive ? "true" : "false") << ",\n";
    json << "  \"adaptive_iterations\": " << adaptive_iterations << ",\n";
    json << "  \"final_n_elements\": " << mesh.n_elements << ",\n";
    json << "  \"n_dofs\": " << mesh.total_dofs() << ",\n";
    json << "  \"time_scheme\": \"" << escape_json(cd.time.scheme) << "\",\n";
    json << "  \"lithology\": {\n";
    json << "    \"primary\": \"" << escape_json(cd.lithology) << "\",\n";
    json << "    \"layers\": [";
    if (!cd.lithology_layers.empty())
        json << "\n";
    for (size_t i = 0; i < cd.lithology_layers.size(); ++i) {
        const auto& layer = cd.lithology_layers[i];
        json << "      {\"z_top_m\": " << layer.z_top_m
             << ", \"z_bottom_m\": " << layer.z_bottom_m
             << ", \"material\": \"" << escape_json(layer.material)
             << "\", \"label\": \"" << escape_json(layer.label) << "\"}";
        json << (i + 1 == cd.lithology_layers.size() ? "\n" : ",\n");
    }
    json << "    ]\n";
    json << "  },\n";
    json << "  \"primary_model\": \"" << escape_json(cd.creep.primary_model) << "\",\n";
    json << "  \"tertiary_model\": \"" << escape_json(cd.creep.tertiary_model) << "\",\n";
    json << "  \"dilatancy_envelope\": \"" << escape_json(cd.creep.dilatancy_envelope) << "\",\n";
    json << "  \"creep_flags\": {\n";
    json << "    \"secondary\": " << (cd.creep.secondary ? "true" : "false") << ",\n";
    json << "    \"primary\": " << (cd.creep.primary ? "true" : "false") << ",\n";
    json << "    \"tertiary\": " << (cd.creep.tertiary ? "true" : "false") << "\n";
    json << "  },\n";
    json << "  \"thermal_enabled\": " << (cd.thermal.enabled ? "true" : "false") << ",\n";
    json << "  \"thermal_mode\": \"" << escape_json(cd.thermal.mode) << "\",\n";
    json << "  \"damage_tracking\": " << (cd.output.damage_tracking ? "true" : "false") << ",\n";
    json << "  \"damage_thresholds\": [";
    for (size_t i = 0; i < cd.output.damage_thresholds.size(); ++i) {
        if (i > 0) json << ", ";
        json << cd.output.damage_thresholds[i];
    }
    json << "],\n";
    json << "  \"failure_D_critical\": " << cd.output.failure_D_critical << ",\n";
    json << "  \"total_time_h\": " << (cd.time.total_s / 3600.0) << ",\n";
    json << "  \"wall_time_s\": " << wall_time_s << ",\n";
    json << "  \"omp_threads\": " << saltcreep_omp_max_threads() << ",\n";
    json << "  \"time_assembly_s\": " << stats.time_assembly_s << ",\n";
    json << "  \"time_solve_s\": " << stats.time_solve_s << ",\n";
    json << "  \"time_constitutive_s\": " << stats.time_constitutive_s << "\n";
    json << "}\n";
}

// ─────────────────────────────────────────────────────────────────────────────
int main(int argc, char* argv[]) {
    if (argc < 2) { std::cerr << "Usage: saltcreep <case.yaml>\n"; return 1; }

    CaseData cd;
    try {
        cd = parse_case(fs::path(argv[1]));
    } catch (const std::exception& ex) {
        std::cerr << "Error parsing case: " << ex.what() << "\n";
        return 2;
    }

    const double Ri = cd.geom.Ri;
    const double Re = Ri * cd.geom.outer_factor;

    // Element
    auto elem = make_element(cd.element_type);

    // Mesh
    const bool is_1d = cd.element_type == "axisym_1d_L3";
    Mesh1D mesh_1d;
    Mesh2D mesh_2d;
    Mesh* mesh_ptr = nullptr;
    if (is_1d) {
        mesh_1d = build_mesh_L3(Ri, Re, cd.mesh.n_radial, cd.mesh.ratio);
        mesh_ptr = &mesh_1d;
    } else if (is_axisym_2d_element(cd.element_type)) {
        mesh_2d = build_mesh_structured_2d(cd.element_type, Ri, Re, cd.geom.layer_thickness_m,
                                           cd.mesh.n_radial, cd.mesh.n_axial,
                                           cd.mesh.ratio);
        mesh_ptr = &mesh_2d;
    } else {
        std::cerr << "Error: unsupported element.type '" << cd.element_type << "'\n";
        return 3;
    }
    Mesh& mesh = *mesh_ptr;

    // Constitutive model dispatch:
    //   elastic_only            → ElasticIsotropic (zero viscous rate)
    //   tertiary + damage       → MottaV1 (DM amplified by damage)
    //   secondary && !primary   → DoubleMechanism (DM only)
    //   primary (± secondary)   → EDMT (transient + optional secondary)
    std::unique_ptr<ConstitutiveModel> model;
    if (cd.creep.tertiary && cd.creep.damage && cd.creep.tertiary_model == "MottaV1") {
        model = std::make_unique<MottaV1>(
            cd.dm, cd.motta_v1, make_dilatancy_envelope(cd), cd.E_Pa, cd.nu);
    } else if (cd.creep.tertiary && cd.creep.damage && cd.creep.tertiary_model == "wang_2004") {
        model = std::make_unique<Wang2004>(cd.dm, cd.wang_2004, cd.E_Pa, cd.nu);
    } else if (cd.creep.tertiary && cd.creep.tertiary_model == "aubertin_isv_sh_d") {
        model = std::make_unique<AubertinISVSHD>(cd.aubertin_isv_sh_d, cd.E_Pa, cd.nu);
    } else if (cd.creep.primary && cd.creep.primary_model == "isv_sh_dm") {
        model = std::make_unique<ISVSHDMunson>(cd.dm, cd.isv_sh_dm, cd.E_Pa, cd.nu, cd.creep.secondary);
    } else if (cd.creep.primary) {
        model = std::make_unique<EDMT>(cd.dm, cd.edmt, cd.E_Pa, cd.nu, cd.creep.secondary);
    } else if (cd.creep.secondary) {
        model = std::make_unique<DoubleMechanism>(cd.dm, cd.E_Pa, cd.nu);
    } else {
        model = std::make_unique<ElasticIsotropic>(cd.E_Pa, cd.nu);
    }

    double depth = cd.depths.burial_m + cd.depths.water_depth_m + cd.depths.salt_above_m;
    auto wall_pressure = make_wall_pressure_field(cd, depth);
    int adaptive_iterations = 0;
    if (cd.mesh.adaptive) {
        if (is_1d) {
            std::cerr << "Error: mesh.adaptive requires a 2D axisymmetric element\n";
            return 3;
        }
        try {
            adaptive_iterations = adapt_mesh_if_requested(
                cd, mesh_2d, *elem, *model, *wall_pressure, depth);
        } catch (const std::exception& ex) {
            std::cerr << "Error during mesh adaptation: " << ex.what() << "\n";
            return 3;
        }
    }

    // Thermal field
    std::unique_ptr<ThermalField> thermal;
    if (cd.thermal.mode == "profile") {
        thermal = std::make_unique<ProfileField>(
            ProfileField::make_profile(cd.thermal.seabed_temp_C,
                                       cd.depths.burial_m + cd.depths.water_depth_m,
                                       cd.thermal.grad_C_per_m,
                                       cd.thermal.alpha_thermal,
                                       cd.thermal.T_reference_K));
    } else if (cd.thermal.mode == "conduction_1d") {
        if (!is_1d) {
            std::cerr << "Error: thermal.mode conduction_1d is currently supported only with axisym_1d_L3\n";
            return 3;
        }
        Conduction1DOptions thermal_options;
        thermal_options.k_W_m_K = cd.thermal.k_W_m_K;
        thermal_options.rho_kg_m3 = cd.thermal.rho_kg_m3;
        thermal_options.cp_J_kg_K = cd.thermal.cp_J_kg_K;
        thermal_options.initial_T_K = cd.thermal.initial_T_K;
        thermal_options.inner_wall_T_K = cd.thermal.inner_wall_T_K;
        thermal_options.outer_T_K = cd.thermal.outer_T_K;
        thermal_options.dt_thermal_s = cd.thermal.dt_thermal_s;
        thermal_options.beta = cd.thermal.beta;
        thermal_options.alpha_thermal = cd.thermal.alpha_thermal;
        thermal_options.T_reference_K = cd.thermal.T_reference_K;
        thermal_options.outer_bc = cd.thermal.outer_bc;
        thermal = std::make_unique<Conduction1DField>(mesh_1d, thermal_options);
    } else if (cd.thermal.mode == "conduction_2d") {
        if (is_1d) {
            std::cerr << "Error: thermal.mode conduction_2d requires a 2D axisymmetric element\n";
            return 3;
        }
        Conduction2DOptions thermal_options;
        thermal_options.k_W_m_K = cd.thermal.k_W_m_K;
        thermal_options.rho_kg_m3 = cd.thermal.rho_kg_m3;
        thermal_options.cp_J_kg_K = cd.thermal.cp_J_kg_K;
        thermal_options.initial_T_K = cd.thermal.initial_T_K;
        thermal_options.inner_wall_T_K = cd.thermal.inner_wall_T_K;
        thermal_options.outer_T_K = cd.thermal.outer_T_K;
        thermal_options.top_T_K = cd.thermal.top_T_K;
        thermal_options.bottom_T_K = cd.thermal.bottom_T_K;
        thermal_options.dt_thermal_s = cd.thermal.dt_thermal_s;
        thermal_options.beta = cd.thermal.beta;
        thermal_options.alpha_thermal = cd.thermal.alpha_thermal;
        thermal_options.T_reference_K = cd.thermal.T_reference_K;
        thermal_options.outer_bc = cd.thermal.outer_bc;
        thermal_options.top_bc = cd.thermal.top_bc;
        thermal_options.bottom_bc = cd.thermal.bottom_bc;
        thermal_options.layers.reserve(cd.thermal.layers.size());
        for (const auto& layer : cd.thermal.layers) {
            thermal_options.layers.push_back(Conduction2DLayer{
                layer.z_top_m,
                layer.z_bottom_m,
                layer.k_W_m_K,
                layer.rho_kg_m3,
                layer.cp_J_kg_K,
            });
        }
        thermal = std::make_unique<Conduction2DField>(mesh_2d, *elem, thermal_options);
    } else {
        thermal = std::make_unique<ProfileField>(
            ProfileField::make_constant(cd.thermal.T_K,
                                        cd.thermal.alpha_thermal,
                                        cd.thermal.T_reference_K));
    }

    PerformanceStats initial_stats;
    const auto simulation_start = std::chrono::steady_clock::now();

    // Stiffness matrix
    auto assembly_start = std::chrono::steady_clock::now();
    auto K = Assembler::assemble_K(mesh, *elem, *model);

    // External load (fluid pressure traction at inner wall)
    auto f_ext = Assembler::assemble_boundary_pressure(
        mesh, *elem, *wall_pressure, 0.0, 0.0);
    auto assembly_end = std::chrono::steady_clock::now();
    initial_stats.time_assembly_s += std::chrono::duration<double>(
        assembly_end - assembly_start).count();

    fs::path out_dir = fs::path("results") / cd.name;

    // ── elastic only ─────────────────────────────────────────────────────────
    if (cd.creep.elastic_only) {
        ElasticSolver solver;
        auto solve_start = std::chrono::steady_clock::now();
        auto result = solver.solve(K, f_ext, {});
        auto solve_end = std::chrono::steady_clock::now();
        initial_stats.time_solve_s += std::chrono::duration<double>(
            solve_end - solve_start).count();
        write_elastic_csv(out_dir, mesh, *elem, result.u, model->D_elastic());
        if (cd.output.vtu) {
            const auto sigma_gp = compute_elastic_sigma_gp(
                mesh, *elem, result.u, model->D_elastic());
            const int total_gp = mesh.n_elements *
                static_cast<int>(elem->gauss_points().size());
            const std::vector<Strain> eps_v_gp(total_gp, Strain::Zero());
            const std::vector<InternalState> state_gp(total_gp, InternalState{});
            const std::string file = VtuWriter::frame_filename(cd.name, 0);
            VtuSnapshot snapshot{&result.u, &sigma_gp, &eps_v_gp,
                                 &state_gp, thermal.get(), 0.0};
            VtuWriter::write(out_dir / file, mesh, *elem, snapshot);
            VtuWriter::write_pvd(out_dir / (cd.name + ".pvd"),
                                 {VtuFrame{file, 0.0}});
        }
        const auto end = std::chrono::steady_clock::now();
        const double wall_time_s = std::chrono::duration<double>(
            end - simulation_start).count();
        write_metadata_json(out_dir, cd, mesh, wall_time_s, initial_stats,
                            adaptive_iterations);
        return 0;
    }

    // ── time integration (secondary creep) ───────────────────────────────────
    auto sigma_geo = build_geostatic(mesh, *elem, cd.k0,
                                     cd.overburden_grad_Pa_per_m, depth,
                                     cd.geostatic_mode == "depth_profile");

    // Outer wall (u[Re]=0) must be pinned: without it, the geostatic force at Re
    // drives spurious outward expansion (see SESTSAL %SUPPORT condition).
    std::vector<int> fixed_dofs = build_fixed_dofs(mesh);
    int output_every = cd.output.every_n_steps;
    if (auto* outp = getenv("SALTCREEP_OUTPUT_EVERY"))  // NOLINT
        output_every = std::stoi(outp);
    VtuOutputOptions vtu_options = make_vtu_options(cd);
    DamageTrackingOptions damage_options = make_damage_options(cd);

    if (cd.time.scheme == "implicit_adaptive") {
        ImplicitAdaptiveOptions options;
        options.tol_local = cd.time.tol_local;
        options.tol_global = cd.time.tol_global;
        options.dt_min_s = cd.time.dt_min_s;
        options.dt_max_s = cd.time.dt_max_s;
        ImplicitAdaptiveIntegrator integrator(mesh, *elem, *model, *thermal,
                                              K, f_ext, sigma_geo, fixed_dofs,
                                              options, initial_stats, wall_pressure);
        if (!cd.time.steps.empty())
            integrator.run_schedule(cd.time.steps, cd.time.total_s, output_every, out_dir,
                                    vtu_options, damage_options);
        else
            integrator.run(cd.time.dt_s, cd.time.total_s, output_every, out_dir,
                           vtu_options, damage_options);
        const auto end = std::chrono::steady_clock::now();
        const double wall_time_s = std::chrono::duration<double>(
            end - simulation_start).count();
        write_metadata_json(out_dir, cd, mesh, wall_time_s,
                            integrator.performance_stats(), adaptive_iterations);
    } else if (cd.time.scheme == "explicit") {
        TimeIntegrator integrator(mesh, *elem, *model, *thermal,
                                  K, f_ext, sigma_geo, fixed_dofs,
                                  initial_stats, wall_pressure);
        if (!cd.time.steps.empty())
            integrator.run_schedule(cd.time.steps, cd.time.total_s, output_every, out_dir,
                                    vtu_options, damage_options);
        else
            integrator.run(cd.time.dt_s, cd.time.total_s, output_every, out_dir,
                           vtu_options, damage_options);
        const auto end = std::chrono::steady_clock::now();
        const double wall_time_s = std::chrono::duration<double>(
            end - simulation_start).count();
        write_metadata_json(out_dir, cd, mesh, wall_time_s,
                            integrator.performance_stats(), adaptive_iterations);
    } else {
        std::cerr << "Error: unknown time.scheme '" << cd.time.scheme
                  << "' (expected explicit or implicit_adaptive)\n";
        return 4;
    }
    return 0;
}
