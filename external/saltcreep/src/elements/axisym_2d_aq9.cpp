#include "elements/axisym_2d_aq9.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <stdexcept>
#include <unordered_map>

#include <Eigen/LU>

namespace {
constexpr double kPi = 3.14159265358979323846;
constexpr double kDetJTol = 1.0e-12;
constexpr double kCoordTol = 1.0e-10;
constexpr double kSentinelBase = -100.0;

struct AQ9Geometry {
    double r = 0.0;
    double detJ = 0.0;
    double dr_dxi = 0.0;
    double dr_deta = 0.0;
    double dz_dxi = 0.0;
    double dz_deta = 0.0;
};

struct RadialBounds {
    double rL = 0.0;
    double rM = 0.0;
    double rR = 0.0;
};

struct RadialCoefficients {
    double c[3][3]{};
};

void eta_basis(double eta, double& eb, double& em, double& et,
               double& deb, double& dem, double& det) {
    eb = 0.5 * eta * (eta - 1.0);
    em = 1.0 - eta * eta;
    et = 0.5 * eta * (eta + 1.0);
    deb = eta - 0.5;
    dem = -2.0 * eta;
    det = eta + 0.5;
}

RadialBounds radial_bounds(std::span<const Node> node_coords) {
    if (node_coords.size() != 9)
        throw std::invalid_argument("AxisymAQ9: expected 9 node coordinates");

    auto [min_it, max_it] = std::minmax_element(
        node_coords.begin(), node_coords.end(),
        [](const Node& a, const Node& b) { return a.r < b.r; });
    RadialBounds b;
    b.rL = min_it->r;
    b.rR = max_it->r;
    b.rM = 0.5 * (b.rL + b.rR);

    if (b.rL <= 0.0 || b.rR <= b.rL)
        throw std::domain_error("AxisymAQ9: invalid radial bounds");

    const double tol = kCoordTol * std::max(1.0, std::abs(b.rR));
    const int left_nodes[] = {0, 3, 7};
    const int right_nodes[] = {1, 2, 5};
    const int mid_nodes[] = {4, 6, 8};
    for (int i : left_nodes)
        if (std::abs(node_coords[i].r - b.rL) > tol)
            throw std::domain_error("AxisymAQ9: non-rectangular left radial edge");
    for (int i : right_nodes)
        if (std::abs(node_coords[i].r - b.rR) > tol)
            throw std::domain_error("AxisymAQ9: non-rectangular right radial edge");
    for (int i : mid_nodes)
        if (std::abs(node_coords[i].r - b.rM) > tol)
            throw std::domain_error("AxisymAQ9: radial mid-node is not centered");
    return b;
}

long long radial_key(const RadialBounds& b) {
    const long long kL = static_cast<long long>(std::llround(b.rL * 1.0e9));
    const long long kR = static_cast<long long>(std::llround(b.rR * 1.0e9));
    return kL ^ (kR + 0x9e3779b97f4a7c15LL + (kL << 6) + (kL >> 2));
}

Eigen::Matrix3d radial_interpolation_matrix(const RadialBounds& b) {
    Eigen::Matrix3d A;
    A << 1.0, b.rL, 1.0 / b.rL,
         1.0, b.rM, 1.0 / b.rM,
         1.0, b.rR, 1.0 / b.rR;
    return A;
}

RadialCoefficients radial_coefficients(const RadialBounds& b) {
    static thread_local std::unordered_map<long long, RadialCoefficients> cache;
    const long long key = radial_key(b);
    const auto it = cache.find(key);
    if (it != cache.end())
        return it->second;

    const Eigen::Matrix3d C = radial_interpolation_matrix(b).inverse();
    RadialCoefficients coeffs;
    for (int a = 0; a < 3; ++a)
        for (int j = 0; j < 3; ++j)
            coeffs.c[a][j] = C(j, a);
    cache.emplace(key, coeffs);
    return coeffs;
}

void radial_basis(const RadialBounds& b, double xi,
                  double R[3], double dR_dxi[3]) {
    const double dr_dxi = b.rR - b.rL;
    const double r = b.rL + (xi - 1.0) * dr_dxi;
    if (r <= 0.0)
        throw std::domain_error("AxisymAQ9: r <= 0 in radial basis");

    const RadialCoefficients coeffs = radial_coefficients(b);
    const double p[3] = {1.0, r, 1.0 / r};
    const double dp_dxi[3] = {0.0, dr_dxi, -dr_dxi / (r * r)};

    for (int a = 0; a < 3; ++a) {
        R[a] = p[0] * coeffs.c[a][0] + p[1] * coeffs.c[a][1] + p[2] * coeffs.c[a][2];
        dR_dxi[a] = dp_dxi[0] * coeffs.c[a][0] +
                    dp_dxi[1] * coeffs.c[a][1] +
                    dp_dxi[2] * coeffs.c[a][2];
    }
}

int radial_index_from_sentinel(double xi) {
    if (xi > kSentinelBase + 1.0)
        return -1;
    const int idx = static_cast<int>(std::llround(-(xi - kSentinelBase)));
    return (0 <= idx && idx < 4) ? idx : -1;
}

double local_xi_to_legacy(double xi) {
    if (xi >= -1.0 - 1.0e-12 && xi <= 1.0 + 1.0e-12)
        return 1.5 + 0.5 * xi;
    if (xi >= 1.0 - 1.0e-12 && xi <= 2.0 + 1.0e-12)
        return xi;
    std::ostringstream oss;
    oss << "AxisymAQ9: local xi outside supported ranges: " << xi;
    throw std::domain_error(oss.str());
}

AQ9Geometry compute_geometry(const double* N,
                             const double* dN_dxi,
                             const double* dN_deta,
                             std::span<const Node> node_coords) {
    AQ9Geometry geo;
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

double moment_polynomial(int m) {
    return (std::pow(2.0, m + 1) - 1.0) / static_cast<double>(m + 1);
}

double moment_reciprocal(double ct, int k) {
    if (k == 1)
        return std::log((2.0 - ct) / (1.0 - ct));
    if (k == 2)
        return 1.0 / (1.0 - ct) - 1.0 / (2.0 - ct);
    return 0.5 * (1.0 / ((1.0 - ct) * (1.0 - ct)) -
                  1.0 / ((2.0 - ct) * (2.0 - ct)));
}

AxisymAQ9::RadialQuadrature solve_special_radial_quadrature(double ct) {
    Eigen::Matrix<double, 7, 1> y;
    y << 1.20, 1.50, 1.85, 0.08, 0.30, 0.40, 0.22;

    auto valid_trial = [](const Eigen::Matrix<double, 7, 1>& v) {
        return v[0] > 1.0 && v[0] < v[1] &&
               v[1] < v[2] && v[2] < 2.0 &&
               v[3] > 0.0 && v[4] > 0.0 && v[5] > 0.0 && v[6] > 0.0;
    };

    bool converged = false;
    for (int iter = 0; iter < 80; ++iter) {
        const double x[4] = {1.0, y[0], y[1], y[2]};
        const double w[4] = {y[3], y[4], y[5], y[6]};

        Eigen::Matrix<double, 7, 1> residual;
        for (int m = 0; m < 4; ++m) {
            double value = 0.0;
            for (int i = 0; i < 4; ++i)
                value += w[i] * std::pow(x[i], m);
            residual[m] = value - moment_polynomial(m);
        }
        for (int k = 1; k <= 3; ++k) {
            double value = 0.0;
            for (int i = 0; i < 4; ++i)
                value += w[i] / std::pow(x[i] - ct, k);
            residual[3 + k] = value - moment_reciprocal(ct, k);
        }

        if (residual.lpNorm<Eigen::Infinity>() < 1.0e-13) {
            converged = true;
            break;
        }

        Eigen::Matrix<double, 7, 7> J = Eigen::Matrix<double, 7, 7>::Zero();
        for (int m = 0; m < 4; ++m) {
            for (int j = 1; j < 4; ++j)
                J(m, j - 1) = (m == 0) ? 0.0 : w[j] * m * std::pow(x[j], m - 1);
            for (int j = 0; j < 4; ++j)
                J(m, 3 + j) = std::pow(x[j], m);
        }
        for (int k = 1; k <= 3; ++k) {
            const int row = 3 + k;
            for (int j = 1; j < 4; ++j)
                J(row, j - 1) = -k * w[j] / std::pow(x[j] - ct, k + 1);
            for (int j = 0; j < 4; ++j)
                J(row, 3 + j) = 1.0 / std::pow(x[j] - ct, k);
        }

        const Eigen::Matrix<double, 7, 1> delta =
            J.fullPivLu().solve(-residual);
        if (!delta.allFinite())
            throw std::runtime_error("AxisymAQ9: radial quadrature Newton failed");

        double alpha = 1.0;
        bool accepted = false;
        for (int ls = 0; ls < 30; ++ls) {
            const auto trial = y + alpha * delta;
            if (valid_trial(trial)) {
                y = trial;
                accepted = true;
                break;
            }
            alpha *= 0.5;
        }
        if (!accepted)
            throw std::runtime_error("AxisymAQ9: radial quadrature left positive domain");
    }

    if (!converged)
        throw std::runtime_error("AxisymAQ9: radial quadrature Newton did not converge");

    AxisymAQ9::RadialQuadrature q;
    q.xi = {1.0, y[0], y[1], y[2]};
    q.weight = {y[3], y[4], y[5], y[6]};

    for (double weight : q.weight) {
        if (!(weight > 0.0)) {
            std::ostringstream oss;
            oss << "AxisymAQ9: negative radial quadrature weight for ct=" << ct;
            throw std::runtime_error(oss.str());
        }
    }
    return q;
}
} // namespace

AxisymAQ9::AxisymAQ9() {
    const double a = std::sqrt(3.0 / 5.0);
    const double eta[3] = {-a, 0.0, a};
    const double w_eta[3] = {5.0 / 9.0, 8.0 / 9.0, 5.0 / 9.0};
    int k = 0;
    for (int j = 0; j < 3; ++j) {
        for (int i = 0; i < 4; ++i)
            gp_[k++] = GaussPoint{kSentinelBase - static_cast<double>(i), w_eta[j], eta[j]};
    }
}

std::span<const GaussPoint> AxisymAQ9::gauss_points() const {
    return {gp_.data(), gp_.size()};
}

void AxisymAQ9::shape_functions(const GaussPoint& gp, std::span<double> N) const {
    const std::array<Node, 9> canonical = {
        Node{1.0, 0.0}, Node{2.0, 0.0}, Node{2.0, 1.0}, Node{1.0, 1.0},
        Node{1.5, 0.0}, Node{2.0, 0.5}, Node{1.5, 1.0}, Node{1.0, 0.5},
        Node{1.5, 0.5}
    };
    shape_functions(gp, canonical, N);
}

void AxisymAQ9::shape_functions(const GaussPoint& gp,
                                std::span<const Node> node_coords,
                                std::span<double> N) const {
    const int idx = radial_index_from_sentinel(gp.xi);
    const double xi = (idx >= 0) ? radial_quadrature(node_coords).xi[idx]
                                 : local_xi_to_legacy(gp.xi);

    const RadialBounds b = radial_bounds(node_coords);
    double R[3], dR_dxi[3];
    radial_basis(b, xi, R, dR_dxi);

    double eb, em, et, deb, dem, det;
    eta_basis(gp.eta, eb, em, et, deb, dem, det);

    N[0] = R[0] * eb;
    N[1] = R[2] * eb;
    N[2] = R[2] * et;
    N[3] = R[0] * et;
    N[4] = R[1] * eb;
    N[5] = R[2] * em;
    N[6] = R[1] * et;
    N[7] = R[0] * em;
    N[8] = R[1] * em;
}

void AxisymAQ9::shape_derivatives(const GaussPoint& gp,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    const std::array<Node, 9> canonical = {
        Node{1.0, 0.0}, Node{2.0, 0.0}, Node{2.0, 1.0}, Node{1.0, 1.0},
        Node{1.5, 0.0}, Node{2.0, 0.5}, Node{1.5, 1.0}, Node{1.0, 0.5},
        Node{1.5, 0.5}
    };
    shape_derivatives(gp, canonical, dN_dxi, dN_deta);
}

void AxisymAQ9::shape_derivatives(const GaussPoint& gp,
                                  std::span<const Node> node_coords,
                                  std::span<double> dN_dxi,
                                  std::span<double> dN_deta) const {
    const int idx = radial_index_from_sentinel(gp.xi);
    const double xi = (idx >= 0) ? radial_quadrature(node_coords).xi[idx]
                                 : local_xi_to_legacy(gp.xi);

    const RadialBounds b = radial_bounds(node_coords);
    double R[3], dR_dxi_values[3];
    radial_basis(b, xi, R, dR_dxi_values);

    double eb, em, et, deb, dem, det;
    eta_basis(gp.eta, eb, em, et, deb, dem, det);

    dN_dxi[0] = dR_dxi_values[0] * eb;
    dN_dxi[1] = dR_dxi_values[2] * eb;
    dN_dxi[2] = dR_dxi_values[2] * et;
    dN_dxi[3] = dR_dxi_values[0] * et;
    dN_dxi[4] = dR_dxi_values[1] * eb;
    dN_dxi[5] = dR_dxi_values[2] * em;
    dN_dxi[6] = dR_dxi_values[1] * et;
    dN_dxi[7] = dR_dxi_values[0] * em;
    dN_dxi[8] = dR_dxi_values[1] * em;

    dN_deta[0] = R[0] * deb;
    dN_deta[1] = R[2] * deb;
    dN_deta[2] = R[2] * det;
    dN_deta[3] = R[0] * det;
    dN_deta[4] = R[1] * deb;
    dN_deta[5] = R[2] * dem;
    dN_deta[6] = R[1] * det;
    dN_deta[7] = R[0] * dem;
    dN_deta[8] = R[1] * dem;
}

Eigen::MatrixXd AxisymAQ9::B_matrix(const GaussPoint& gp,
                                    std::span<const Node> node_coords) const {
    double N[9], dN_dxi[9], dN_deta[9];
    shape_functions(gp, node_coords, N);
    shape_derivatives(gp, node_coords, dN_dxi, dN_deta);

    const AQ9Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymAQ9::B_matrix: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymAQ9::B_matrix: singular Jacobian");

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

double AxisymAQ9::jacobian_weight(const GaussPoint& gp,
                                  std::span<const Node> node_coords) const {
    double N[9], dN_dxi[9], dN_deta[9];
    shape_functions(gp, node_coords, N);
    shape_derivatives(gp, node_coords, dN_dxi, dN_deta);

    const AQ9Geometry geo = compute_geometry(N, dN_dxi, dN_deta, node_coords);
    if (geo.r <= 0.0)
        throw std::domain_error("AxisymAQ9::jacobian_weight: r <= 0 at Gauss point");
    if (std::abs(geo.detJ) < kDetJTol)
        throw std::domain_error("AxisymAQ9::jacobian_weight: singular Jacobian");

    const int idx = radial_index_from_sentinel(gp.xi);
    const double radial_weight = (idx >= 0) ? radial_quadrature(node_coords).weight[idx] : gp.weight;
    const double eta_weight = (idx >= 0) ? gp.weight : 1.0;
    return 2.0 * kPi * geo.r * std::abs(geo.detJ) * radial_weight * eta_weight;
}

AxisymAQ9::RadialQuadrature AxisymAQ9::radial_quadrature(
    std::span<const Node> node_coords) const {
    const RadialBounds b = radial_bounds(node_coords);
    const double ct = 1.0 - b.rL / (b.rR - b.rL);
    const long long key = static_cast<long long>(std::llround(ct * 1.0e12));

    static thread_local std::unordered_map<long long, RadialQuadrature> cache;
    const auto it = cache.find(key);
    if (it != cache.end())
        return it->second;

    RadialQuadrature q = solve_special_radial_quadrature(ct);
    cache.emplace(key, q);
    return q;
}
