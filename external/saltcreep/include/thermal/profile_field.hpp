#pragma once
#include "ThermalField.hpp"

// Two-mode thermal field for Etapas 0–5a (no conduction PDE yet).
//
// mode = Constant: returns T_K everywhere (Etapa 0 stub, unit tests).
// mode = Profile:  T(z) = T_seabed_C + grad_C_per_m * (depth_origin_m + z) + 273.15 K.
//                  For 1D radial cases z=0, preserving the old constant-at-depth
//                  behaviour. For 2D cases the profile varies with vertical coordinate z.
//
// alpha_thermal remains 0 unless explicitly enabled in YAML; thermal strain is
// consumed by the mechanical loop only in Etapa 5c.
class ProfileField : public ThermalField {
public:
    // Constant mode — behaviour preserved from Etapa 0
    static ProfileField make_constant(double T_K,
                                      double alpha_thermal = 0.0,
                                      double T_reference_K = 298.15);

    // Profile mode — single-gradient analytical T(depth)
    // T [K] = (T_seabed_C + grad_C_per_m * (depth_origin_m + z)) + 273.15
    static ProfileField make_profile(double T_seabed_C,
                                     double depth_origin_m,
                                     double grad_C_per_m,
                                     double alpha_thermal = 0.0,
                                     double T_reference_K = 298.15);

    double temperature_at(const Eigen::Vector2d& x, double t) const override;
    double alpha_thermal() const override { return alpha_thermal_; }
    double T_reference()   const override { return T_reference_K_; }

private:
    enum class Mode { Constant, Profile };

    Mode mode_ = Mode::Constant;
    double constant_T_K_ = 298.15;
    double seabed_T_C_ = 4.0;
    double depth_origin_m_ = 0.0;
    double grad_C_per_m_ = 0.0;
    double alpha_thermal_ = 0.0;
    double T_reference_K_ = 298.15;

    ProfileField(Mode mode,
                 double constant_T_K,
                 double seabed_T_C,
                 double depth_origin_m,
                 double grad_C_per_m,
                 double alpha_thermal,
                 double T_reference_K);
};
