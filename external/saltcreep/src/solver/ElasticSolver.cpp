#include "solver/ElasticSolver.hpp"
#include <stdexcept>

SolverResult ElasticSolver::solve(Eigen::SparseMatrix<double> K,
                                   Eigen::VectorXd             f,
                                   const std::vector<int>&     fixed_dofs) const {
    // Apply Dirichlet BCs by row/column elimination (large-number penalty is avoided
    // because it can ill-condition K for SimplicialLDLT).
    // Strategy: zero the row and column of each fixed DOF, set diagonal to 1, rhs to 0.
    K.makeCompressed();
    for (int dof : fixed_dofs) {
        // Zero the row
        for (Eigen::SparseMatrix<double>::InnerIterator it(K, dof); it; ++it)
            it.valueRef() = 0.0;
        // Zero the column (K is symmetric — iterate over all rows)
        for (int j = 0; j < K.outerSize(); ++j) {
            for (Eigen::SparseMatrix<double>::InnerIterator it(K, j); it; ++it) {
                if (it.row() == dof) it.valueRef() = 0.0;
            }
        }
        // Diagonal = 1, rhs = 0
        K.coeffRef(dof, dof) = 1.0;
        f[dof] = 0.0;
    }
    K.makeCompressed();

    Eigen::SimplicialLDLT<Eigen::SparseMatrix<double>> solver;
    solver.compute(K);
    if (solver.info() != Eigen::Success)
        throw std::runtime_error("ElasticSolver: factorization failed");

    Eigen::VectorXd u = solver.solve(f);
    if (solver.info() != Eigen::Success)
        throw std::runtime_error("ElasticSolver: solve failed");

    return {u};
}
