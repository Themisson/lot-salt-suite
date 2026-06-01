#pragma once
#include <filesystem>
#include <string>
#include <vector>

// ── DM parameters (SI units) ─────────────────────────────────────────────────
struct DMParams {
    double e0_s;      // reference strain rate [1/s]
    double sig0;      // reference stress [Pa]
    double T0;        // reference temperature [K]
    double n1, n2;    // exponents (n1 for σ_ef ≤ σ₀, n2 for σ_ef > σ₀)
    double Q_over_R;  // activation energy / gas constant [K]
};

struct ThermalLayer {
    double z_top_m = 0.0;
    double z_bottom_m = 0.0;
    double k_W_m_K = 2.5;
    double rho_kg_m3 = 2160.0;
    double cp_J_kg_K = 900.0;
};

// ── Geometry ─────────────────────────────────────────────────────────────────
struct GeomParams {
    double Ri;            // inner radius (m)
    double outer_factor;  // Re = outer_factor * Ri
};

// ── Mesh ─────────────────────────────────────────────────────────────────────
struct MeshParams {
    int    n_radial;  // number of elements in radial direction
    double ratio;     // length of last / first element (geometric progression)
    int    n_axial = 1;
    bool   adaptive = false;
    double error_threshold = 0.10;
    int    max_refinement_levels = 3;
    double damage_refinement_threshold = -1.0; // <0 disables damage-driven marking
};

// ── Depths ───────────────────────────────────────────────────────────────────
struct DepthParams {
    double burial_m;       // depth to top of salt layer (m)
    double water_depth_m;  // water depth (m)
    double salt_above_m;   // salt thickness above the zone of interest (m)
};

// ── Thermal parameters ───────────────────────────────────────────────────────
struct ThermalParams {
    bool enabled = false;          // enables thermal strain coupling in Etapa 5c
    std::string mode;          // "constant" | "profile" | "conduction_1d" | "conduction_2d"
    double T_K;                // used for mode=constant
    double seabed_temp_C;      // used for mode=profile
    double grad_C_per_m;       // single thermal gradient (°C/m) for profile mode
    double alpha_thermal = 0.0; // thermal expansion coefficient [1/K]
    double T_reference_K = 298.15; // reference temperature for thermal strain [K]
    std::string outer_bc = "prescribed"; // "prescribed" | "flux_zero"
    std::string top_bc = "flux_zero"; // "prescribed" | "flux_zero"
    std::string bottom_bc = "flux_zero"; // "prescribed" | "flux_zero"
    double inner_wall_T_K = 298.15;
    double outer_T_K = 298.15;
    double top_T_K = 298.15;
    double bottom_T_K = 298.15;
    double initial_T_K = 298.15;
    double k_W_m_K = 2.5;
    double rho_kg_m3 = 2160.0;
    double cp_J_kg_K = 900.0;
    double dt_thermal_s = -1.0; // negative => default to mechanical dt_h after parsing time
    double beta = 0.5;
    std::vector<ThermalLayer> layers;
};

// ── Time integration ─────────────────────────────────────────────────────────
// Variable dt schedule: list of (until_s, dt_s) segments (SESTSAL %TIME.INCREMENT style).
// Until the first segment's until_s, use that dt; then switch to the next, etc.
struct TimeSegment {
    double until_s;  // switch to next segment after this simulation time [s]
    double dt_s;     // time step for this segment [s]
};

struct TimeParams {
    double total_s;                    // total simulation time [s]
    double dt_s;                       // fallback uniform step if steps is empty [s]
    std::string scheme;                // "explicit" | "implicit_adaptive"
    double tol_local = 1.0e-10;         // local Newton residual tolerance
    double tol_global = 1.0e-4;         // adaptive step-doubling tolerance
    double dt_min_s = 1.0e-12 * 3600.0; // minimum adaptive step [s]
    double dt_max_s = 10.0 * 3600.0;    // maximum adaptive step [s]
    std::vector<TimeSegment> steps;    // variable schedule (optional)
};

// ── EDMT parameters (primary creep, SI units) ────────────────────────────────
// K1: transient amplification factor (rate_initial = (1+K1)*rate_DM, K1 > 0)
// K2: decay rate with accumulated effective strain [1/strain]
// Saturation: as eps_v_eff→∞, rate → rate_DM (secondary only).
struct EdmtParams {
    double K1 = 0.0;  // dimensionless; 0 = no transient effect
    double K2 = 0.0;  // [1/strain]
};

