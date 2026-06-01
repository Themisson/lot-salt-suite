#pragma once

#include "lot/LotTypes.hpp"

namespace lss::lot {

struct LeakoffConfig {
  bool enabled = false;
  LeakoffModel model = LeakoffModel::None;
};

}  // namespace lss::lot
