#include "mesh/error_estimator.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

#include <Eigen/LU>

namespace {
std::vector<Node> element_coords(const Mesh& mesh, int element_id, int nne) {
    std::vector<Node> coords(nne);
    for (int i = 0; i < nne; ++i)
        coords[i] = mesh.nodes[mesh.elem_nodes[nne * element_id + i]];
    return coords;
}

double quadratic_energy(const Stress& sigma,
                        const Eigen::Matrix4d& compliance) {
    return std::max(0.0, sigma.dot(compliance * sigma));
}
} // namespace

std::vector<ElementError>
ErrorEstimator::compute_errors(const Mesh& mesh,
                               const Element& element,
                               const ConstitutiveModel& model,
                               const TimeState& state) const {
    const int n_gp = static_cast<int>(element.gauss_points().size());
    const int nne = element.n_nodes();
    const int total_gp = mesh.n_elements * n_gp;
    if (static_cast<int>(state.sigma_gp.size()) != total_gp)
        throw std::invalid_argument("ErrorEstimator: sigma_gp size does not match mesh");

    std::vector<Stress> sigma_node(mesh.n_nodes, Stress::Zero());
    std::vector<double> weight_node(mesh.n_nodes, 0.0);

    for (int e = 0; e < mesh.n_elements; ++e) {
        const auto coords = element_coords(mesh, e, nne);
        for (int g = 0; g < n_gp; ++g) {
            const auto& gp = element.gauss_points()[g];
            const double jw = std::abs(element.jacobian_weight(gp, coords));
            std::vector<double> N(nne);
            element.shape_functions(gp, coords, N);
            const Stress& sigma = state.sigma_gp[e * n_gp + g];
            for (int i = 0; i < nne; ++i) {
                const int node = mesh.elem_nodes[nne * e + i];
                const double w = std::abs(N[i]) * jw;
                sigma_node[node] += w * sigma;
                weight_node[node] += w;
            }
        }
    }

    for (int n = 0; n < mesh.n_nodes; ++n) {
        if (weight_node[n] > 0.0)
            sigma_node[n] /= weight_node[n];
    }

    const Eigen::Matrix4d compliance = model.D_elastic().inverse();
    std::vector<ElementError> errors(mesh.n_elements);
    constexpr double eps = 1.0e-30;

    for (int e = 0; e < mesh.n_elements; ++e) {
        const auto coords = element_coords(mesh, e, nne);
        double eta2 = 0.0;
        double energy = 0.0;
        double max_D = 0.0;

        for (int g = 0; g < n_gp; ++g) {
            const auto& gp = element.gauss_points()[g];
            const double jw = std::abs(element.jacobian_weight(gp, coords));
            std::vector<double> N(nne);
            element.shape_functions(gp, coords, N);

            Stress recovered = Stress::Zero();
            for (int i = 0; i < nne; ++i) {
                const int node = mesh.elem_nodes[nne * e + i];
                recovered += N[i] * sigma_node[node];
            }

            const int idx = e * n_gp + g;
            const Stress diff = state.sigma_gp[idx] - recovered;
            eta2 += quadratic_energy(diff, compliance) * jw;
            energy += quadratic_energy(state.sigma_gp[idx], compliance) * jw;
            if (idx < static_cast<int>(state.state_gp.size()))
                max_D = std::max(max_D, state.state_gp[idx].damage_D);
        }

        errors[e].element_id = e;
        errors[e].eta_abs = std::sqrt(std::max(0.0, eta2));
        errors[e].stress_energy = std::max(0.0, energy);
        errors[e].eta_rel = errors[e].eta_abs / std::sqrt(std::max(energy, eps));
        errors[e].damage_indicator = max_D;
    }

    return errors;
}

std::vector<char>
ErrorEstimator::mark_for_refinement(std::span<const ElementError> errors,
                                    const ErrorEstimatorOptions& options) const {
    if (options.error_threshold < 0.0)
        throw std::invalid_argument("ErrorEstimator: error_threshold must be non-negative");

    std::vector<char> marked(errors.size(), 0);
    for (size_t i = 0; i < errors.size(); ++i) {
        const bool by_error = errors[i].eta_rel > options.error_threshold;
        const bool by_damage = options.damage_refinement_threshold >= 0.0 &&
                               errors[i].damage_indicator >
                                   options.damage_refinement_threshold;
        marked[i] = (by_error || by_damage) ? 1 : 0;
    }
    return marked;
}
