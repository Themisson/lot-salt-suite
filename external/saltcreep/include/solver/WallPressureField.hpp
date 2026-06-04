#pragma once

#include <Eigen/Core>
#include <filesystem>
#include <memory>
#include <string>

class TimeDepthTable;

class WallPressureField {
public:
    virtual ~WallPressureField() = default;

    // x = (r,z) in local model coordinates; t is physical time in seconds.
    virtual double pressure_at(const Eigen::Vector2d& x, double t_s) const = 0;
};

class ConstantWallPressureField final : public WallPressureField {
public:
    explicit ConstantWallPressureField(double pressure_Pa);

    double pressure_at(const Eigen::Vector2d& x, double t_s) const override;

private:
    double pressure_Pa_ = 0.0;
};

class HydrostaticMudPressureField final : public WallPressureField {
public:
    HydrostaticMudPressureField(double weight_lb_per_gal,
                                double depth_origin_m,
                                double surface_pressure_Pa = 0.0);

    double pressure_at(const Eigen::Vector2d& x, double t_s) const override;

    double mud_density_kg_m3() const;
    double pressure_gradient_Pa_m() const;

private:
    double weight_lb_per_gal_ = 0.0;
    double depth_origin_m_ = 0.0;
    double surface_pressure_Pa_ = 0.0;
};

class CsvWallPressureField final : public WallPressureField {
public:
    CsvWallPressureField(const std::filesystem::path& csv_path,
                         std::string pressure_column = "p_wall_Pa",
                         std::string time_column = "t_h",
                         std::string z_column = "z_m");

    ~CsvWallPressureField() override;

    double pressure_at(const Eigen::Vector2d& x, double t_s) const override;

private:
    std::unique_ptr<TimeDepthTable> table_;
};
