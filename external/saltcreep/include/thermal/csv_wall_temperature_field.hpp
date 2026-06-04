#pragma once

#include "thermal/ThermalField.hpp"

#include <filesystem>
#include <memory>
#include <string>

class TimeDepthTable;

class CsvWallTemperatureField final : public ThermalField {
public:
    CsvWallTemperatureField(const std::filesystem::path& csv_path,
                            std::string temperature_column = "T_wall_K",
                            std::string time_column = "t_h",
                            std::string z_column = "z_m",
                            double alpha_thermal = 0.0,
                            double T_reference_K = 298.15);

    ~CsvWallTemperatureField() override;

    double temperature_at(const Eigen::Vector2d& x, double t_s) const override;
    double alpha_thermal() const override { return alpha_thermal_; }
    double T_reference() const override { return T_reference_K_; }

private:
    std::unique_ptr<TimeDepthTable> table_;
    double alpha_thermal_ = 0.0;
    double T_reference_K_ = 298.15;
};
