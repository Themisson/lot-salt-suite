#include "elements/axisym_2d_q9.hpp"

#include <cmath>
#include <stdexcept>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kDetJTol = 1.0e-12;

struct Q9Geometry {
    double r = 0.0;
    double detJ = 0.0;
    double dr_dxi = 0.0;
    double dr_deta = 0.0;
    double dz_dxi = 0.0;
    double dz_deta = 0.0;
};

void lagrange_1d(double s, double& lm, double& l0, double& lp,
                 double& dlm, double& dl0, double& dlp) {
    lm = 0.5 * s * (s - 1.0);
    l0 = 1.0 - s * s;
    lp = 0.5 * s * (s + 1.0);
    dlm = s - 0.5;
    dl0 = -2.0 * s;
    dlp = s + 0.5;
}

Q9Geometry compute_geometry(const double* N,
                            const double* dN_dxi,
                            const double* dN_deta,
                            std::span<const Node> node_coords) {
    Q9Geometry geo;
    for (int i = 0; i < 9; ++i) {
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

AxisymQ9::AxisymQ9() {
    const double a = std::sqrt(3.0 / 5.0);
    const double pts[3] = {-a, 0.0, a};
    const double w[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};
    int k = 0;
    for (int j = 0; j < 3; ++j) {
        for (int i = 0; i < 3; ++i)
            gp_[k++] = GaussPoint{pts[i], w[i] * w[j], pts[j]};
    }
}

std::span<const GaussPoint> AxisymQ9::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

void AxisymQ9::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    double xm, x0, xp, dxm, dx0, dxp;
    double em, e0, ep, dem, de0, dep;
    lagrange_1d(gp.xi, xm, x0, xp, dxm, dx0, dxp);
    lagrange_1d(gp.eta, em, e0, ep, dem, de0, dep);

    N[0] = xm * em;
    N[1] = xp * em;
    N[2] = xp * ep;
    N[3] = xm * ep;
    N[4] = x0 * em;
    N[5] = xp * e0;
    N[6] = x0 * ep;
    N[7] = xm * e0;
    N[8] = x0 * e0;
}

void AxisymQ9::shape_derivatives(const GaussPoint& gp,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    double xm, x0, xp, dxm, dx0, dxp;
    double em, e0, ep, dem, de0, dep;
    lagrange_1d(gp.xi, xm, x0, xp, dxm, dx0, dxp);
    lagrange_1d(gp.eta, em, e0, ep, dem, de0, dep);

    dN_dxi[0] = dxm * em;
    dN_dxi[1] = dxp * em;
    dN_dxi[2] = dxp * ep;
    dN_dxi[3] = dxm * ep;
    dN_dxi[4] = dx0 * em;
    dN_dxi[5] = dxp * e0;
    dN_dxi[6] = dx0 * ep;
    dN_dxi[7] = dxm * e0;
    dN_dxi[8] = dx0 * e0;

    dN_deta[0] = xm * dem;
    dN_deta[1] = xp * dem;
    dN_deta[2] = xp * dep;
    dN_deta[3] = xm * dep;
    dN_deta[4] = x0 * dem;
    dN_deta[5] = xp * de0;
    dN_deta[6] = x0 * dep;
    dN_deta[7] = xm * de0;
    dN_deta[8] = x0 * de0;
}

Eigen::MatrixXd AxisymQ9::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[9], dN_dxi[9], dN_deta[9];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const Q9Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymQ9::B_matrix: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymQ9::B_matrix: singular Jacobian");

    Eigen::MatrixXd B = Eigen::MatrixXd::Zero(4, 18);
    for (int i = 0; i < 9; ++i) {
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

double AxisymQ9::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[9], dN_dxi[9], dN_deta[9];
    shape_functions(gp, N);
    shape_derivatives(gp, dN_dxi, dN_deta);

    const Q9Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymQ9::jacobian_weight: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymQ9::jacobian_weight: singular Jacobian");

    return 2.0 * kPi * geo.r * std::abs(geo.detJ) * gp.weight;
}
