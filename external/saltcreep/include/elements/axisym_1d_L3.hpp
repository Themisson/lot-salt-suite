#pragma once
#include <array>
#include "Element.hpp"

// 1D axisymmetric element: 3-node quadratic Lagrangian along radial direction.
// Nodes at ξ = {−1, 0, +1}, 1 DOF per node (radial displacement u_r).
// B matrix: 4×3, Voigt order {εr, εθ, εz, γrz}; rows εz and γrz are identically zero.
// Integrates with weight 2πr|J|w (full axisymmetric revolution).
class AxisymL3 : public Element {
public:
    AxisymL3();

    using Element::shape_derivatives;
    using Element::shape_functions;

    std::span<const GaussPoint> gauss_points() const override;
    void shape_functions(const GaussPoint& gp, std::span<double> N) const override;
    void shape_derivatives(const GaussPoint& gp,
                           std::span<double> dNdxi,
                           std::span<double> dNdeta) const override;
    Eigen::MatrixXd B_matrix(const GaussPoint& gp,
                             std::span<const Node> node_coords) const override;
    double jacobian_weight(const GaussPoint& gp,
                           std::span<const Node> node_coords) const override;

    // Compatibility overloads for existing 1D tests and analytical checks.
    void shape_functions(double xi, std::span<double> N) const;
    void shape_derivatives(double xi, std::span<double> dNdxi) const;
    Eigen::MatrixXd B_matrix(double xi,
                             std::span<const double> node_r) const;
    double jacobian_weight(double xi,
                           std::span<const double> node_r) const;

    int n_nodes()         const override { return 3; }
    int n_dofs_per_node() const override { return 1; }
    int n_strain_comp()   const override { return 4; }

private:
    static constexpr int kNGauss = 3;
    std::array<GaussPoint, kNGauss> gp_;
};
