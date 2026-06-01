#pragma once
#include "ConstitutiveModel.hpp"

// Elastic-only constitutive model (stub for Etapa 0).
// evaluate() always returns zero viscous rate.
// D_elastic() returns the 4×4 axisymmetric stiffness matrix for an isotropic material.
class ElasticIsotropic : public ConstitutiveModel {
public:
    // E in Pa, nu dimensionless
    explicit ElasticIsotropic(double E, double nu);

    ViscousResult   evaluate(const Stress& sigma,
                             const InternalState& state,
                             double T, double dt) const override;
    Eigen::Matrix4d D_elastic() const override;

private:
    double E_;
    double nu_;
};
