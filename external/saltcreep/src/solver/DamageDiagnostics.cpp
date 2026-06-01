#include "solver/DamageDiagnostics.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <limits>
#include <sstream>

#include "constitutive/double_mechanism.hpp"

namespace {
std::vector<double> normalize_thresholds(DamageTrackingOptions options) {
    std::vector<double> values = std::move(options.damage_thresholds);
    values.push_back(options.failure_D_critical);
    values.push_back(options.D_max);
    values.erase(std::remove_if(values.begin(), values.end(),
                                [](double v) { return !(v > 0.0 && v <= 1.0); }),
                 values.end());
    std::sort(values.begin(), values.end());
    values.erase(std::unique(values.begin(), values.end(),
                             [](double a, double b) { return std::abs(a - b) < 1.0e-12; }),
                 values.end());
    return values;
}

std::string threshold_event_name(double value) {
    std::ostringstream oss;
    oss << "D_threshold_" << std::setprecision(6) << value;
    return oss.str();
}
} // namespace

DamageDiagnostics::DamageDiagnostics(const std::filesystem::path& out_dir,
                                     const Mesh& mesh,
                                     const Element& element,
                                     const ThermalField& thermal,
                                     DamageTrackingOptions options)
    : mesh_(mesh)
    , element_(element)
    , thermal_(thermal)
    , options_(std::move(options))
    , n_gp_(static_cast<int>(element.gauss_points().size()))
    , total_gp_(mesh.n_elements * n_gp_) {
    if (!options_.enabled)
        return;
    options_.damage_thresholds = normalize_thresholds(options_);
    prepare_points();
    prepare_files(out_dir);
    previous_D_.assign(total_gp_, 0.0);
    previous_rate_.assign(total_gp_, 0.0);
    previous_previous_rate_.assign(total_gp_, 0.0);
    has_previous_rate_.assign(total_gp_, 0);
    has_previous_previous_rate_.assign(total_gp_, 0);
    threshold_crossed_.assign(
        total_gp_, std::vector<char>(options_.damage_thresholds.size(), 0));
    failure_crossed_.assign(total_gp_, 0);
    rate_crossed_.assign(total_gp_, 0);
    inflection_recorded_.assign(total_gp_, 0);
}

void DamageDiagnostics::prepare_files(const std::filesystem::path& out_dir) {
    std::filesystem::create_directories(out_dir);
    events_csv_.open(out_dir / "damage_events.csv");
    wall_csv_.open(out_dir / "damage_wall.csv");
    events_csv_ << "t_h,r,z,gp_id,D,eps_dot,event_type\n";
    wall_csv_ << "t_h,D,eps_dot,sigma_ef\n";
    events_csv_ << std::fixed << std::setprecision(12);
    wall_csv_ << std::fixed << std::setprecision(12);
}

void DamageDiagnostics::prepare_points() {
    const auto gps = element_.gauss_points();
    const int nne = element_.n_nodes();
    point_info_.assign(total_gp_, {});
    double min_r = std::numeric_limits<double>::infinity();
    for (int e = 0; e < mesh_.n_elements; ++e) {
        std::vector<Node> coords(nne);
        for (int i = 0; i < nne; ++i)
            coords[i] = mesh_.nodes[mesh_.elem_nodes[nne * e + i]];
        for (int g = 0; g < n_gp_; ++g) {
            std::vector<double> N(nne);
            element_.shape_functions(gps[g], coords, N);
            PointInfo point;
            for (int i = 0; i < nne; ++i) {
                point.r += N[i] * coords[i].r;
                point.z += N[i] * coords[i].z;
            }
            const int idx = e * n_gp_ + g;
            point_info_[idx] = point;
            if (point.r < min_r) {
                min_r = point.r;
                wall_gp_ = idx;
            }
        }
    }
}

double DamageDiagnostics::effective_stress(const Stress& sigma) {
    const double p = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    const double s0 = sigma[0] - p;
    const double s1 = sigma[1] - p;
    const double s2 = sigma[2] - p;
    const double s3 = sigma[3];
    return std::sqrt(std::max(0.0, 1.5 * (s0*s0 + s1*s1 + s2*s2 + 2.0*s3*s3)));
}

double DamageDiagnostics::effective_strain_rate(const Strain& rate) {
    const double mean = (rate[0] + rate[1] + rate[2]) / 3.0;
    const double e0 = rate[0] - mean;
    const double e1 = rate[1] - mean;
    const double e2 = rate[2] - mean;
    const double e3 = rate[3];
    return std::sqrt(std::max(0.0, (2.0 / 3.0) *
        (e0*e0 + e1*e1 + e2*e2 + 0.5*e3*e3)));
}

