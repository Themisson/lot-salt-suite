#pragma once
#include <Eigen/Sparse>
#include <Eigen/SparseCholesky>
#include <vector>

struct SolverResult {
    Eigen::VectorXd u;  // nodal displacements (radial, m)
};

// Thin wrapper: applies essential BCs, factors K once, back-substitutes.
class ElasticSolver {
public:
    // fixed_dofs: list of DOF indices to pin (u=0 Dirichlet BC).
    // Modifies K and f in place (copies taken internally).
    SolverResult solve(Eigen::SparseMatrix<double> K,
                       Eigen::VectorXd             f,
                       const std::vector<int>&     fixed_dofs) const;
};
