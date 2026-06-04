#pragma once

#include <string>

#include "core/types.hpp"
#include "coupling/LotSaltCouplingConfigBuilder.hpp"
#include "coupling/LotSaltSigmaThetaDiagnostic.hpp"
#include "lot/PknRunner.hpp"
#include "salt/SaltCreepTimeBridge.hpp"
#include "salt/SaltWallStressDiagnostics.hpp"

namespace lss::coupling {

struct LotSaltSigmaThetaDriverResult {
  lss::lot::PknRun pkn_run;
  LotSaltCouplingConfig coupling_config;
  lss::salt::SaltWallStressDiagnostics wall_stress;
  LotSaltSigmaThetaDiagnosticResult diagnostic;

  bool valid = false;
  std::string caveat;
};

// Experimental opt-in driver. The bridge is supplied by the caller and is used
// only as a current-state stress snapshot source; this function does not advance
// salt time or synchronize salt stresses with each PKN step.
[[nodiscard]] LotSaltSigmaThetaDriverResult
run_lot_salt_sigma_theta_experimental(
    const lss::core::CaseData& data,
    lss::salt::SaltCreepTimeBridge& bridge,
    const LotSaltCouplingConfigOptions& options = {});

}  // namespace lss::coupling
