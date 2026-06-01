#include "elements/axisym_2d_q8.hpp"

#include <cmath>
#include <stdexcept>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kDetJTol = 1.0e-12;

struct Q8Geometry {
    double r = 0.0;
    double detJ = 0.0;
    double dr_dxi = 0.0;
    double dr_deta = 0.0;
    double dz_dxi = 0.0;
    double dz_deta = 0.0;
};

Q8Geometry compute_geometry(const double* N,
                            const double* dN_dxi,
                            const double* dN_deta,
                            std::span<const Node> node_coords) {
    Q8Geometry geo;
    for (int i = 0; i < 8; ++i) {
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

AxisymQ8::AxisymQ8() {
    const double a = std::sqrt(3.0 / 5.0);
    const double pts[3] = {-a, 0.0, a};
    const double w[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};
    int k = 0;
    for (int j = 0; j < 3; ++j) {
        for (int i = 0; i < 3; ++i) {
            gp_[k++] = GaussPoint{pts[i], w[i] * w[j], pts[j]};
        }
    }
}

std::span<const GaussPoint> AxisymQ8::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

void AxisymQ8::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    const double xi = gp.xi;
    const double eta = gp.eta;

    N[0] = -0.25 * (1.0 - xi) * (1.0 - eta) * (1.0 + xi + eta);
    N[1] = -0.25 * (1.0 + xi) * (1.0 - eta) * (1.0 - xi + eta);
    N[2] = -0.25 * (1.0 + xi) * (1.0 + eta) * (1.0 - xi - eta);
    N[3] = -0.25 * (1.0 - xi) * (1.0 + eta) * (1.0 + xi - eta);
    N[4] =  0.5  * (1.0 - xi * xi) * (1.0 - eta);
    N[5] =  0.5  * (1.0 + xi) * (1.0 - eta * eta);
    N[6] =  0.5  * (1.0 - xi * xi) * (1.0 + eta);
    N[7] =  0.5  * (1.0 - xi) * (1.0 - eta * eta);
}

void AxisymQ8::shape_derivatives(const GaussPoint& gp,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    const double xi = gp.xi;
    const double eta = gp.eta;

    dN_dxi[0] = 0.25 * (1.0 - eta) * (2.0 * xi + eta);
    dN_dxi[1] = 0.25 * (1.0 - eta) * (2.0 * xi - eta);
    dN_dxi[2] = 0.25 * (1.0 + eta) * (2.0 * xi + eta);
    dN_dxi[3] = 0.25 * (1.0 + eta) * (2.0 * xi - eta);
    dN_dxi[4] = -xi * (1.0 - eta);
    dN_dxi[5] = 0.5 * (1.0 - eta * eta);
    dN_dxi[6] = -xi * (1.0 + eta);
    dN_dxi[7] = -0.5 * (1.0 - eta * eta);

    dN_deta[0] = 0.25 * (1.0 - xi) * (xi + 2.0 * eta);
    dN_deta[1] = 0.25 * (1.0 + xi) * (-xi + 2.0 * eta);
    dN_deta[2] = 0.25 * (1.0 + xi) * (xi + 2.0 * eta);
    dN_deta[3] = 0.25 * (1.0 - xi) * (-xi + 2.0 * eta);
    dN_deta[4] = -0.5 * (1.0 - xi * xi);
    dN_deta[5] = -(1.0 + xi) * eta;
    dN_deta[6] = 0.5 * (1.0 - xi * xi);
    dN_deta[7] = -(1.0 - xi) * eta;
}

Eigen::MatrixXd AxisymQ8::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[8], dN_dxi[8], dN_deta[8];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const Q8Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymQ8::B_matrix: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymQ8::B_matrix: singular Jacobian");

    Eigen::MatrixXd B = Eigen::MatrixXd::Zero(4, 16);
    for (int i = 0; i < 8; ++i) {
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

double AxisymQ8::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[8], dN_dxi[8], dN_deta[8];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const Q8Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymQ8::jacobian_weight: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymQ8::jacobian_weight: singular Jacobian");

    return 2.0 * kPi * geo.r * std::abs(geo.detJ) * gp.weight;
}
