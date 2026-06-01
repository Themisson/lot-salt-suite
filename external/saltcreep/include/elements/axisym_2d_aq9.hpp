#pragma once
#include <array>
#include <span>

#include <Eigen/Core>

#include "elements/Element.hpp"

// 2D axisymmetric AQ9 element enriched with the Lamé radial basis {1, r, 1/r}.
// Node order matches Q9:
// (-1,-1), (1,-1), (1,1), (-1,1), (0,-1), (1,0), (0,1), (-1,0), (0,0).
class AxisymAQ9 : public Element {
public:
    struct RadialQuadrature {
        std::array<double, 4> xi{};
        std::array<double, 4> weight{};
    };

    AxisymAQ9();

    using Element::shape_derivatives;
    using Element::shape_functions;

    std::span<const GaussPoint> gauss_points() const override;

    void shape_functions(const GaussPoint& gp, std::span<double> N) const override;
    void shape_functions(const GaussPoint& gp,
                         std::span<const Node> node_coords,
                         std::span<double> N) const override;

    void shape_derivatives(const GaussPoint& gp,
                           std::span<double> dN_dxi,
                           std::span<double> dN_deta) const override;
    void shape_derivatives(const GaussPoint& gp,
                           std::span<const Node> node_coords,
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
    static constexpr int kNGauss = 12;
    std::array<GaussPoint, kNGauss> gp_;

    RadialQuadrature radial_quadrature(std::span<const Node> node_coords) const;
};
