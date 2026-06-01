#include "elements/axisym_2d_q4.hpp"

#include <cmath>
#include <stdexcept>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kDetJTol = 1.0e-12;

struct Q4Geometry {
    double r = 0.0;
    double detJ = 0.0;
    double dr_dxi = 0.0;
    double dr_deta = 0.0;
    double dz_dxi = 0.0;
    double dz_deta = 0.0;
};

Q4Geometry compute_geometry(const double* N,
                            const double* dN_dxi,
                            const double* dN_deta,
                            std::span<const Node> node_coords) {
    Q4Geometry geo;
    for (int i = 0; i < 4; ++i) {
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

AxisymQ4::AxisymQ4() {
    const double a = 1.0 / std::sqrt(3.0);
    gp_[0] = GaussPoint{-a, 1.0, -a};
    gp_[1] = GaussPoint{ a, 1.0, -a};
    gp_[2] = GaussPoint{ a, 1.0,  a};
    gp_[3] = GaussPoint{-a, 1.0,  a};
}

std::span<const GaussPoint> AxisymQ4::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

void AxisymQ4::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    const double xi = gp.xi;
    const double eta = gp.eta;
    N[0] = 0.25 * (1.0 - xi) * (1.0 - eta);
    N[1] = 0.25 * (1.0 + xi) * (1.0 - eta);
    N[2] = 0.25 * (1.0 + xi) * (1.0 + eta);
    N[3] = 0.25 * (1.0 - xi) * (1.0 + eta);
}

void AxisymQ4::shape_derivatives(const GaussPoint& gp,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    const double xi = gp.xi;
    const double eta = gp.eta;

    dN_dxi[0] = -0.25 * (1.0 - eta);
    dN_dxi[1] =  0.25 * (1.0 - eta);
    dN_dxi[2] =  0.25 * (1.0 + eta);
    dN_dxi[3] = -0.25 * (1.0 + eta);

    dN_deta[0] = -0.25 * (1.0 - xi);
    dN_deta[1] = -0.25 * (1.0 + xi);
    dN_deta[2] =  0.25 * (1.0 + xi);
    dN_deta[3] =  0.25 * (1.0 - xi);
}

Eigen::MatrixXd AxisymQ4::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[4], dN_dxi[4], dN_deta[4];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const Q4Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymQ4::B_matrix: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymQ4::B_matrix: singular Jacobian");

    Eigen::MatrixXd B = Eigen::MatrixXd::Zero(4, 8);
    for (int i = 0; i < 4; ++i) {
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

double AxisymQ4::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[4], dN_dxi[4], dN_deta[4];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const Q4Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymQ4::jacobian_weight: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymQ4::jacobian_weight: singular Jacobian");

    return 2.0 * kPi * geo.r * std::abs(geo.detJ) * gp.weight;
}
