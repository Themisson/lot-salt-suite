#pragma once

#include "core/types.hpp"
#include "lot/PknInput.hpp"
#include "lot/PknResult.hpp"

namespace lss::lot {

struct PknRun {
  PknInput input;
  PknResult result;
};

[[nodiscard]] PknInput make_pkn_input(const lss::core::CaseData& data);
[[nodiscard]] PknRun run_pkn_case(const lss::core::CaseData& data);

}  // namespace lss::lot
