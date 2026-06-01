#include "elements/axisym_1d_L3.hpp"
#include <array>
#include <cmath>
#include <stdexcept>

namespace {
constexpr double kPi = 3.14159265358979323846;
// 3-point Gauss-Legendre on [−1,1]: exact for polynomials up to degree 5
constexpr double kGP3[3]  = {-0.7745966692414834, 0.0, 0.7745966692414834};
constexpr double kGW3[3]  = { 0.5555555555555556, 0.8888888888888888, 0.5555555555555556};
}

AxisymL3::AxisymL3() {
    for (int i = 0; i < kNGauss; ++i)
        gp_[i] = {kGP3[i], kGW3[i]};
}

std::span<const GaussPoint> AxisymL3::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

// Shape functions for 3-node Lagrangian line, nodes at ξ = {−1, 0, +1}:
//   N1 = ξ(ξ−1)/2,  N2 = 1−ξ²,  N3 = ξ(ξ+1)/2
void AxisymL3::shape_functions(double xi, std::span<double> N) const {
    N[0] = 0.5 * xi * (xi - 1.0);
    N[1] = 1.0 - xi * xi;
    N[2] = 0.5 * xi * (xi + 1.0);
}

void AxisymL3::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    shape_functions(gp.xi, N);
}

// dN_i/dξ
void AxisymL3::shape_derivatives(double xi, std::span<double> dNdxi) const {
    dNdxi[0] = xi - 0.5;
    dNdxi[1] = -2.0 * xi;
    dNdxi[2] = xi + 0.5;
}

void AxisymL3::shape_derivatives(const GaussPoint& gp,
                                  std::span<double> dNdxi,
                                  std::span<double> dNdeta) const {
    shape_derivatives(gp.xi, dNdxi);
    for (double& value : dNdeta)
        value = 0.0;
}

// B matrix (4×3): Voigt {εr, εθ, εz, γrz}
//   col i = [ dNi/dr,  Ni/r,  0,  0 ]^T
// dNi/dr = dNi/dξ / J  where  J = Σ dNi/dξ · r_i  (scalar Jacobian)
// r = Σ Ni · r_i  (isoparametric mapping)
Eigen::MatrixXd AxisymL3::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[3], dNdxi[3];
    shape_functions(gp.xi, N);
    shape_derivatives(gp.xi, dNdxi);

    double r = 0.0, J = 0.0;
    for (int i = 0; i < 3; ++i) {
        r += N[i]     * node_coords[i].r;
        J += dNdxi[i] * node_coords[i].r;
    }
    if (r <= 0.0)
        throw std::domain_error("AxisymL3::B_matrix: r <= 0 at Gauss point");
    if (std::abs(J) < 1e-30)
        throw std::domain_error("AxisymL3::B_matrix: zero Jacobian");

    Eigen::MatrixXd B = Eigen::MatrixXd::Zero(4, 3);
    for (int i = 0; i < 3; ++i) {
        B(0, i) = dNdxi[i] / J;  // εr = dNi/dr
        B(1, i) = N[i]     / r;  // εθ = Ni/r  ← the critical axisymmetric term
        // B(2,i) = 0               εz = 0 (1D radial, plane-strain)
        // B(3,i) = 0               γrz = 0
    }
    return B;
}

Eigen::MatrixXd AxisymL3::B_matrix(double xi,
                                    std::span<const double> node_r) const {
    std::array<Node, 3> coords{};
    for (int i = 0; i < 3; ++i)
        coords[i] = Node{node_r[i], 0.0};
    return B_matrix(GaussPoint{xi, 1.0}, std::span<const Node>(coords.data(), coords.size()));
}

// jacobian_weight = 2π * r(ξ) * |J(ξ)| * w_GP
double AxisymL3::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[3], dNdxi[3];
    shape_functions(gp.xi, N);
    shape_derivatives(gp.xi, dNdxi);

    double r = 0.0, J = 0.0;
    for (int i = 0; i < 3; ++i) {
        r += N[i]     * node_coords[i].r;
        J += dNdxi[i] * node_coords[i].r;
    }
    // weight parameter is passed per Gauss point in the element loop;
    // this function returns the geometric factor only (caller multiplies by w_GP)
    // — BUT interface contract says "inclui o peso de Gauss", so we return full weight.
    // The caller does NOT multiply by w_GP again.
    //
    // To honour the interface, we compute: 2π·r·|J|·w_GP.
    // We find w_GP by matching xi to the stored Gauss points.
    double w = gp.weight;
    return 2.0 * kPi * r * std::abs(J) * w;
}

double AxisymL3::jacobian_weight(double xi,
                                  std::span<const double> node_r) const {
    std::array<Node, 3> coords{};
    for (int i = 0; i < 3; ++i)
        coords[i] = Node{node_r[i], 0.0};

    double weight = 0.0;
    for (const auto& gp : gp_) {
        if (std::abs(gp.xi - xi) < 1e-12) {
            weight = gp.weight;
            break;
        }
    }
    return jacobian_weight(GaussPoint{xi, weight}, std::span<const Node>(coords.data(), coords.size()));
}
