#include "solver/WallPressureField.hpp"

#include <stdexcept>

namespace {
constexpr double kLbPerGalToKgPerM3 = 119.826;
constexpr double kGravity = 9.80665;
}

ConstantWallPressureField::ConstantWallPressureField(double pressure_Pa)
    : pressure_Pa_(pressure_Pa) {}

double ConstantWallPressureField::pressure_at(const Eigen::Vector2d&, double) const {
    return pressure_Pa_;
}

HydrostaticMudPressureField::HydrostaticMudPressureField(double weight_lb_per_gal,
                                                         double depth_origin_m,
                                                         double surface_pressure_Pa)
    : weight_lb_per_gal_(weight_lb_per_gal)
    , depth_origin_m_(depth_origin_m)
    , surface_pressure_Pa_(surface_pressure_Pa) {
    if (weight_lb_per_gal_ <= 0.0)
        throw std::invalid_argument("HydrostaticMudPressureField: mud weight must be positive");
}

double HydrostaticMudPressureField::pressure_at(const Eigen::Vector2d& x, double) const {
    return surface_pressure_Pa_ + pressure_gradient_Pa_m() * (depth_origin_m_ + x[1]);
}

double HydrostaticMudPressureField::mud_density_kg_m3() const {
    return weight_lb_per_gal_ * kLbPerGalToKgPerM3;
}

double HydrostaticMudPressureField::pressure_gradient_Pa_m() const {
    return mud_density_kg_m3() * kGravity;
}
