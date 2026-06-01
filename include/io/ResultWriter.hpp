#pragma once

#include <filesystem>
#include <string>

#include "lot/PknResult.hpp"

namespace lss::io {

void write_pkn_result(const std::filesystem::path& output_dir,
                      const std::string& case_id,
                      const lss::lot::PknResult& result);

}  // namespace lss::io
