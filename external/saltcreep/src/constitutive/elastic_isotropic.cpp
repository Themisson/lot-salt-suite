#include "constitutive/elastic_isotropic.hpp"

ElasticIsotropic::ElasticIsotropic(double E, double nu) : E_(E), nu_(nu) {}

ViscousResult ElasticIsotropic::evaluate(const Stress&,
                                          const InternalState& state,
                                          double, double) const {
    return {Strain::Zero(), state};
}

// Axisymmetric elastic D (4×4), Voigt order {εr, εθ, εz, εrz}.
// Same form as plane-strain D; distinction is in B, not D.
//   C1 = E(1−ν) / [(1+ν)(1−2ν)]
//   C2 = Eν     / [(1+ν)(1−2ν)]
//   C3 = E      / [2(1+ν)]
Eigen::Matrix4d ElasticIsotropic::D_elastic() const {
    const double denom = (1.0 + nu_) * (1.0 - 2.0 * nu_);
    const double C1 = E_ * (1.0 - nu_) / denom;
    const double C2 = E_ * nu_          / denom;
    const double C3 = E_ / (2.0 * (1.0 + nu_));

    Eigen::Matrix4d D = Eigen::Matrix4d::Zero();
    D(0,0) = C1;  D(0,1) = C2;  D(0,2) = C2;
    D(1,0) = C2;  D(1,1) = C1;  D(1,2) = C2;
    D(2,0) = C2;  D(2,1) = C2;  D(2,2) = C1;
    D(3,3) = C3;
    return D;
}
