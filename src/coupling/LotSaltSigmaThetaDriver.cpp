#include "coupling/LotSaltSigmaThetaDriver.hpp"

namespace lss::coupling {

LotSaltSigmaThetaDriverResult run_lot_salt_sigma_theta_experimental(
    const lss::core::CaseData& data,
    lss::salt::SaltCreepTimeBridge& bridge,
    const LotSaltCouplingConfigOptions& options) {
  LotSaltSigmaThetaDriverResult result;
  result.caveat =
      "experimental opt-in driver; wall stress is a caller-provided bridge "
      "snapshot and is not temporally synchronized with every PKN step";

  result.coupling_config =
      make_hydrostatic_lot_salt_coupling_config(data, options);
  result.pkn_run = lss::lot::run_pkn_case(data);
  result.wall_stress = bridge.wall_stress_diagnostics();
  result.diagnostic = evaluate_lot_salt_sigma_theta_series(
      result.pkn_run.result, result.coupling_config, result.wall_stress);
  result.valid = result.diagnostic.valid && result.wall_stress.valid;
  return result;
}

}  // namespace lss::coupling
