#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <chrono>
#include <filesystem>
#include <fstream>
#include <stdexcept>
#include <string>

#include "io/CaseParser.hpp"
#include "io/TimeDepthTable.hpp"
#include "solver/WallPressureField.hpp"
#include "thermal/csv_wall_temperature_field.hpp"

namespace {

std::filesystem::path find_data_dir() {
    for (const auto& candidate : {
             std::filesystem::path("data"),
             std::filesystem::path("../data"),
             std::filesystem::path("../../data")}) {
        if (std::filesystem::exists(candidate / "litologias"))
            return candidate;
    }
    throw std::runtime_error("Cannot find data/litologias");
}

std::filesystem::path unique_temp_dir(const std::string& stem) {
    const auto ticks = std::chrono::high_resolution_clock::now()
        .time_since_epoch().count();
    const auto base = std::filesystem::temp_directory_path() /
        (stem + "_" + std::to_string(ticks));
    std::filesystem::create_directories(base);
    return base;
}

void write_schedule_csv(const std::filesystem::path& path) {
    std::ofstream csv(path);
    csv << "t_h,z_m,p_wall_Pa,T_wall_K\n";
    csv << "0,0,100,300\n";
    csv << "0,100,200,320\n";
    csv << "2,0,300,340\n";
    csv << "2,100,500,380\n";
}

} // namespace

TEST_CASE("TimeDepthTable interpolates linearly in time and depth",
          "[csv][pressure][thermal]") {
    const auto dir = unique_temp_dir("saltcreep_csv_table");
    const auto csv_path = dir / "schedule.csv";
    write_schedule_csv(csv_path);

    TimeDepthTable pressure(csv_path, "p_wall_Pa", "t_h", "z_m");

    REQUIRE(pressure.value_at(0.0, 0.0) == Catch::Approx(100.0));
    REQUIRE(pressure.value_at(2.0 * 3600.0, 100.0) == Catch::Approx(500.0));
    REQUIRE(pressure.value_at(1.0 * 3600.0, 50.0) == Catch::Approx(275.0));
    REQUIRE(pressure.value_at(-10.0, -1.0) == Catch::Approx(100.0));
    REQUIRE(pressure.value_at(10.0 * 3600.0, 150.0) == Catch::Approx(500.0));

    std::filesystem::remove_all(dir);
}

TEST_CASE("CSV wall pressure and temperature fields evaluate operational schedules",
          "[csv][pressure][thermal]") {
    const auto dir = unique_temp_dir("saltcreep_csv_fields");
    const auto csv_path = dir / "schedule.csv";
    write_schedule_csv(csv_path);

    CsvWallPressureField pressure(csv_path);
    CsvWallTemperatureField temperature(csv_path, "T_wall_K", "t_h", "z_m", 1.0e-5, 300.0);

    const Eigen::Vector2d x{0.155575, 50.0};
    REQUIRE(pressure.pressure_at(x, 1.0 * 3600.0) == Catch::Approx(275.0));
    REQUIRE(temperature.temperature_at(x, 1.0 * 3600.0) == Catch::Approx(335.0));
    REQUIRE(temperature.alpha_thermal() == Catch::Approx(1.0e-5));
    REQUIRE(temperature.T_reference() == Catch::Approx(300.0));

    std::filesystem::remove_all(dir);
}

TEST_CASE("CaseParser accepts CSV pressure and wall-temperature modes",
          "[csv][parser]") {
    const auto dir = unique_temp_dir("saltcreep_csv_parser");
    const auto csv_path = dir / "schedule.csv";
    const auto yaml_path = dir / "case.yaml";
    write_schedule_csv(csv_path);

    std::ofstream yaml(yaml_path);
    yaml
        << "name: csv_parser_case\n"
        << "geometry:\n"
        << "  well_radius_m: 0.155575\n"
        << "  outer_radius_factor: 100\n"
        << "mesh:\n"
        << "  n_elements_radial: 2\n"
        << "  ratio: 10\n"
        << "element:\n"
        << "  type: axisym_1d_L3\n"
        << "depths:\n"
        << "  burial_m: 2500\n"
        << "  water_depth_m: 1600\n"
        << "fluid:\n"
        << "  mode: csv_time_depth_profile\n"
        << "  csv: schedule.csv\n"
        << "thermal:\n"
        << "  enabled: true\n"
        << "  mode: csv_wall_temperature\n"
        << "  csv: schedule.csv\n"
        << "  alpha_thermal: 1.0e-5\n"
        << "  T_reference_C: 25\n"
        << "time:\n"
        << "  total_h: 2\n"
        << "  dt_h: 1\n"
        << "creep:\n"
        << "  elastic_only: false\n"
        << "  secondary: false\n";
    yaml.close();

    const CaseData cd = parse_case(yaml_path, find_data_dir());
    REQUIRE(cd.fluid.mode == "csv_time_depth_profile");
    REQUIRE(std::filesystem::path(cd.fluid.csv_path) == csv_path);
    REQUIRE(cd.thermal.mode == "csv_wall_temperature");
    REQUIRE(std::filesystem::path(cd.thermal.csv_path) == csv_path);
    REQUIRE(cd.thermal.T_reference_K == Catch::Approx(298.15));

    std::filesystem::remove_all(dir);
}
