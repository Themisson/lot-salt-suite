#include "solver/StressSampler.hpp"

#include <algorithm>
#include <cmath>
#include <iomanip>
#include <stdexcept>
#include <utility>

#include "physics/stress_utils.hpp"

namespace {

Eigen::Vector2d gauss_position(const Mesh& mesh,
                               const Element& element,
                               int element_id,
                               int local_gp_id) {
    const int nne = element.n_nodes();
    const int n_gp = static_cast<int>(element.gauss_points().size());
    if (element_id < 0 || element_id >= mesh.n_elements ||
        local_gp_id < 0 || local_gp_id >= n_gp)
        throw std::out_of_range("StressSampler: invalid Gauss point index");

    std::vector<Node> coords(nne);
    for (int i = 0; i < nne; ++i)
        coords[i] = mesh.nodes[mesh.elem_nodes[nne * element_id + i]];

    std::vector<double> N(nne);
    element.shape_functions(element.gauss_points()[local_gp_id], coords, N);

    Eigen::Vector2d x = Eigen::Vector2d::Zero();
    for (int i = 0; i < nne; ++i) {
        x[0] += N[i] * coords[i].r;
        x[1] += N[i] * coords[i].z;
    }
    return x;
}

StressSample make_sample(const Mesh& mesh,
                         const Element& element,
                         const TimeState& state,
                         int element_id,
                         int local_gp_id,
                         double depth_origin_m) {
    const int n_gp = static_cast<int>(element.gauss_points().size());
    const int gp_id = element_id * n_gp + local_gp_id;
    if (gp_id < 0 || gp_id >= static_cast<int>(state.sigma_gp.size()))
        throw std::runtime_error("StressSampler: state.sigma_gp size is inconsistent with mesh");

    const Eigen::Vector2d x = gauss_position(mesh, element, element_id, local_gp_id);
    StressSample sample;
    sample.gp_id = gp_id;
    sample.element_id = element_id;
    sample.local_gp_id = local_gp_id;
    sample.r_m = x[0];
    sample.z_m = x[1];
    sample.depth_m = depth_origin_m + x[1];
    sample.sigma = state.sigma_gp[gp_id];
    sample.deviatoric = stress_utils::deviatoric_stress(sample.sigma);
    sample.mean_stress_Pa = stress_utils::mean_stress(sample.sigma);
    sample.J2_Pa2 = stress_utils::j2_from_deviatoric(sample.deviatoric);
    sample.sigma_ef_Pa = stress_utils::von_mises_effective_stress(sample.sigma);
    return sample;
}

} // namespace

