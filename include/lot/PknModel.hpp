#pragma once

#include "lot/PknInput.hpp"
#include "lot/PknResult.hpp"

namespace lss::lot {

class PknModel {
 public:
  [[nodiscard]] PknResult evaluate(const PknInput& input, double elapsed_time_s) const;
  [[nodiscard]] PknResult simulate(const PknInput& input) const;
};

}  // namespace lss::lot
