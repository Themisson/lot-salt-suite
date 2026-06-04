#pragma once

#include <cstddef>
#include <string>
#include <vector>

#include "coupling/LotSaltPressureMap.hpp"
#include "coupling/LotSaltSigmaThetaBreakdown.hpp"
#include "lot/PknResult.hpp"
#include "salt/SaltWallStressDiagnostics.hpp"

namespace lss::coupling {

struct LotSaltCouplingConfig;

struct LotSaltSigmaThetaDiagnosticPoint {
  SigmaThetaBreakdownPoint breakdown;
  LotSaltPressureMapResult pressure_map;

  int wall_stress_gp_id = -1;
  int wall_stress_element_id = -1;
  int wall_stress_local_gp_id = -1;

  double wall_stress_r_m = 0.0;
  double wall_stress_z_m = 0.0;
  double wall_stress_depth_m = 0.0;

  double mean_stress_Pa = 0.0;
  double j2_Pa2 = 0.0;
  double von_mises_effective_stress_Pa = 0.0;
};

struct LotSaltSigmaThetaDiagnosticResult {
  std::vector<LotSaltSigmaThetaDiagnosticPoint> points;
  bool any_opened = false;
  bool valid = false;
  std::string pressure_source;
  std::string stress_source;
};

// Experimental opt-in diagnostic. SaltWallStressDiagnostics is a caller-owned
// snapshot; this function does not synchronize salt stress state with PKN time.
[[nodiscard]] LotSaltSigmaThetaDiagnosticResult
evaluate_lot_salt_sigma_theta_step(
    const lss::lot::PknResult& pkn_result,
    std::size_t step_index,
    const LotSaltCouplingConfig& config,
    const lss::salt::SaltWallStressDiagnostics& wall_stress);

// Applies the same wall-stress snapshot to each PKN time step. This is an
// experimental simplification until a future driver supplies per-step stresses.
[[nodiscard]] LotSaltSigmaThetaDiagnosticResult
evaluate_lot_salt_sigma_theta_series(
    const lss::lot::PknResult& pkn_result,
    const LotSaltCouplingConfig& config,
    const lss::salt::SaltWallStressDiagnostics& wall_stress);

}  // namespace lss::coupling
