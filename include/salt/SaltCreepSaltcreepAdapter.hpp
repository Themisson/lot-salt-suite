#pragma once

#include "salt/SaltCreepInterface.hpp"

namespace lss::salt {

class SaltCreepSaltcreepAdapter final : public SaltCreepInterface {
 public:
  [[nodiscard]] bool is_available() const override;

  [[nodiscard]] SaltCreepResponse evaluate_wall_response(
      const SaltCreepQuery& query) const override;

  [[nodiscard]] static double radial_closure_from_displacement(
      double radial_displacement_m);
};

}  // namespace lss::salt
