#include <catch2/catch_test_macros.hpp>

#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

#include "constitutive/ConstitutiveModel.hpp"
#include "elements/axisym_1d_L3.hpp"
#include "solver/Assembler.hpp"
#include "solver/DamageDiagnostics.hpp"
#include "thermal/profile_field.hpp"

namespace fs = std::filesystem;

namespace {
class ScriptedRateModel : public ConstitutiveModel {
public:
    ViscousResult evaluate(const Stress&,
                           const InternalState& state,
                           double,
                           double) const override {
        const double rate = state.eps_v_eff;
        Strain eps_dot = Strain::Zero();
        eps_dot[0] = rate;
        eps_dot[1] = -0.5 * rate;
        eps_dot[2] = -0.5 * rate;
        return {eps_dot, state};
    }

    Eigen::Matrix4d D_elastic() const override {
        return Eigen::Matrix4d::Identity();
    }
};

DamageTrackingOptions options() {
    DamageTrackingOptions opt;
    opt.enabled = true;
    opt.damage_thresholds = {0.1, 0.3, 0.5, 0.8};
    opt.failure_D_critical = 0.5;
    opt.creep_rate_multiplier_threshold = 10.0;
    opt.D_max = 0.99;
    opt.dm = DMParams{1.0e-9, 1.0e6, 300.0, 3.0, 5.0, 0.0};
    opt.E_Pa = 25.0e9;
    opt.nu = 0.3;
    opt.has_dm_reference = true;
    return opt;
}

TimeState make_state(int total_gp, double D, double rate) {
    TimeState state;
    state.u_total = Eigen::VectorXd::Zero(3);
    state.sigma_gp.assign(total_gp, Stress{2.0e6, -1.0e6, -1.0e6, 0.0});
    state.eps_v_gp.assign(total_gp, Strain::Zero());
    state.eps_th_gp.assign(total_gp, Strain::Zero());
    state.state_gp.assign(total_gp, InternalState{});
    for (auto& gp_state : state.state_gp) {
        gp_state.damage_D = D;
        gp_state.eps_v_eff = rate;
    }
    return state;
}

std::string slurp(const fs::path& path) {
    std::ifstream in(path);
    std::ostringstream out;
    out << in.rdbuf();
    return out.str();
}
} // namespace

TEST_CASE("DamageDiagnostics: disabled tracking does not create damage CSVs",
          "[damage][diagnostics]") {
    const fs::path out = fs::temp_directory_path() / "saltcreep_damage_diag_disabled";
    fs::remove_all(out);
    AxisymL3 elem;
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    ProfileField thermal = ProfileField::make_constant(300.0);
    ScriptedRateModel model;

    auto opt = options();
    opt.enabled = false;
    DamageDiagnostics diag(out, mesh, elem, thermal, opt);
    TimeState state = make_state(mesh.n_elements * static_cast<int>(elem.gauss_points().size()),
                                 0.0, 1.0e-8);
    diag.initialize(state, model, 0.0);
    diag.record(state, model, 3600.0);

    REQUIRE_FALSE(fs::exists(out / "damage_events.csv"));
    REQUIRE_FALSE(fs::exists(out / "damage_wall.csv"));
}

