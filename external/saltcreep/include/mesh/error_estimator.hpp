#pragma once

#include <span>
#include <vector>

#include "constitutive/ConstitutiveModel.hpp"
#include "elements/Element.hpp"
#include "mesh/Mesh.hpp"
#include "solver/TimeState.hpp"

struct ElementError {
    int element_id = -1;
    double eta_abs = 0.0;
    double eta_rel = 0.0;
    double stress_energy = 0.0;
    double damage_indicator = 0.0;
};

struct ErrorEstimatorOptions {
    double error_threshold = 0.10;
    double damage_refinement_threshold = -1.0;
};

class ErrorEstimator {
public:
    std::vector<ElementError> compute_errors(const Mesh& mesh,
                                             const Element& element,
                                             const ConstitutiveModel& model,
                                             const TimeState& state) const;

    std::vector<char> mark_for_refinement(
        std::span<const ElementError> errors,
        const ErrorEstimatorOptions& options) const;
};