double DamageDiagnostics::rate_at(const TimeState& state,
                                  const ConstitutiveModel& model,
                                  int gp_id,
                                  double time_s) const {
    const auto& p = point_info_[gp_id];
    const double T = thermal_.temperature_at(Eigen::Vector2d(p.r, p.z), time_s);
    const auto result = model.evaluate(state.sigma_gp[gp_id], state.state_gp[gp_id], T, 0.0);
    return effective_strain_rate(result.strain_rate_voigt);
}

double DamageDiagnostics::dm_rate_at(const TimeState& state,
                                     int gp_id,
                                     double time_s) const {
    if (!options_.has_dm_reference)
        return 0.0;
    const auto& p = point_info_[gp_id];
    const double T = thermal_.temperature_at(Eigen::Vector2d(p.r, p.z), time_s);
    DoubleMechanism dm(options_.dm, options_.E_Pa, options_.nu);
    const auto result = dm.evaluate(state.sigma_gp[gp_id], InternalState{}, T, 0.0);
    return effective_strain_rate(result.strain_rate_voigt);
}

void DamageDiagnostics::write_event(double time_s, int gp_id, double D,
                                    double eps_dot, const char* event_type) {
    const auto& p = point_info_[gp_id];
    events_csv_ << (time_s / 3600.0) << ','
                << p.r << ','
                << p.z << ','
                << gp_id << ','
                << D << ','
                << eps_dot << ','
                << event_type << '\n';
    events_csv_.flush();
}

void DamageDiagnostics::write_wall(double time_s, const TimeState& state,
                                   const ConstitutiveModel& model) {
    const double rate = rate_at(state, model, wall_gp_, time_s);
    wall_csv_ << (time_s / 3600.0) << ','
              << state.state_gp[wall_gp_].damage_D << ','
              << rate << ','
              << effective_stress(state.sigma_gp[wall_gp_]) << '\n';
    wall_csv_.flush();
}

void DamageDiagnostics::initialize(const TimeState& state,
                                   const ConstitutiveModel& model,
                                   double time_s) {
    if (!options_.enabled)
        return;
    for (int idx = 0; idx < total_gp_; ++idx) {
        previous_D_[idx] = state.state_gp[idx].damage_D;
        previous_rate_[idx] = rate_at(state, model, idx, time_s);
        has_previous_rate_[idx] = 1;
    }
    write_wall(time_s, state, model);
    initialized_ = true;
}

void DamageDiagnostics::record(const TimeState& state,
                               const ConstitutiveModel& model,
                               double time_s) {
    if (!options_.enabled)
        return;
    if (!initialized_)
        initialize(state, model, time_s);

    for (int idx = 0; idx < total_gp_; ++idx) {
        const double D = state.state_gp[idx].damage_D;
        const double rate = rate_at(state, model, idx, time_s);
        for (size_t t = 0; t < options_.damage_thresholds.size(); ++t) {
            const double threshold = options_.damage_thresholds[t];
            if (!threshold_crossed_[idx][t] && previous_D_[idx] < threshold && D >= threshold) {
                const std::string event = threshold_event_name(threshold);
                write_event(time_s, idx, D, rate, event.c_str());
                threshold_crossed_[idx][t] = 1;
            }
        }

        if (!failure_crossed_[idx] && previous_D_[idx] < options_.failure_D_critical &&
            D >= options_.failure_D_critical) {
            write_event(time_s, idx, D, rate, "failure_D_critical");
            failure_crossed_[idx] = 1;
        }

        const double dm_rate = dm_rate_at(state, idx, time_s);
        if (!rate_crossed_[idx] && dm_rate > 0.0 &&
            rate >= options_.creep_rate_multiplier_threshold * dm_rate) {
            write_event(time_s, idx, D, rate, "creep_rate_threshold");
            rate_crossed_[idx] = 1;
        }

        if (!inflection_recorded_[idx] && has_previous_previous_rate_[idx]) {
            const double previous_slope = previous_rate_[idx] - previous_previous_rate_[idx];
            const double current_slope = rate - previous_rate_[idx];
            if (previous_slope <= 0.0 && current_slope > 0.0) {
                write_event(time_s, idx, D, rate, "inflection");
                inflection_recorded_[idx] = 1;
            }
        }

        previous_D_[idx] = D;
        previous_previous_rate_[idx] = previous_rate_[idx];
        previous_rate_[idx] = rate;
        has_previous_previous_rate_[idx] = has_previous_rate_[idx];
        has_previous_rate_[idx] = 1;
    }
    write_wall(time_s, state, model);
}
