#include "elements/axisym_2d_t6.hpp"

#include <cmath>
#include <stdexcept>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kDetJTol = 1.0e-12;

struct T6Geometry {
    double r = 0.0;
    double detJ = 0.0;
    double dr_dxi = 0.0;
    double dr_deta = 0.0;
    double dz_dxi = 0.0;
    double dz_deta = 0.0;
};

T6Geometry compute_geometry(const double* N,
                            const double* dN_dxi,
                            const double* dN_deta,
                            std::span<const Node> node_coords) {
    T6Geometry geo;
    for (int i = 0; i < 6; ++i) {
        geo.r += N[i] * node_coords[i].r;
        geo.dr_dxi += dN_dxi[i] * node_coords[i].r;
        geo.dr_deta += dN_deta[i] * node_coords[i].r;
        geo.dz_dxi += dN_dxi[i] * node_coords[i].z;
        geo.dz_deta += dN_deta[i] * node_coords[i].z;
    }
    geo.detJ = geo.dr_dxi * geo.dz_deta - geo.dr_deta * geo.dz_dxi;
    return geo;
}
} // namespace

AxisymT6::AxisymT6() {
    constexpr double a = 0.816847572980459;
    constexpr double b = 0.091576213509771;
    constexpr double c = 0.108103018168070;
    constexpr double d = 0.445948490915965;
    constexpr double w1 = 0.054975871827661;
    constexpr double w2 = 0.111690794839006;

    gp_[0] = GaussPoint{b, w1, b};
    gp_[1] = GaussPoint{a, w1, b};
    gp_[2] = GaussPoint{b, w1, a};
    gp_[3] = GaussPoint{d, w2, d};
    gp_[4] = GaussPoint{c, w2, d};
    gp_[5] = GaussPoint{d, w2, c};
}

std::span<const GaussPoint> AxisymT6::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

void AxisymT6::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    const double L1 = 1.0 - gp.xi - gp.eta;
    const double L2 = gp.xi;
    const double L3 = gp.eta;

    N[0] = L1 * (2.0 * L1 - 1.0);
    N[1] = L2 * (2.0 * L2 - 1.0);
    N[2] = L3 * (2.0 * L3 - 1.0);
    N[3] = 4.0 * L1 * L2;
    N[4] = 4.0 * L2 * L3;
    N[5] = 4.0 * L3 * L1;
}

void AxisymT6::shape_derivatives(const GaussPoint& gp,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    const double L1 = 1.0 - gp.xi - gp.eta;
    const double L2 = gp.xi;
    const double L3 = gp.eta;

    dN_dxi[0] = -(4.0 * L1 - 1.0);
    dN_dxi[1] = 4.0 * L2 - 1.0;
    dN_dxi[2] = 0.0;
    dN_dxi[3] = 4.0 * (L1 - L2);
    dN_dxi[4] = 4.0 * L3;
    dN_dxi[5] = -4.0 * L3;

    dN_deta[0] = -(4.0 * L1 - 1.0);
    dN_deta[1] = 0.0;
    dN_deta[2] = 4.0 * L3 - 1.0;
    dN_deta[3] = -4.0 * L2;
    dN_deta[4] = 4.0 * L2;
    dN_deta[5] = 4.0 * (L1 - L3);
}

Eigen::MatrixXd AxisymT6::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[6], dN_dxi[6], dN_deta[6];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const T6Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymT6::B_matrix: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymT6::B_matrix: singular Jacobian");

    Eigen::MatrixXd B = Eigen::MatrixXd::Zero(4, 12);
    for (int i = 0; i < 6; ++i) {
        const double dN_dr = ( geo.dz_deta * dN_dxi[i] - geo.dz_dxi * dN_deta[i]) / geo.detJ;
        const double dN_dz = (-geo.dr_deta * dN_dxi[i] + geo.dr_dxi * dN_deta[i]) / geo.detJ;
        const int col_r = 2 * i;
        const int col_z = col_r + 1;

        B(0, col_r) = dN_dr;
        B(1, col_r) = N[i] / geo.r;
        B(2, col_z) = dN_dz;
        B(3, col_r) = dN_dz;
        B(3, col_z) = dN_dr;
    }
    return B;
}

double AxisymT6::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[6], dN_dxi[6], dN_deta[6];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const T6Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymT6::jacobian_weight: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymT6::jacobian_weight: singular Jacobian");

    return 2.0 * kPi * geo.r * std::abs(geo.detJ) * gp.weight;
}
