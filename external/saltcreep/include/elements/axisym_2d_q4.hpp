#pragma once
#include <array>

#include "elements/Element.hpp"

// 2D axisymmetric 4-node bilinear quadrilateral in (r,z).
// Node order in reference space: (-1,-1), (1,-1), (1,1), (-1,1).
// DOFs per node: {u_r, u_z}. Voigt order: {epsilon_rr, epsilon_tt, epsilon_zz, gamma_rz}.
class AxisymQ4 : public Element {
public:
    AxisymQ4();

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

    int n_nodes() const override { return 4; }
    int n_dofs_per_node() const override { return 2; }
    int n_strain_comp() const override { return 4; }

private:
    static constexpr int kNGauss = 4;
    std::array<GaussPoint, kNGauss> gp_;
};
