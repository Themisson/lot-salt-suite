#pragma once
#include <span>
#include <Eigen/Core>
#include "types.hpp"

class Element {
public:
    virtual ~Element() = default;

    // Gauss points in local coordinates. 1D elements use xi; 2D elements use xi, eta.
    virtual std::span<const GaussPoint> gauss_points() const = 0;

    // Shape functions N_i(xi, eta), size = n_nodes().
    virtual void shape_functions(const GaussPoint& gp, std::span<double> N) const = 0;

    // Geometry-aware overload for elements whose basis depends on physical coordinates
    // (for example, AQ9 with Lamé enrichment). Existing elements use the local-only form.
    virtual void shape_functions(const GaussPoint& gp,
                                 std::span<const Node> node_coords,
                                 std::span<double> N) const {
        (void)node_coords;
        shape_functions(gp, N);
    }

    // Shape function derivatives in local coordinates, each size = n_nodes().
    // 1D elements write dN_dxi and may leave dN_deta as zero.
    virtual void shape_derivatives(const GaussPoint& gp,
                                   std::span<double> dN_dxi,
                                   std::span<double> dN_deta) const = 0;

    virtual void shape_derivatives(const GaussPoint& gp,
                                   std::span<const Node> node_coords,
                                   std::span<double> dN_dxi,
                                   std::span<double> dN_deta) const {
        (void)node_coords;
        shape_derivatives(gp, dN_dxi, dN_deta);
    }

    // B matrix: n_strain_comp() × (n_nodes() * n_dofs_per_node())
    // Axisymmetric Voigt order is {εr, εθ, εz, γrz}.
    virtual Eigen::MatrixXd B_matrix(const GaussPoint& gp,
                                     std::span<const Node> node_coords) const = 0;

    // Integration weight at this Gauss point, INCLUDING 2πr and |J|.
    // For 1D: 2π * r(xi) * |J| * w_GP.
    // For 2D: 2π * r(xi,eta) * |detJ| * w_GP.
    virtual double jacobian_weight(const GaussPoint& gp,
                                   std::span<const Node> node_coords) const = 0;

    virtual int n_nodes()         const = 0;
    virtual int n_dofs_per_node() const = 0;
    virtual int n_strain_comp()   const = 0;  // 4 for axisymmetric
};
