#pragma once

#include "salt/SaltCreepAdapterConfig.hpp"
#include "salt/SaltCreepAdapterState.hpp"
#include "salt/SaltCreepInterface.hpp"

#include <memory>

namespace lss::salt {

class SaltCreepSaltcreepAdapter final : public SaltCreepInterface {
 public:
  SaltCreepSaltcreepAdapter();
  explicit SaltCreepSaltcreepAdapter(SaltCreepAdapterConfig config);
  ~SaltCreepSaltcreepAdapter() override;

  SaltCreepSaltcreepAdapter(const SaltCreepSaltcreepAdapter&) = delete;
  SaltCreepSaltcreepAdapter& operator=(const SaltCreepSaltcreepAdapter&) =
      delete;
  SaltCreepSaltcreepAdapter(SaltCreepSaltcreepAdapter&&) noexcept;
  SaltCreepSaltcreepAdapter& operator=(SaltCreepSaltcreepAdapter&&) noexcept;

  [[nodiscard]] bool is_available() const override;

  [[nodiscard]] const SaltCreepAdapterConfig& config() const;
  [[nodiscard]] const SaltCreepAdapterState& state() const;
  [[nodiscard]] int backend_build_count() const;

  [[nodiscard]] SaltCreepResponse evaluate_wall_response(
      const SaltCreepQuery& query) const override;

  [[nodiscard]] static double radial_closure_from_displacement(
      double radial_displacement_m);

 private:
  struct BackendCache;

  [[nodiscard]] BackendCache& backend() const;

  SaltCreepAdapterConfig config_;
  // Logically const: evaluate_wall_response() does not change configuration or
  // physical model choices, but it records the latest backend response and
  // lazily initializes the cached backend objects.
  mutable SaltCreepAdapterState state_;
  mutable std::unique_ptr<BackendCache> backend_cache_;
  mutable int backend_build_count_ = 0;
};

}  // namespace lss::salt
