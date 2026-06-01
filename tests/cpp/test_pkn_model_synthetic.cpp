#include <cmath>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/PknModel.hpp"

namespace {

lss::lot::PknInput synthetic_input() {
  lss::lot::PknInput input;
  input.injection.rate_m3_s = 0.001;
  input.injection.total_time_s = 100.0;
  input.injection.dt_s = 10.0;
  input.fracture_height_m = 20.0;
  input.initial_width_m = 0.0;
  input.net_pressure_Pa = 1000000.0;
  return input;
}

}  // namespace

TEST_CASE("Synthetic PKN model returns non-negative finite values") {
  const lss::lot::PknModel model;
  const auto result = model.evaluate(synthetic_input(), 100.0);

  CHECK(result.width_m >= 0.0);
  CHECK(result.length_m >= 0.0);
  CHECK(result.volume_m3 >= 0.0);
  CHECK(result.net_pressure_Pa >= 0.0);
  CHECK(std::isfinite(result.width_m));
  CHECK(std::isfinite(result.length_m));
  CHECK(std::isfinite(result.volume_m3));
  CHECK(std::isfinite(result.net_pressure_Pa));
}

TEST_CASE("Synthetic PKN model volume is monotonic with elapsed time") {
  const lss::lot::PknModel model;
  const auto input = synthetic_input();

  const auto early = model.evaluate(input, 10.0);
  const auto late = model.evaluate(input, 100.0);

  CHECK(late.volume_m3 >= early.volume_m3);
  CHECK(late.length_m >= early.length_m);
}

TEST_CASE("Synthetic PKN model clamps negative net pressure to zero") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.net_pressure_Pa = -1.0;

  const auto result = model.evaluate(input, 10.0);

  CHECK(result.net_pressure_Pa == Catch::Approx(0.0));
}

TEST_CASE("Synthetic PKN model rejects invalid dimensions") {
  const lss::lot::PknModel model;
  auto input = synthetic_input();
  input.fracture_height_m = 0.0;

  CHECK_THROWS_AS(model.evaluate(input, 10.0), std::invalid_argument);
}
