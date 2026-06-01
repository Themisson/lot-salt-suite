#pragma once
#include <array>

#include "elements/Element.hpp"

// 2D axisymmetric 9-node quadratic Lagrange quadrilateral in (r,z).
// Node order: Q8 order plus center:
// (-1,-1), (1,-1), (1,1), (-1,1), (0,-1), (1,0), (0,1), (-1,0), (0,0).
class AxisymQ9 : public Element {
public:
    AxisymQ9();

    using Element::shape_derivatives;
    using Element::shape_functions;

    std::span<const GaussPoint> gauss_points() const override;
    void shape_functions(const GaussPoint& gp, std::span<double> N) const override;
    void shape_derivatives(const GaussPoint& gp,
                           std::span<double> dN_dxi,
                           std::span<double> dN_deta) const override;
    Eigen::MatrixXd B_matrix(const GaussPoint& gp,
                             std::span<const Node> node_coords) const override;
    double jacobian_weight(const GaussPoint& gp,
                           std::span<const Node> node_coords) const override;

    int n_nodes() const override { return 9; }
    int n_dofs_per_node() const override { return 2; }
    int n_strain_comp() const override { return 4; }

private:
    static constexpr int kNGauss = 9;
    std::array<GaussPoint, kNGauss> gp_;
};
