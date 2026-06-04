#pragma once

#include <filesystem>
#include <string>
#include <vector>

class TimeDepthTable {
public:
    TimeDepthTable(const std::filesystem::path& csv_path,
                   std::string value_column,
                   std::string time_column = "t_h",
                   std::string z_column = "z_m");

    double value_at(double t_s, double z_m) const;

    const std::vector<double>& times_s() const { return times_s_; }
    const std::vector<double>& depths_m() const { return depths_m_; }

private:
    std::vector<double> times_s_;
    std::vector<double> depths_m_;
    std::vector<double> values_;

    double value_at_index(size_t time_index, size_t depth_index) const;
};
