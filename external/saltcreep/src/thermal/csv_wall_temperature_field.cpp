#include "thermal/csv_wall_temperature_field.hpp"

#include "io/TimeDepthTable.hpp"

#include <utility>

CsvWallTemperatureField::CsvWallTemperatureField(const std::filesystem::path& csv_path,
                                                 std::string temperature_column,
                                                 std::string time_column,
                                                 std::string z_column,
                                                 double alpha_thermal,
                                                 double T_reference_K)
    : table_(std::make_unique<TimeDepthTable>(csv_path,
                                              std::move(temperature_column),
                                              std::move(time_column),
                                              std::move(z_column)))
    , alpha_thermal_(alpha_thermal)
    , T_reference_K_(T_reference_K) {}

CsvWallTemperatureField::~CsvWallTemperatureField() = default;

double CsvWallTemperatureField::temperature_at(const Eigen::Vector2d& x, double t_s) const {
    return table_->value_at(t_s, x[1]);
}
