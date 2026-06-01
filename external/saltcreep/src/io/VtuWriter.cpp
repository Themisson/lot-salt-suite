#include "io/VtuWriter.hpp"

#include <algorithm>
#include <array>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace {

std::string xml_escape(const std::string& value) {
    std::string out;
    out.reserve(value.size());
    for (char c : value) {
        switch (c) {
            case '&': out += "&amp;"; break;
            case '<': out += "&lt;"; break;
            case '>': out += "&gt;"; break;
            case '"': out += "&quot;"; break;
            default: out.push_back(c); break;
        }
    }
    return out;
}

int vtk_cell_type(const Mesh& mesh, const Element& element) {
    const int n = element.n_nodes();
    if (mesh.dofs_per_node == 1 && n == 3)
        return 21; // VTK_QUADRATIC_EDGE
    if (n == 3)
        return 5;  // VTK_TRIANGLE
    if (n == 4)
        return 9;  // VTK_QUAD
    if (n == 6)
        return 22; // VTK_QUADRATIC_TRIANGLE
    if (n == 8)
        return 23; // VTK_QUADRATIC_QUAD
    if (n == 9)
        return 28; // VTK_BIQUADRATIC_QUAD
    throw std::runtime_error("VtuWriter: unsupported element node count");
}

double scalar_or_zero(const Eigen::VectorXd* values, int index) {
    return (values && index >= 0 && index < values->size()) ? (*values)[index] : 0.0;
}

std::array<double, 3> nodal_displacement(const Mesh& mesh,
                                         const Eigen::VectorXd* u,
                                         int node_id) {
    std::array<double, 3> out{0.0, 0.0, 0.0};
    if (!u)
        return out;
    out[0] = scalar_or_zero(u, mesh.dof_index(node_id, 0));
    if (mesh.dofs_per_node > 1)
        out[1] = scalar_or_zero(u, mesh.dof_index(node_id, 1));
    return out;
}

template <typename Vec4>
std::array<double, 4> average_gp_vector(const std::vector<Vec4>* values,
                                        int start,
                                        int n_gp) {
    std::array<double, 4> out{0.0, 0.0, 0.0, 0.0};
    if (!values || static_cast<int>(values->size()) < start + n_gp)
        return out;
    for (int g = 0; g < n_gp; ++g)
        for (int c = 0; c < 4; ++c)
            out[c] += (*values)[start + g][c];
    for (double& v : out)
        v /= static_cast<double>(n_gp);
    return out;
}

double average_gp_damage(const std::vector<InternalState>* values,
                         int start,
                         int n_gp) {
    if (!values || static_cast<int>(values->size()) < start + n_gp)
        return 0.0;
    double out = 0.0;
    for (int g = 0; g < n_gp; ++g)
        out += (*values)[start + g].damage_D;
    return out / static_cast<double>(n_gp);
}

void write_array_header(std::ofstream& out,
                        const std::string& name,
                        int n_components = 1,
                        const std::string& type = "Float64") {
    out << "        <DataArray type=\"" << type << "\" Name=\"" << name << "\"";
    if (n_components > 1)
        out << " NumberOfComponents=\"" << n_components << "\"";
    out << " format=\"ascii\">\n          ";
}

void write_array_footer(std::ofstream& out) {
    out << "\n        </DataArray>\n";
}

} // namespace

std::string VtuWriter::frame_filename(const std::string& case_name, int frame_index) {
    std::ostringstream name;
    name << case_name << "_" << std::setw(4) << std::setfill('0') << frame_index << ".vtu";
    return name.str();
}