TEST_CASE("DamageDiagnostics: damage thresholds are recorded in increasing order",
          "[damage][diagnostics]") {
    const fs::path out = fs::temp_directory_path() / "saltcreep_damage_diag_thresholds";
    fs::remove_all(out);
    AxisymL3 elem;
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    ProfileField thermal = ProfileField::make_constant(300.0);
    ScriptedRateModel model;
    DamageDiagnostics diag(out, mesh, elem, thermal, options());
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());

    diag.initialize(make_state(total_gp, 0.0, 1.0e-8), model, 0.0);
    diag.record(make_state(total_gp, 0.15, 1.0e-8), model, 3600.0);
    diag.record(make_state(total_gp, 0.35, 1.0e-8), model, 7200.0);
    diag.record(make_state(total_gp, 0.55, 1.0e-8), model, 10800.0);
    diag.record(make_state(total_gp, 0.85, 1.0e-8), model, 14400.0);

    const std::string events = slurp(out / "damage_events.csv");
    const auto p01 = events.find("D_threshold_0.1");
    const auto p03 = events.find("D_threshold_0.3");
    const auto p05 = events.find("D_threshold_0.5");
    const auto p08 = events.find("D_threshold_0.8");
    REQUIRE(p01 != std::string::npos);
    REQUIRE(p03 != std::string::npos);
    REQUIRE(p05 != std::string::npos);
    REQUIRE(p08 != std::string::npos);
    REQUIRE(p01 < p03);
    REQUIRE(p03 < p05);
    REQUIRE(p05 < p08);
    REQUIRE(events.find("failure_D_critical") != std::string::npos);
}

TEST_CASE("DamageDiagnostics: wall damage history is monotone for monotone D",
          "[damage][diagnostics]") {
    const fs::path out = fs::temp_directory_path() / "saltcreep_damage_diag_wall";
    fs::remove_all(out);
    AxisymL3 elem;
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    ProfileField thermal = ProfileField::make_constant(300.0);
    ScriptedRateModel model;
    DamageDiagnostics diag(out, mesh, elem, thermal, options());
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());

    diag.initialize(make_state(total_gp, 0.0, 1.0e-8), model, 0.0);
    diag.record(make_state(total_gp, 0.2, 1.0e-8), model, 3600.0);
    diag.record(make_state(total_gp, 0.4, 1.0e-8), model, 7200.0);

    const std::string wall = slurp(out / "damage_wall.csv");
    REQUIRE(wall.find("\n0.000000000000,0.000000000000") != std::string::npos);
    REQUIRE(wall.find("\n1.000000000000,0.200000000000") != std::string::npos);
    REQUIRE(wall.find("\n2.000000000000,0.400000000000") != std::string::npos);
}

TEST_CASE("DamageDiagnostics: creep-rate threshold event is recorded",
          "[damage][diagnostics]") {
    const fs::path out = fs::temp_directory_path() / "saltcreep_damage_diag_rate";
    fs::remove_all(out);
    AxisymL3 elem;
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    ProfileField thermal = ProfileField::make_constant(300.0);
    ScriptedRateModel model;
    DamageDiagnostics diag(out, mesh, elem, thermal, options());
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());

    diag.initialize(make_state(total_gp, 0.0, 1.0e-12), model, 0.0);
    diag.record(make_state(total_gp, 0.0, 1.0e-2), model, 3600.0);

    REQUIRE(slurp(out / "damage_events.csv").find("creep_rate_threshold") != std::string::npos);
}

TEST_CASE("DamageDiagnostics: inflection is detected from three consecutive rates",
          "[damage][diagnostics]") {
    const fs::path out = fs::temp_directory_path() / "saltcreep_damage_diag_inflection";
    fs::remove_all(out);
    AxisymL3 elem;
    Mesh1D mesh = build_mesh_L3(1.0, 2.0, 1, 1.0);
    ProfileField thermal = ProfileField::make_constant(300.0);
    ScriptedRateModel model;
    DamageDiagnostics diag(out, mesh, elem, thermal, options());
    const int total_gp = mesh.n_elements * static_cast<int>(elem.gauss_points().size());

    diag.initialize(make_state(total_gp, 0.0, 3.0e-8), model, 0.0);
    diag.record(make_state(total_gp, 0.0, 2.0e-8), model, 3600.0);
    diag.record(make_state(total_gp, 0.0, 1.0e-8), model, 7200.0);
    diag.record(make_state(total_gp, 0.0, 2.0e-8), model, 10800.0);

    REQUIRE(slurp(out / "damage_events.csv").find("inflection") != std::string::npos);
}
