#pragma once

#include "salt/SaltCreepAdapterConfig.hpp"
#include "salt/SaltCreepAdapterState.hpp"
#include "salt/SaltCreepInterface.hpp"

namespace lss::salt {

class SaltCreepSaltcreepAdapter final : public SaltCreepInterface {
 public:
  SaltCreepSaltcreepAdapter();
  explicit SaltCreepSaltcreepAdapter(SaltCreepAdapterConfig config);

  [[nodiscard]] bool is_available() const override;

  [[nodiscard]] const SaltCreepAdapterConfig& config() const;
  [[nodiscard]] const SaltCreepAdapterState& state() const;

  [[nodiscard]] SaltCreepResponse evaluate_wall_response(
      const SaltCreepQuery& query) const override;

  [[nodiscard]] static double radial_closure_from_displacement(
      double radial_displacement_m);

 private:
  SaltCreepAdapterConfig config_;
  // Logically const: evaluate_wall_response() does not change configuration or
  // physical model choices, but it records the latest backend response.
  mutable SaltCreepAdapterState state_;
};

}  // namespace lss::salt
