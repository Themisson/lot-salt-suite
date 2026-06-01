#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include <cmath>

#include "elements/axisym_1d_L3.hpp"
#include "constitutive/elastic_isotropic.hpp"

// ---------------------------------------------------------------------------
// Patch test for AxisymL3
// A quadratic element should reproduce linear fields exactly (patch test).
// We test:
//  1. Shape functions sum to 1 (partition of unity) at several ξ values.
//  2. A linear displacement field u_r(r) = α·r is exactly interpolated.
//  3. The strain εr = du/dr = α is exactly recovered at every Gauss point.
//  4. The strain εθ = u/r = α·r/r = α is exactly recovered too.
// ---------------------------------------------------------------------------

TEST_CASE("AxisymL3: partition of unity", "[patch][element]") {
    AxisymL3 elem;
    double N[3];
    for (double xi : {-1.0, -0.5, 0.0, 0.5, 1.0, -0.7745966, 0.7745966}) {
        elem.shape_functions(xi, N);
        double sum = N[0] + N[1] + N[2];
        REQUIRE(std::abs(sum - 1.0) < 1e-14);
    }
}

TEST_CASE("AxisymL3: linear displacement field reproduced exactly", "[patch][element]") {
    AxisymL3 elem;
    // Element from r=1 to r=3 (mid-node at r=2)
    const double coords[3] = {1.0, 2.0, 3.0};
    const double alpha     = 5.0e-4;   // linear coefficient: u_r = alpha * r

    // Nodal displacements for u_r(r) = alpha * r
    const double ue[3] = {alpha * coords[0], alpha * coords[1], alpha * coords[2]};

    for (const auto& gp : elem.gauss_points()) {
        // Interpolate r at this Gauss point
        double N[3]; elem.shape_functions(gp.xi, N);
        double r = N[0] * coords[0] + N[1] * coords[1] + N[2] * coords[2];

        // Interpolate u_r
        double u_interp = N[0] * ue[0] + N[1] * ue[1] + N[2] * ue[2];
        REQUIRE(std::abs(u_interp - alpha * r) < 1e-14 * std::abs(alpha * r));

        // B matrix: should give εr = alpha and εθ = alpha
        Eigen::MatrixXd B = elem.B_matrix(gp.xi, coords);
        Eigen::Map<const Eigen::Vector3d> ue_map(ue);
        Eigen::Vector4d strain = B * ue_map;

        REQUIRE(std::abs(strain[0] - alpha) < 1e-12);  // εr = alpha
        REQUIRE(std::abs(strain[1] - alpha) < 1e-12);  // εθ = alpha (u_r/r = alpha*r/r)
        REQUIRE(std::abs(strain[2])         < 1e-14);  // εz = 0
        REQUIRE(std::abs(strain[3])         < 1e-14);  // γrz = 0
    }
}

TEST_CASE("AxisymL3: jacobian_weight is positive and matches manual formula", "[patch][element]") {
    AxisymL3 elem;
    const double coords[3] = {1.0, 2.0, 3.0};  // r1=1, r2=3, mid=2
    constexpr double kTwoPi = 2.0 * 3.14159265358979323846;

    for (const auto& gp : elem.gauss_points()) {
        double jw = elem.jacobian_weight(gp.xi, coords);
        REQUIRE(jw > 0.0);

        // Manual: J = Σ dN_i/dξ * r_i
        double dN[3]; elem.shape_derivatives(gp.xi, dN);
        double N[3];  elem.shape_functions(gp.xi, N);
        double r = 0.0, J = 0.0;
        for (int i = 0; i < 3; ++i) { r += N[i] * coords[i]; J += dN[i] * coords[i]; }
        double expected = kTwoPi * r * std::abs(J) * gp.weight;
        REQUIRE(std::abs(jw - expected) < 1e-12 * expected);
    }
}