namespace stress_sampler {

std::vector<StressSample> sample_gauss_points(const Mesh& mesh,
                                              const Element& element,
                                              const TimeState& state,
                                              double depth_origin_m) {
    const int n_gp = static_cast<int>(element.gauss_points().size());
    const int expected = mesh.n_elements * n_gp;
    if (static_cast<int>(state.sigma_gp.size()) != expected)
        throw std::runtime_error("StressSampler: expected one stress per Gauss point");

    std::vector<StressSample> samples;
    samples.reserve(static_cast<size_t>(expected));
    for (int e = 0; e < mesh.n_elements; ++e)
        for (int g = 0; g < n_gp; ++g)
            samples.push_back(make_sample(mesh, element, state, e, g, depth_origin_m));
    return samples;
}

std::vector<StressSample> sample_wall_gauss_points(const Mesh& mesh,
                                                   const Element& element,
                                                   const TimeState& state,
                                                   double depth_origin_m) {
    std::vector<StressSample> all =
        sample_gauss_points(mesh, element, state, depth_origin_m);
    if (all.empty())
        return {};

    const auto min_it = std::min_element(
        all.begin(), all.end(),
        [](const StressSample& a, const StressSample& b) { return a.r_m < b.r_m; });
    const double min_r = min_it->r_m;
    const double tol = 1.0e-10 * std::max(1.0, std::abs(min_r));

    std::vector<StressSample> wall;
    for (const auto& sample : all) {
        if (std::abs(sample.r_m - min_r) <= tol)
            wall.push_back(sample);
    }
    std::sort(wall.begin(), wall.end(), [](const StressSample& a, const StressSample& b) {
        if (a.z_m == b.z_m)
            return a.gp_id < b.gp_id;
        return a.z_m < b.z_m;
    });
    return wall;
}

void write_stress_header(std::ostream& out) {
    out << "t_h,gp_id,element_id,local_gp_id,r_m,z_m,depth_m,"
        << "sigma_rr_Pa,sigma_theta_Pa,sigma_theta_comp_Pa,"
        << "sigma_zz_Pa,sigma_rz_Pa,"
        << "sdev_rr_Pa,sdev_theta_Pa,sdev_zz_Pa,sdev_rz_Pa,"
        << "mean_stress_Pa,J2_Pa2,sigma_ef_Pa\n";
}

void write_stress_record(std::ostream& out,
                         double t_h,
                         const StressSample& sample) {
    out << t_h << ","
        << sample.gp_id << ","
        << sample.element_id << ","
        << sample.local_gp_id << ","
        << sample.r_m << ","
        << sample.z_m << ","
        << sample.depth_m << ","
        << sample.sigma[0] << ","
        << sample.sigma[1] << ","
        << stress_utils::sigma_theta_compression_positive(sample.sigma) << ","
        << sample.sigma[2] << ","
        << sample.sigma[3] << ","
        << sample.deviatoric[0] << ","
        << sample.deviatoric[1] << ","
        << sample.deviatoric[2] << ","
        << sample.deviatoric[3] << ","
        << sample.mean_stress_Pa << ","
        << sample.J2_Pa2 << ","
        << sample.sigma_ef_Pa << "\n";
}

void write_wall_stress_record(std::ostream& out,
                              const Mesh& mesh,
                              const Element& element,
                              const TimeState& state,
                              double t_h,
                              double depth_origin_m) {
    for (const auto& sample :
         sample_wall_gauss_points(mesh, element, state, depth_origin_m))
        write_stress_record(out, t_h, sample);
}

void write_all_gauss_stress_record(std::ostream& out,
                                   const Mesh& mesh,
                                   const Element& element,
                                   const TimeState& state,
                                   double t_h,
                                   double depth_origin_m) {
    for (const auto& sample :
         sample_gauss_points(mesh, element, state, depth_origin_m))
        write_stress_record(out, t_h, sample);
}

} // namespace stress_sampler

StressDiagnosticsWriter::StressDiagnosticsWriter(
    const std::filesystem::path& out_dir,
    StressDiagnosticsOptions options)
    : options_(std::move(options)) {
    if (!options_.enabled)
        return;
    if (options_.scope != "wall" && options_.scope != "all_gauss")
        throw std::runtime_error("StressDiagnosticsWriter: scope must be wall or all_gauss");

    std::filesystem::create_directories(out_dir);
    wall_csv_.open(out_dir / "wall_stress.csv");
    if (!wall_csv_)
        throw std::runtime_error("StressDiagnosticsWriter: cannot open wall_stress.csv");
    wall_csv_ << std::fixed << std::setprecision(12);
    stress_sampler::write_stress_header(wall_csv_);

    if (options_.scope == "all_gauss") {
        profile_csv_.open(out_dir / "stress_profile.csv");
        if (!profile_csv_)
            throw std::runtime_error("StressDiagnosticsWriter: cannot open stress_profile.csv");
        profile_csv_ << std::fixed << std::setprecision(12);
        stress_sampler::write_stress_header(profile_csv_);
    }
}

void StressDiagnosticsWriter::write(const Mesh& mesh,
                                    const Element& element,
                                    const TimeState& state,
                                    double t_h) {
    if (!options_.enabled)
        return;

    stress_sampler::write_wall_stress_record(
        wall_csv_, mesh, element, state, t_h, options_.depth_origin_m);
    if (profile_csv_.is_open()) {
        stress_sampler::write_all_gauss_stress_record(
            profile_csv_, mesh, element, state, t_h, options_.depth_origin_m);
    }
}
