#pragma once

#include "salt/SaltCreepTypes.hpp"

namespace lss::salt {

class SaltCreepInterface {
 public:
  virtual ~SaltCreepInterface() = default;

  [[nodiscard]] virtual bool is_available() const = 0;

  [[nodiscard]] virtual SaltCreepResponse evaluate_wall_response(
      const SaltCreepQuery& query) const = 0;
};

class NullSaltCreepInterface final : public SaltCreepInterface {
 public:
  [[nodiscard]] bool is_available() const override;

  [[nodiscard]] SaltCreepResponse evaluate_wall_response(
      const SaltCreepQuery& query) const override;
};

}  // namespace lss::salt
