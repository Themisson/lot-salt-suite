#pragma once

#include <fstream>

#include <Eigen/Core>

#include "mesh/Mesh.hpp"

namespace time_output {

double wall_displacement_magnitude_m(const Mesh& mesh, const Eigen::VectorXd& u);

void write_closure_header(std::ofstream& csv);
void write_closure_record(std::ofstream& csv,
                          const Mesh& mesh,
                          const Eigen::VectorXd& u,
                          double t_h,
                          double closure_pct);

void write_displacement_profile_header(std::ofstream& csv);
void write_displacement_profile_record(std::ofstream& csv,
                                       const Mesh& mesh,
                                       const Eigen::VectorXd& u,
                                       double t_h);

void write_wall_profile_header(std::ofstream& csv);
void write_wall_profile_record(std::ofstream& csv,
                               const Mesh& mesh,
                               const Eigen::VectorXd& u,
                               double t_h);

} // namespace time_output
