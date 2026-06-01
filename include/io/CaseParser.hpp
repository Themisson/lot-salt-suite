#pragma once

#include <filesystem>

#include "core/types.hpp"

namespace lss::io {

lss::core::CaseData parse_yaml(const std::filesystem::path& path);

}  // namespace lss::io