struct ISVSHDMunsonParams {
    double e0_s = 5.0e-7;       // [1/s]
    double sig_ref = 1.0e6;     // [Pa]
    double n = 1.5;
    double Q_J_mol = 51.6e3;    // [J/mol]
    double T0 = 359.15;         // [K]
    double K_h = 1.2;
};

// ── Motta v1 damage parameters ───────────────────────────────────────────────
// Kachanov-style damage evolution:
//   dD/dt = A_d * max(f_dil, 0)^m_d / (1-D)^p_d
//   eps_dot = eps_dot_DM / (1-D)^n_d
struct MottaV1Params {
    double n_d = 2.0;
    double A_d = 1.0e-24;   // [1/(s Pa^m_d)] for the default m_d=1
    double m_d = 1.0;
    double p_d = 0.0;
    double D_max = 0.99;
};

struct Wang2004Params {
    double n_d = 2.0;
    double A_d = 1.2e-8;   // [1/(s Pa^m_d)]
    double m_d = 2.5;
    double p_d = 1.0;
    double D_max = 0.99;
};

struct AubertinISVSHDParams {
    double e0_s = 5.0e-7;      // [1/s]
    double sig0 = 1.0e6;       // [Pa]
    double n = 3.0;
    double Q_J_mol = 51.6e3;   // [J/mol]
    double T0 = 359.15;        // [K]
    double K1 = 0.8;
    double K2 = 2.5;           // [1/strain]
    double A_d = 1.5e-8;       // [1/(s Pa^m_d)]
    double m_d = 2.5;
    double n_d = 2.0;
    double p_d = 1.0;
    double D_max = 0.99;
};

struct SpierParams {
    double a = 0.25;        // dimensionless confinement coefficient
    double b_Pa = 0.0;      // cohesion/threshold term [Pa]
};

struct RatiganParams {
    double c = 0.81;        // threshold coefficient in sqrt(J2) - c*(I1_comp+d)^m
    double d_Pa = 0.0;      // pressure offset [Pa]
    double m = 1.0;         // pressure exponent
};

struct DeVriesParams {
    double e_Pa = 10.0e6;       // threshold amplitude [Pa]
    double f = 1.0;             // sinh coefficient
    double sigma0_Pa = 30.0e6;  // reference pressure [Pa]
};

struct HunscheParams {
    double g_Pa = 10.0e6;       // threshold amplitude [Pa]
    double I1_ref_Pa = 30.0e6;  // reference first invariant in compression [Pa]
    double h = 1.0;             // pressure exponent
};

// ── Creep flags ──────────────────────────────────────────────────────────────
struct CreepFlags {
    bool elastic_only = true;
    bool secondary    = false;
    bool primary      = false;  // EDMT transient creep
    bool tertiary     = false;
    bool damage       = false;
    std::string primary_model = "EDMT";
    std::string tertiary_model;
    std::string dilatancy_envelope;
};

// ── Output options ───────────────────────────────────────────────────────────
struct OutputParams {
    int every_n_steps = 10;
    bool vtu = false;
    int vtu_every_n_steps = 10;
    bool revolve_3d = false;
    bool damage_tracking = false;
    std::vector<double> damage_thresholds;
    double failure_D_critical = 0.5;
    double creep_rate_multiplier_threshold = 10.0;
};

// ── Complete case description ─────────────────────────────────────────────────
struct CaseData {
    std::string   name;
    GeomParams    geom;
    MeshParams    mesh;
    DepthParams   depths;
    std::string   element_type;  // default: "axisym_1d_L3"
    std::string   lithology;     // "halita" | "taquidrita" | "carnalita"
    double        fluid_Pa;      // drilling fluid pressure at wall (Pa)
    double        k0;            // lateral earth pressure coefficient
    double        overburden_grad_Pa_per_m;  // overburden stress gradient [Pa/m]
    DMParams      dm;
    EdmtParams    edmt;
    ISVSHDMunsonParams isv_sh_dm;
    MottaV1Params motta_v1;
    Wang2004Params wang_2004;
    AubertinISVSHDParams aubertin_isv_sh_d;
    SpierParams   spier;
    RatiganParams ratigan;
    DeVriesParams devries;
    HunscheParams hunsche;
    double        E_Pa;
    double        nu;
    ThermalParams thermal;
    TimeParams    time;
    CreepFlags    creep;
    OutputParams  output;
};

// Parse a YAML case file.  Loads litologia constants from data/litologias/.
// data_dir: path to the project data/ folder (default: relative to yaml_path).
// Throws std::runtime_error on missing required fields or invalid combinations.
CaseData parse_case(const std::filesystem::path& yaml_path,
                    const std::filesystem::path& data_dir = {});
