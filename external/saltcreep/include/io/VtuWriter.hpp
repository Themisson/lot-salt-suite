#pragma once
#include <filesystem>
#include <string>
#include <vector>

#include <Eigen/Core>

#include "elements/Element.hpp"
#include "mesh/Mesh.hpp"
#include "thermal/ThermalField.hpp"
#include "types.hpp"

struct VtuOutputOptions {
    bool enabled = false;
    int every_n_steps = 10;
    bool revolve_3d = false; // reserved; current writer exports the axisymmetric (r,z) sector
    std::string case_name;
    double well_radius_m = 0.0;
    double depth_origin_m = 0.0;
};

struct VtuFrame {
    std::string file;
    double time_s = 0.0;
};

struct VtuSnapshot {
    const Eigen::VectorXd* u = nullptr;
    const std::vector<Stress>* sigma_gp = nullptr;
    const std::vector<Strain>* eps_v_gp = nullptr;
    const std::vector<InternalState>* state_gp = nullptr;
    const ThermalField* thermal = nullptr;
    double time_s = 0.0;
};

class VtuWriter {
public:
    static std::string frame_filename(const std::string& case_name, int frame_index);

    static void write(const std::filesystem::path& path,
                      const Mesh& mesh,
                      const Element& element,
                      const VtuSnapshot& snapshot);

    static void write_pvd(const std::filesystem::path& path,
                          const std::vector<VtuFrame>& frames);
};
