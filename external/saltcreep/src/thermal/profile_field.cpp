#include "thermal/profile_field.hpp"

ProfileField::ProfileField(Mode mode,
                           double constant_T_K,
                           double seabed_T_C,
                           double depth_origin_m,
                           double grad_C_per_m,
                           double alpha_thermal,
                           double T_reference_K)
    : mode_(mode)
    , constant_T_K_(constant_T_K)
    , seabed_T_C_(seabed_T_C)
    , depth_origin_m_(depth_origin_m)
    , grad_C_per_m_(grad_C_per_m)
    , alpha_thermal_(alpha_thermal)
    , T_reference_K_(T_reference_K) {}

ProfileField ProfileField::make_constant(double T_K,
                                          double alpha_thermal,
                                          double T_reference_K) {
    return ProfileField{Mode::Constant, T_K, 0.0, 0.0, 0.0,
                        alpha_thermal, T_reference_K};
}

ProfileField ProfileField::make_profile(double T_seabed_C,
                                        double depth_origin_m,
                                        double grad_C_per_m,
                                        double alpha_thermal,
                                        double T_reference_K) {
    return ProfileField{Mode::Profile, 0.0, T_seabed_C, depth_origin_m,
                        grad_C_per_m, alpha_thermal, T_reference_K};
}

double ProfileField::temperature_at(const Eigen::Vector2d& x, double) const {
    if (mode_ == Mode::Constant)
        return constant_T_K_;

    const double depth_m = depth_origin_m_ + x[1];
    return (seabed_T_C_ + grad_C_per_m_ * depth_m) + 273.15;
}
