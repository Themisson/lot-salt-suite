#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <algorithm>
#include <cmath>
#include <filesystem>

#include "elements/ElementFactory.hpp"
#include "io/CaseParser.hpp"
#include "solver/Assembler.hpp"
#include "solver/WallPressureField.hpp"

namespace {
constexpr double kLbPerGalToKgPerM3 = 119.826;
constexpr double kGravity = 9.80665;
constexpr double kTwoPi = 2.0 * 3.14159265358979323846;

std::filesystem::path find_data_dir() {
    for (const auto& candidate : {
             std::filesystem::path("data"),
             std::filesystem::path("../data"),
             std::filesystem::path("../../data")}) {
        if (std::filesystem::exists(candidate / "litologias"))
            return candidate;
    }
    throw std::runtime_error("Cannot find data/litologias");
}

std::filesystem::path find_case(const std::filesystem::path& relative) {
    for (const auto& root : {
             std::filesystem::path("."),
             std::filesystem::path(".."),
             std::filesystem::path("../..")}) {
        const auto candidate = root / relative;
        if (std::filesystem::exists(candidate))
            return candidate;
    }
    throw std::runtime_error("Cannot find case " + relative.string());
}

double expected_mud_pressure(double ppg, double depth_m, double surface_pressure = 0.0) {
    return surface_pressure + ppg * kLbPerGalToKgPerM3 * kGravity * depth_m;
}
} // namespace

TEST_CASE("HydrostaticMudPressureField evaluates mud pressure by physical depth",
          "[pressure][fluid]") {
    const double ppg = 8.5;
    const double depth_origin = 4100.0;
    HydrostaticMudPressureField field(ppg, depth_origin);

    REQUIRE(field.mud_density_kg_m3() == Catch::Approx(ppg * kLbPerGalToKgPerM3));
    REQUIRE(field.pressure_gradient_Pa_m() ==
            Catch::Approx(ppg * kLbPerGalToKgPerM3 * kGravity));
    REQUIRE(field.pressure_at(Eigen::Vector2d{0.155575, 0.0}, 0.0) ==
            Catch::Approx(expected_mud_pressure(ppg, depth_origin)));
    REQUIRE(field.pressure_at(Eigen::Vector2d{0.155575, 1000.0}, 0.0) ==
            Catch::Approx(expected_mud_pressure(ppg, depth_origin + 1000.0)));
}

TEST_CASE("Parser: legacy mud weight remains a constant wall pressure",
          "[pressure][parser]") {
    const CaseData cd = parse_case(
        find_case("cases/tcc/modelo_A.yaml"),
        find_data_dir());
    const double depth = cd.depths.water_depth_m + cd.depths.burial_m + cd.depths.salt_above_m;

    REQUIRE(cd.fluid.mode == "constant");
    REQUIRE(cd.fluid_Pa == Catch::Approx(
        expected_mud_pressure(cd.fluid.weight_lb_per_gal, depth)));
}

TEST_CASE("Parser: APB 1D case computes mud pressure at the case depth",
          "[pressure][parser]") {
    const CaseData cd = parse_case(
        find_case("cases/apb/mud_gradient_1d_8p5ppg.yaml"),
        find_data_dir());
    const double depth = cd.depths.water_depth_m + cd.depths.burial_m + cd.depths.salt_above_m;

    REQUIRE(cd.element_type == "axisym_1d_L3");
    REQUIRE(cd.fluid.mode == "hydrostatic_depth_profile");
    REQUIRE(cd.fluid.weight_lb_per_gal == Catch::Approx(8.5));
    REQUIRE(cd.fluid_Pa == Catch::Approx(expected_mud_pressure(8.5, depth)));
}

TEST_CASE("Assembler: 1D hydrostatic field matches scalar Neumann pressure",
          "[pressure][assembler]") {
    const double Ri = 0.155575;
    const double Re = 15.5575;
    const double depth = 4100.0;
    const double ppg = 8.5;
    Mesh1D mesh = build_mesh_L3(Ri, Re, 3, 10.0);
    auto elem = make_element("axisym_1d_L3");
    HydrostaticMudPressureField field(ppg, depth);

    const auto f_field = Assembler::assemble_boundary_pressure(mesh, *elem, field, 0.0);
    const auto f_scalar = Assembler::assemble_neumann(
        mesh, expected_mud_pressure(ppg, depth), 0.0);

    REQUIRE((f_field - f_scalar).norm() == Catch::Approx(0.0).margin(1.0e-8));
}

TEST_CASE("Assembler: 2D hydrostatic pressure integrates along the inner wall",
          "[pressure][assembler][2d]") {
    const double Ri = 0.155575;
    const double Re = 15.5575;
    const double height = 1000.0;
    const double depth = 4100.0;
    const double ppg = 8.5;
    Mesh2D mesh = build_mesh_structured_2d("axisym_2d_Q8", Ri, Re, height, 1, 1, 1.0);
    auto elem = make_element("axisym_2d_Q8");
    HydrostaticMudPressureField field(ppg, depth);

    const auto f = Assembler::assemble_boundary_pressure(mesh, *elem, field, 0.0);

    double total_inner_radial_force = 0.0;
    for (int n = 0; n < mesh.n_nodes; ++n) {
        if (std::abs(mesh.nodes[n].r - Ri) <= 1.0e-12)
            total_inner_radial_force += f[mesh.dof_index(n, 0)];
    }

    const double p_top = expected_mud_pressure(ppg, depth);
    const double p_bottom = expected_mud_pressure(ppg, depth + height);
    const double expected_total = kTwoPi * Ri * height * 0.5 * (p_top + p_bottom);

    REQUIRE(total_inner_radial_force == Catch::Approx(expected_total).epsilon(1.0e-12));
}
