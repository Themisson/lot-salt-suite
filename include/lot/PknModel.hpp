#pragma once

#include "lot/PknInput.hpp"
#include "lot/PknResult.hpp"

namespace lss::lot {

[[nodiscard]] double effectiveCompressibility(double fluid_compressibility,
                                              double geometric_compressibility);

[[nodiscard]] double volumetricPressureIncrement(double dV_effective,
                                                 double annular_volume,
                                                 double effective_compressibility);

class PknModel {
 public:
  [[nodiscard]] PknResult evaluate(const PknInput& input, double elapsed_time_s) const;
  [[nodiscard]] PknResult simulate(const PknInput& input) const;
};

}  // namespace lss::lot
