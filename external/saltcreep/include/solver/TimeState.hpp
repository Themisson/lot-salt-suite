#pragma once

#include <vector>

#include <Eigen/Core>

#include "types.hpp"

// State carried across time steps by explicit and implicit integrators.
struct TimeState {
    Eigen::VectorXd            u_total;       // accumulated nodal displacement [m]
    std::vector<Stress>        sigma_gp;      // stress at each Gauss point [Pa, Voigt]
    std::vector<Strain>        eps_v_gp;      // accumulated viscous strain per GP [Voigt]
    std::vector<Strain>        eps_th_gp;     // accumulated thermal strain per GP [Voigt]
    std::vector<InternalState> state_gp;      // model-specific internal state
};
