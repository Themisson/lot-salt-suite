#include "elements/axisym_2d_t3.hpp"

#include <cmath>
#include <stdexcept>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kDetJTol = 1.0e-12;

struct T3Geometry {
    double r = 0.0;
    double detJ = 0.0;
    double dr_dxi = 0.0;
    double dr_deta = 0.0;
    double dz_dxi = 0.0;
    double dz_deta = 0.0;
};

T3Geometry compute_geometry(const double* N,
                            const double* dN_dxi,
                            const double* dN_deta,
                            std::span<const Node> node_coords) {
    T3Geometry geo;
    for (int i = 0; i < 3; ++i) {
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

AxisymT3::AxisymT3() {
    gp_[0] = GaussPoint{1.0 / 6.0, 1.0 / 6.0, 1.0 / 6.0};
    gp_[1] = GaussPoint{2.0 / 3.0, 1.0 / 6.0, 1.0 / 6.0};
    gp_[2] = GaussPoint{1.0 / 6.0, 1.0 / 6.0, 2.0 / 3.0};
}

std::span<const GaussPoint> AxisymT3::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

void AxisymT3::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    N[0] = 1.0 - gp.xi - gp.eta;
    N[1] = gp.xi;
    N[2] = gp.eta;
}

void AxisymT3::shape_derivatives(const GaussPoint&,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    dN_dxi[0] = -1.0;
    dN_dxi[1] =  1.0;
    dN_dxi[2] =  0.0;

    dN_deta[0] = -1.0;
    dN_deta[1] =  0.0;
    dN_deta[2] =  1.0;
}

Eigen::MatrixXd AxisymT3::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[3], dN_dxi[3], dN_deta[3];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const T3Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymT3::B_matrix: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymT3::B_matrix: singular Jacobian");

    Eigen::MatrixXd B = Eigen::MatrixXd::Zero(4, 6);
    for (int i = 0; i < 3; ++i) {
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

double AxisymT3::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[3], dN_dxi[3], dN_deta[3];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const T3Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymT3::jacobian_weight: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymT3::jacobian_weight: singular Jacobian");

    return 2.0 * kPi * geo.r * std::abs(geo.detJ) * gp.weight;
}
