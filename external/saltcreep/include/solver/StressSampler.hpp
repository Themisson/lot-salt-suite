#pragma once

#include <filesystem>
#include <fstream>
#include <ostream>
#include <string>
#include <vector>

#include "elements/Element.hpp"
#include "mesh/Mesh.hpp"
#include "solver/TimeState.hpp"
#include "types.hpp"

struct StressDiagnosticsOptions {
    bool enabled = false;
    std::string scope = "wall"; // wall | all_gauss
    double depth_origin_m = 0.0;
};

struct StressSample {
    int gp_id = -1;
    int element_id = -1;
    int local_gp_id = -1;
    double r_m = 0.0;
    double z_m = 0.0;
    double depth_m = 0.0;
    Stress sigma = Stress::Zero();
    Stress deviatoric = Stress::Zero();
    double mean_stress_Pa = 0.0;
    double J2_Pa2 = 0.0;
    double sigma_ef_Pa = 0.0;
};

namespace stress_sampler {

std::vector<StressSample> sample_gauss_points(const Mesh& mesh,
                                              const Element& element,
                                              const TimeState& state,
                                              double depth_origin_m);

std::vector<StressSample> sample_wall_gauss_points(const Mesh& mesh,
                                                   const Element& element,
                                                   const TimeState& state,
                                                   double depth_origin_m);

void write_stress_header(std::ostream& out);
void write_stress_record(std::ostream& out,
                         double t_h,
                         const StressSample& sample);
void write_wall_stress_record(std::ostream& out,
                              const Mesh& mesh,
                              const Element& element,
                              const TimeState& state,
                              double t_h,
                              double depth_origin_m);
void write_all_gauss_stress_record(std::ostream& out,
                                   const Mesh& mesh,
                                   const Element& element,
                                   const TimeState& state,
                                   double t_h,
                                   double depth_origin_m);

} // namespace stress_sampler

class StressDiagnosticsWriter {
public:
    StressDiagnosticsWriter(const std::filesystem::path& out_dir,
                            StressDiagnosticsOptions options);

    void write(const Mesh& mesh,
               const Element& element,
               const TimeState& state,
               double t_h);

    bool enabled() const { return options_.enabled; }

private:
    StressDiagnosticsOptions options_;
    std::ofstream wall_csv_;
    std::ofstream profile_csv_;
};
