#pragma once
#include <Eigen/Core>

class ThermalField {
public:
    virtual ~ThermalField() = default;

    // Temperature (K) at physical point x = {r, z} and time t (s).
    // Weak coupling: T does not depend on mechanical state.
    virtual double temperature_at(const Eigen::Vector2d& x, double t) const = 0;

    // Linear thermal expansion coefficient (1/K) for ε^th = α(T − T_ref)
    virtual double alpha_thermal() const = 0;

    // Reference temperature (K) for thermal strain calculation
    virtual double T_reference() const = 0;
};