void VtuWriter::write(const std::filesystem::path& path,
                      const Mesh& mesh,
                      const Element& element,
                      const VtuSnapshot& snapshot) {
    std::filesystem::create_directories(path.parent_path());
    std::ofstream out(path);
    if (!out)
        throw std::runtime_error("VtuWriter: cannot open " + path.string());

    const int n_nodes = mesh.n_nodes;
    const int n_cells = mesh.n_elements;
    const int nne = element.n_nodes();
    const int n_gp = static_cast<int>(element.gauss_points().size());
    const int cell_type = vtk_cell_type(mesh, element);

    std::vector<std::array<double, 4>> sigma_node(n_nodes, {0.0, 0.0, 0.0, 0.0});
    std::vector<std::array<double, 4>> epsv_node(n_nodes, {0.0, 0.0, 0.0, 0.0});
    std::vector<double> damage_node(n_nodes, 0.0);
    std::vector<int> counts(n_nodes, 0);

    std::vector<std::array<double, 4>> sigma_cell(n_cells, {0.0, 0.0, 0.0, 0.0});
    std::vector<std::array<double, 4>> epsv_cell(n_cells, {0.0, 0.0, 0.0, 0.0});
    std::vector<double> damage_cell(n_cells, 0.0);

    for (int e = 0; e < n_cells; ++e) {
        const int gp_start = e * n_gp;
        sigma_cell[e] = average_gp_vector(snapshot.sigma_gp, gp_start, n_gp);
        epsv_cell[e] = average_gp_vector(snapshot.eps_v_gp, gp_start, n_gp);
        damage_cell[e] = average_gp_damage(snapshot.state_gp, gp_start, n_gp);

        for (int i = 0; i < nne; ++i) {
            const int node_id = mesh.elem_nodes[nne * e + i];
            for (int c = 0; c < 4; ++c) {
                sigma_node[node_id][c] += sigma_cell[e][c];
                epsv_node[node_id][c] += epsv_cell[e][c];
            }
            damage_node[node_id] += damage_cell[e];
            counts[node_id] += 1;
        }
    }

    for (int n = 0; n < n_nodes; ++n) {
        const double inv = counts[n] > 0 ? 1.0 / static_cast<double>(counts[n]) : 1.0;
        for (int c = 0; c < 4; ++c) {
            sigma_node[n][c] *= inv;
            epsv_node[n][c] *= inv;
        }
        damage_node[n] *= inv;
    }

    out << std::setprecision(17);
    out << "<?xml version=\"1.0\"?>\n";
    out << "<VTKFile type=\"UnstructuredGrid\" version=\"0.1\" byte_order=\"LittleEndian\">\n";
    out << "  <UnstructuredGrid>\n";
    out << "    <Piece NumberOfPoints=\"" << n_nodes
        << "\" NumberOfCells=\"" << n_cells << "\">\n";

    out << "      <PointData Scalars=\"temperature_K\" Vectors=\"u\">\n";
    write_array_header(out, "u", 3);
    for (int n = 0; n < n_nodes; ++n) {
        const auto u = nodal_displacement(mesh, snapshot.u, n);
        out << u[0] << " " << u[1] << " " << u[2] << " ";
    }
    write_array_footer(out);

    write_array_header(out, "u_r");
    for (int n = 0; n < n_nodes; ++n)
        out << nodal_displacement(mesh, snapshot.u, n)[0] << " ";
    write_array_footer(out);

    write_array_header(out, "u_z");
    for (int n = 0; n < n_nodes; ++n)
        out << nodal_displacement(mesh, snapshot.u, n)[1] << " ";
    write_array_footer(out);

    write_array_header(out, "sigma", 4);
    for (const auto& v : sigma_node)
        out << v[0] << " " << v[1] << " " << v[2] << " " << v[3] << " ";
    write_array_footer(out);

    write_array_header(out, "eps_v", 4);
    for (const auto& v : epsv_node)
        out << v[0] << " " << v[1] << " " << v[2] << " " << v[3] << " ";
    write_array_footer(out);

    write_array_header(out, "damage_D");
    for (double v : damage_node)
        out << v << " ";
    write_array_footer(out);

    write_array_header(out, "temperature_K");
    for (const Node& node : mesh.nodes) {
        const Eigen::Vector2d x(node.r, node.z);
        const double T = snapshot.thermal ? snapshot.thermal->temperature_at(x, snapshot.time_s) : 0.0;
        out << T << " ";
    }
    write_array_footer(out);
    out << "      </PointData>\n";

    out << "      <CellData>\n";
    write_array_header(out, "sigma_cell", 4);
    for (const auto& v : sigma_cell)
        out << v[0] << " " << v[1] << " " << v[2] << " " << v[3] << " ";
    write_array_footer(out);

    write_array_header(out, "eps_v_cell", 4);
    for (const auto& v : epsv_cell)
        out << v[0] << " " << v[1] << " " << v[2] << " " << v[3] << " ";
    write_array_footer(out);

    write_array_header(out, "damage_D_cell");
    for (double v : damage_cell)
        out << v << " ";
    write_array_footer(out);
    out << "      </CellData>\n";

    out << "      <Points>\n";
    write_array_header(out, "Points", 3);
    for (const Node& node : mesh.nodes)
        out << node.r << " " << node.z << " 0 ";
    write_array_footer(out);
    out << "      </Points>\n";

    out << "      <Cells>\n";
    out << "        <DataArray type=\"Int32\" Name=\"connectivity\" format=\"ascii\">\n          ";
    for (int e = 0; e < n_cells; ++e)
        for (int i = 0; i < nne; ++i)
            out << mesh.elem_nodes[nne * e + i] << " ";
    out << "\n        </DataArray>\n";

    out << "        <DataArray type=\"Int32\" Name=\"offsets\" format=\"ascii\">\n          ";
    for (int e = 0; e < n_cells; ++e)
        out << (e + 1) * nne << " ";
    out << "\n        </DataArray>\n";

    out << "        <DataArray type=\"UInt8\" Name=\"types\" format=\"ascii\">\n          ";
    for (int e = 0; e < n_cells; ++e)
        out << cell_type << " ";
    out << "\n        </DataArray>\n";
    out << "      </Cells>\n";

    out << "    </Piece>\n";
    out << "  </UnstructuredGrid>\n";
    out << "</VTKFile>\n";
}

void VtuWriter::write_pvd(const std::filesystem::path& path,
                          const std::vector<VtuFrame>& frames) {
    std::filesystem::create_directories(path.parent_path());
    std::ofstream out(path);
    if (!out)
        throw std::runtime_error("VtuWriter: cannot open " + path.string());

    out << std::setprecision(17);
    out << "<?xml version=\"1.0\"?>\n";
    out << "<VTKFile type=\"Collection\" version=\"0.1\" byte_order=\"LittleEndian\">\n";
    out << "  <Collection>\n";
    for (const auto& frame : frames) {
        out << "    <DataSet timestep=\"" << frame.time_s
            << "\" group=\"\" part=\"0\" file=\"" << xml_escape(frame.file) << "\"/>\n";
    }
    out << "  </Collection>\n";
    out << "</VTKFile>\n";
}
