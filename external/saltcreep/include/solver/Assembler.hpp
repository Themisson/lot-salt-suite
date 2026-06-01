#pragma once
#include <string>
#include <vector>
#include <Eigen/Sparse>
#include "elements/Element.hpp"
#include "constitutive/ConstitutiveModel.hpp"
#include "mesh/Mesh.hpp"
#include "solver/WallPressureField.hpp"

// Build geometric-progression mesh for AxisymL3.
// Ri: inner radius, Re: outer radius, n_elem: number of elements,
// ratio: length_last / length_first (> 1 → refinement at inner wall when Ri < Re).
Mesh1D build_mesh_L3(double Ri, double Re, int n_elem, double ratio);

// Build structured 2D axisymmetric meshes for Q4/T3/Q8/Q9/T6 elements.
Mesh2D build_mesh_structured_2d(const std::string& element_type,
                                double Ri,
                                double Re,
                                double height,
                                int n_radial,
                                int n_axial,
                                double ratio);

class Assembler {
public:
    // Assemble global stiffness matrix K (n_dof × n_dof, sparse).
    static Eigen::SparseMatrix<double> assemble_K(
        const Mesh& mesh,
        const Element& element,
        const ConstitutiveModel& model);

    // Assemble load vector from Neumann BCs (traction at inner / outer wall).
    // p_inner: traction at r=Ri (Pa, positive = outward radial, i.e. pressure pushing inward)
    // p_outer: traction at r=Re (Pa, positive = inward, i.e. confining pressure)
    // Returns full load vector of size n_nodes.
    static Eigen::VectorXd assemble_neumann(
        const Mesh& mesh,
        double p_inner,
        double p_outer);

    // Assemble pressure traction on the inner/outer cylindrical boundary for
    // generic 2D axisymmetric elements. Positive pressure at Ri pushes inward
    // in the same sign convention as assemble_neumann() for L3.
    static Eigen::VectorXd assemble_boundary_pressure(
        const Mesh& mesh,
        const Element& element,
        double p_inner,
        double p_outer);

    // Assemble pressure with a wall field evaluated at boundary Gauss points.
    // In 1D this reduces to the pressure at z=0. In 2D it supports p_wall(z,t).
    static Eigen::VectorXd assemble_boundary_pressure(
        const Mesh& mesh,
        const Element& element,
        const WallPressureField& inner_pressure,
        double time_s,
        double p_outer = 0.0);

    // Assemble incremental pseudo-force from viscous strain increments:
    //   f_v = Σ_e Σ_gp  Bᵀ · D · Δε^v · jacobian_weight
    // delta_eps_v_gp: flat list, one Strain per (element, gauss_point) in order
    //   index = e * n_gp + g
    static Eigen::VectorXd assemble_pseudo_force(
        const Mesh& mesh,
        const Element& element,
        const ConstitutiveModel& model,
        const std::vector<Strain>& delta_eps_v_gp);

    // Geostatic internal-force vector (SESTSAL: fisg):
    //   f_geo = Σ_e Σ_gp  Bᵀ · σ_geo_gp · jacobian_weight
    //
    // Used to form the net drilling perturbation:
    //   f_net = f_fluid - f_geo   →   K · u = f_net
    //
    // Without this, the elastic solve applies only fluid pressure on a stress-free
    // medium — incorrect BCs and wrong-sign closure.
    //
    // sigma_geo_gp: Voigt stress {σrr,σθθ,σzz,σrz} per GP (index e*n_gp+g).
    static Eigen::VectorXd assemble_geostatic_force(
        const Mesh& mesh,
        const Element& element,
        const std::vector<Stress>& sigma_geo_gp);
};
