#pragma once

#include <filesystem>
#include <fstream>
#include <vector>

#include "constitutive/ConstitutiveModel.hpp"
#include "elements/Element.hpp"
#include "io/CaseParser.hpp"
#include "mesh/Mesh.hpp"
#include "solver/TimeState.hpp"
#include "thermal/ThermalField.hpp"

struct DamageTrackingOptions {
    bool enabled = false;
    std::vector<double> damage_thresholds;
    double failure_D_critical = 0.5;
    double creep_rate_multiplier_threshold = 10.0;
    double D_max = 0.99;
    DMParams dm{};
    double E_Pa = 0.0;
    double nu = 0.0;
    bool has_dm_reference = false;
};

class DamageDiagnostics {
public:
    DamageDiagnostics(const std::filesystem::path& out_dir,
                      const Mesh& mesh,
                      const Element& element,
                      const ThermalField& thermal,
                      DamageTrackingOptions options);

    void initialize(const TimeState& state, const ConstitutiveModel& model, double time_s);
    void record(const TimeState& state, const ConstitutiveModel& model, double time_s);

    bool enabled() const { return options_.enabled; }

    static double effective_stress(const Stress& sigma);
    static double effective_strain_rate(const Strain& rate);

private:
    struct PointInfo {
        double r = 0.0;
        double z = 0.0;
    };

    const Mesh& mesh_;
    const Element& element_;
    const ThermalField& thermal_;
    DamageTrackingOptions options_;
    int n_gp_ = 0;
    int total_gp_ = 0;
    int wall_gp_ = 0;
    bool initialized_ = false;

    std::vector<PointInfo> point_info_;
    std::vector<double> previous_D_;
    std::vector<double> previous_rate_;
    std::vector<double> previous_previous_rate_;
    std::vector<char> has_previous_rate_;
    std::vector<char> has_previous_previous_rate_;
    std::vector<std::vector<char>> threshold_crossed_;
    std::vector<char> failure_crossed_;
    std::vector<char> rate_crossed_;
    std::vector<char> inflection_recorded_;

    std::ofstream events_csv_;
    std::ofstream wall_csv_;

    void prepare_files(const std::filesystem::path& out_dir);
    void prepare_points();
    void write_event(double time_s, int gp_id, double D, double eps_dot,
                     const char* event_type);
    void write_wall(double time_s, const TimeState& state,
                    const ConstitutiveModel& model);
    double rate_at(const TimeState& state, const ConstitutiveModel& model,
                   int gp_id, double time_s) const;
    double dm_rate_at(const TimeState& state, int gp_id, double time_s) const;
};
