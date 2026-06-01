#pragma once

#include <span>
#include <vector>

#include <Eigen/Core>

#include "elements/Element.hpp"
#include "mesh/Mesh.hpp"
#include "solver/TimeState.hpp"

struct FieldTransferResult {
    Eigen::VectorXd u;
    TimeState state;
};

struct RefinedMesh {
    Mesh2D mesh;
    std::vector<int> parent_element;
    std::vector<int> refinement_level;
};

class MeshRefiner {
public:
    RefinedMesh refine_elements(const Mesh& old_mesh,
                                const Element& element,
                                std::span<const char> marked_elements,
                                std::span<const int> old_levels = {}) const;

    FieldTransferResult interpolate_fields(const Mesh& old_mesh,
                                           const Mesh& new_mesh,
                                           const Element& old_element,
                                           const Element& new_element,
                                           const Eigen::VectorXd& old_u,
                                           const TimeState& old_state,
                                           std::span<const int> parent_element) const;
};
