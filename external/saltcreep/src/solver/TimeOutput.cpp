#include "solver/TimeOutput.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>

namespace time_output {
namespace {

constexpr double kMetersToInches = 39.37007874015748;

double inner_radius(const Mesh& mesh) {
    const auto it = std::min_element(
        mesh.nodes.begin(), mesh.nodes.end(),
        [](const Node& a, const Node& b) { return a.r < b.r; });
    return it == mesh.nodes.end() ? 0.0 : it->r;
}

bool is_inner_wall_node(const Mesh& mesh, int node_id) {
    const double Ri = inner_radius(mesh);
    const double tol = 1.0e-10 * std::max(1.0, std::abs(Ri));
    return std::abs(mesh.nodes[node_id].r - Ri) <= tol;
}

double u_r_at(const Mesh& mesh, const Eigen::VectorXd& u, int node_id) {
    return u[mesh.dof_index(node_id, 0)];
}

double u_z_at(const Mesh& mesh, const Eigen::VectorXd& u, int node_id) {
    if (mesh.dofs_per_node < 2)
        return 0.0;
    return u[mesh.dof_index(node_id, 1)];
}

} // namespace

double wall_displacement_magnitude_m(const Mesh& mesh, const Eigen::VectorXd& u) {
    return -u_r_at(mesh, u, 0);
}

void write_closure_header(std::ofstream& csv) {
    csv << "t_h,closure_pct,wall_disp_m,u_wall_m,"
        << "diameter_wall_m,diameter_wall_in\n";
}

void write_closure_record(std::ofstream& csv,
                          const Mesh& mesh,
                          const Eigen::VectorXd& u,
                          double t_h,
                          double closure_pct) {
    const double Ri = inner_radius(mesh);
    const double u_wall = wall_displacement_magnitude_m(mesh, u);
    const double diameter_m = 2.0 * (Ri - u_wall);
    csv << t_h << "," << closure_pct << ","
        << u_r_at(mesh, u, 0) << ","
        << u_wall << ","
        << diameter_m << ","
        << diameter_m * kMetersToInches << "\n";
}

void write_displacement_profile_header(std::ofstream& csv) {
    csv << "t_h,node_id,r_m,z_m,u_r_m,u_z_m\n";
}

void write_displacement_profile_record(std::ofstream& csv,
                                       const Mesh& mesh,
                                       const Eigen::VectorXd& u,
                                       double t_h) {
    for (int node_id = 0; node_id < mesh.n_nodes; ++node_id) {
        const Node& node = mesh.nodes[node_id];
        csv << t_h << "," << node_id << ","
            << node.r << "," << node.z << ","
            << u_r_at(mesh, u, node_id) << ","
            << u_z_at(mesh, u, node_id) << "\n";
    }
}

void write_wall_profile_header(std::ofstream& csv) {
    csv << "t_h,node_id,z_m,u_r_m,depth_m,"
        << "diameter_m,diameter_in,original_diameter_in\n";
}

void write_wall_profile_record(std::ofstream& csv,
                               const Mesh& mesh,
                               const Eigen::VectorXd& u,
                               double t_h,
                               double depth_origin_m,
                               double well_radius_m) {
    const double Ri = well_radius_m > 0.0 ? well_radius_m : inner_radius(mesh);
    const double original_diameter_in = 2.0 * Ri * kMetersToInches;
    for (int node_id = 0; node_id < mesh.n_nodes; ++node_id) {
        if (!is_inner_wall_node(mesh, node_id))
            continue;
        const double ur = u_r_at(mesh, u, node_id);
        const double diameter_m = 2.0 * (Ri + ur);
        csv << t_h << "," << node_id << ","
            << mesh.nodes[node_id].z << ","
            << ur << ","
            << depth_origin_m + mesh.nodes[node_id].z << ","
            << diameter_m << ","
            << diameter_m * kMetersToInches << ","
            << original_diameter_in << "\n";
    }
}

void write_wall_pressure_profile_header(std::ofstream& csv) {
    csv << "t_h,node_id,z_m,depth_m,p_wall_Pa,T_wall_K\n";
}

void write_wall_pressure_profile_record(std::ofstream& csv,
                                        const Mesh& mesh,
                                        const WallPressureField& pressure,
                                        const ThermalField& thermal,
                                        double t_h,
                                        double time_s,
                                        double depth_origin_m) {
    for (int node_id = 0; node_id < mesh.n_nodes; ++node_id) {
        if (!is_inner_wall_node(mesh, node_id))
            continue;
        const Eigen::Vector2d x{mesh.nodes[node_id].r, mesh.nodes[node_id].z};
        csv << t_h << "," << node_id << ","
            << mesh.nodes[node_id].z << ","
            << depth_origin_m + mesh.nodes[node_id].z << ","
            << pressure.pressure_at(x, time_s) << ","
            << thermal.temperature_at(x, time_s) << "\n";
    }
}

} // namespace time_output
