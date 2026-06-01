#pragma once

#include <string>
#include <vector>

#include <Eigen/Cholesky>
#include <Eigen/Core>

#include "elements/Element.hpp"
#include "mesh/Mesh.hpp"
#include "thermal/ThermalField.hpp"

struct Conduction2DLayer {
    double z_top_m = 0.0;
    double z_bottom_m = 0.0;
    double k_W_m_K = 2.5;
    double rho_kg_m3 = 2160.0;
    double cp_J_kg_K = 900.0;
};

struct Conduction2DOptions {
    double k_W_m_K = 2.5;
    double rho_kg_m3 = 2160.0;
    double cp_J_kg_K = 900.0;
    double initial_T_K = 298.15;
    double inner_wall_T_K = 298.15;
    double outer_T_K = 298.15;
    double top_T_K = 298.15;
    double bottom_T_K = 298.15;
    double dt_thermal_s = 3600.0;
    double beta = 0.5;
    double alpha_thermal = 0.0;
    double T_reference_K = 298.15;
    std::string outer_bc = "prescribed";
    std::string top_bc = "flux_zero";
    std::string bottom_bc = "flux_zero";
    std::vector<Conduction2DLayer> layers;
    std::vector<double> initial_nodal_T_K;
};

class Conduction2DField : public ThermalField {
public:
    Conduction2DField(const Mesh2D& mesh,
                      const Element& element,
                      Conduction2DOptions options);

    double temperature_at(const Eigen::Vector2d& x, double t) const override;
    double alpha_thermal() const override { return options_.alpha_thermal; }
    double T_reference() const override { return options_.T_reference_K; }

    void advance_to(double t_s) const;
    double current_time_s() const { return current_time_s_; }
    const Eigen::VectorXd& nodal_temperatures() const { return T_; }
    double total_energy_J() const;
    double last_boundary_heat_J() const { return last_boundary_heat_J_; }

private:
    struct LayerProperties {
        double k = 0.0;
        double rho_cp = 0.0;
    };

    Mesh2D mesh_;
    const Element& element_;
    Conduction2DOptions options_;
    Eigen::MatrixXd C_;
    Eigen::MatrixXd H_;
    std::vector<int> prescribed_;
    std::vector<int> unknown_;

    mutable Eigen::VectorXd T_;
    Eigen::VectorXd T_initial_;
    mutable double current_time_s_ = 0.0;
    mutable double last_boundary_heat_J_ = 0.0;
    mutable double cached_dt_s_ = -1.0;
    mutable Eigen::LDLT<Eigen::MatrixXd> cached_factor_;

    void assemble_matrices();
    void setup_boundary_sets();
    void apply_prescribed_temperatures(Eigen::VectorXd& T) const;
    void advance_one_step(double dt_s) const;
    double interpolate_temperature(const Eigen::Vector2d& x) const;
    LayerProperties properties_at(double z) const;
};
