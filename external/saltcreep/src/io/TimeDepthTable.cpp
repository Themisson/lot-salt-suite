#include "io/TimeDepthTable.hpp"

#include <algorithm>
#include <cctype>
#include <cmath>
#include <fstream>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <utility>

namespace {

constexpr double kSecondsPerHour = 3600.0;

std::string trim(std::string value) {
    auto not_space = [](unsigned char c) { return !std::isspace(c); };
    value.erase(value.begin(), std::find_if(value.begin(), value.end(), not_space));
    value.erase(std::find_if(value.rbegin(), value.rend(), not_space).base(), value.end());
    return value;
}

std::vector<std::string> split_csv_line(const std::string& line) {
    std::vector<std::string> cells;
    std::stringstream ss(line);
    std::string cell;
    while (std::getline(ss, cell, ','))
        cells.push_back(trim(cell));
    return cells;
}

int column_index(const std::unordered_map<std::string, int>& header,
                 const std::string& column,
                 const std::filesystem::path& csv_path) {
    const auto it = header.find(column);
    if (it == header.end())
        throw std::runtime_error("CSV " + csv_path.string() + " missing column: " + column);
    return it->second;
}

double parse_double(const std::string& text,
                    const std::filesystem::path& csv_path,
                    int line_number,
                    const std::string& column) {
    try {
        size_t pos = 0;
        const double value = std::stod(text, &pos);
        if (pos != text.size())
            throw std::invalid_argument("trailing text");
        return value;
    } catch (const std::exception&) {
        throw std::runtime_error("CSV " + csv_path.string() + " line " +
                                 std::to_string(line_number) +
                                 " has invalid numeric value in column " + column);
    }
}

double to_seconds(double time_value, const std::string& time_column) {
    if (time_column == "t_s" || time_column == "time_s")
        return time_value;
    if (time_column == "t_h" || time_column == "time_h")
        return time_value * kSecondsPerHour;
    return time_value * kSecondsPerHour;
}

std::vector<double> sorted_unique(std::vector<double> values) {
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end(), [](double a, double b) {
        return std::abs(a - b) <= 1.0e-9 * std::max(1.0, std::max(std::abs(a), std::abs(b)));
    }), values.end());
    return values;
}

size_t nearest_index(const std::vector<double>& values, double target) {
    auto it = std::lower_bound(values.begin(), values.end(), target);
    if (it == values.end())
        return values.size() - 1;
    if (it == values.begin())
        return 0;
    const size_t hi = static_cast<size_t>(it - values.begin());
    const size_t lo = hi - 1;
    return (std::abs(values[hi] - target) < std::abs(target - values[lo])) ? hi : lo;
}

std::pair<size_t, size_t> bracket(const std::vector<double>& values, double target) {
    if (values.size() == 1)
        return {0, 0};
    if (target <= values.front())
        return {0, 0};
    if (target >= values.back())
        return {values.size() - 1, values.size() - 1};
    auto hi_it = std::upper_bound(values.begin(), values.end(), target);
    const size_t hi = static_cast<size_t>(hi_it - values.begin());
    return {hi - 1, hi};
}

double linear_weight(double lo, double hi, double x) {
    if (std::abs(hi - lo) <= std::numeric_limits<double>::epsilon() * std::max(1.0, std::abs(hi)))
        return 0.0;
    return (x - lo) / (hi - lo);
}

} // namespace

TimeDepthTable::TimeDepthTable(const std::filesystem::path& csv_path,
                               std::string value_column,
                               std::string time_column,
                               std::string z_column) {
    std::ifstream csv(csv_path);
    if (!csv)
        throw std::runtime_error("Cannot open CSV file: " + csv_path.string());

    std::string line;
    if (!std::getline(csv, line))
        throw std::runtime_error("CSV file is empty: " + csv_path.string());

    const auto header_cells = split_csv_line(line);
    std::unordered_map<std::string, int> header;
    for (int i = 0; i < static_cast<int>(header_cells.size()); ++i)
        header[header_cells[static_cast<size_t>(i)]] = i;

    const int time_idx = column_index(header, time_column, csv_path);
    const int z_idx = column_index(header, z_column, csv_path);
    const int value_idx = column_index(header, value_column, csv_path);

    struct Row { double t_s; double z_m; double value; };
    std::vector<Row> rows;
    int line_number = 1;
    while (std::getline(csv, line)) {
        ++line_number;
        if (trim(line).empty())
            continue;
        const auto cells = split_csv_line(line);
        const int max_idx = std::max({time_idx, z_idx, value_idx});
        if (static_cast<int>(cells.size()) <= max_idx)
            throw std::runtime_error("CSV " + csv_path.string() + " line " +
                                     std::to_string(line_number) + " has too few columns");
        const double raw_time = parse_double(cells[static_cast<size_t>(time_idx)],
                                             csv_path, line_number, time_column);
        rows.push_back(Row{
            to_seconds(raw_time, time_column),
            parse_double(cells[static_cast<size_t>(z_idx)], csv_path, line_number, z_column),
            parse_double(cells[static_cast<size_t>(value_idx)], csv_path, line_number, value_column),
        });
    }
    if (rows.empty())
        throw std::runtime_error("CSV file has no data rows: " + csv_path.string());

    std::vector<double> times;
    std::vector<double> depths;
    times.reserve(rows.size());
    depths.reserve(rows.size());
    for (const auto& row : rows) {
        times.push_back(row.t_s);
        depths.push_back(row.z_m);
    }
    times_s_ = sorted_unique(std::move(times));
    depths_m_ = sorted_unique(std::move(depths));
    values_.assign(times_s_.size() * depths_m_.size(),
                   std::numeric_limits<double>::quiet_NaN());

    for (const auto& row : rows) {
        const size_t ti = nearest_index(times_s_, row.t_s);
        const size_t zi = nearest_index(depths_m_, row.z_m);
        values_[ti * depths_m_.size() + zi] = row.value;
    }

    for (size_t ti = 0; ti < times_s_.size(); ++ti) {
        for (size_t zi = 0; zi < depths_m_.size(); ++zi) {
            if (std::isnan(value_at_index(ti, zi))) {
                throw std::runtime_error("CSV " + csv_path.string() +
                    " must define a complete time-depth grid for column " + value_column);
            }
        }
    }
}

double TimeDepthTable::value_at_index(size_t time_index, size_t depth_index) const {
    return values_[time_index * depths_m_.size() + depth_index];
}

double TimeDepthTable::value_at(double t_s, double z_m) const {
    const auto [t0, t1] = bracket(times_s_, t_s);
    const auto [z0, z1] = bracket(depths_m_, z_m);
    const double wt = linear_weight(times_s_[t0], times_s_[t1], t_s);
    const double wz = linear_weight(depths_m_[z0], depths_m_[z1], z_m);

    const double v00 = value_at_index(t0, z0);
    const double v10 = value_at_index(t1, z0);
    const double v01 = value_at_index(t0, z1);
    const double v11 = value_at_index(t1, z1);
    const double v0 = (1.0 - wt) * v00 + wt * v10;
    const double v1 = (1.0 - wt) * v01 + wt * v11;
    return (1.0 - wz) * v0 + wz * v1;
}
