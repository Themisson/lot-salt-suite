#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "wellbore/AnnularVolume.hpp"

TEST_CASE("Annular volume uses legacy per-radian convention") {
  const double outer_radius_m = 0.20;
  const double inner_radius_m = 0.05;
  const double length_m = 10.0;

  const double per_radian = lss::wellbore::annular_volume_per_radian_m3(
      outer_radius_m, inner_radius_m, length_m);

  CHECK(per_radian == Catch::Approx(0.5 * (0.20 * 0.20 - 0.05 * 0.05) * 10.0));
}

TEST_CASE("Annular total volume is 2 pi times the per-radian volume") {
  const double per_radian =
      lss::wellbore::annular_volume_per_radian_m3(0.20, 0.05, 10.0);
  const double total = lss::wellbore::annular_total_volume_m3(0.20, 0.05, 10.0);

  CHECK(total == Catch::Approx(2.0 * 3.14159265358979323846 * per_radian));
}

TEST_CASE("Annular volume preserves no-drill-pipe behavior") {
  CHECK(lss::wellbore::annular_volume_per_radian_m3(0.20, 0.0, 10.0) ==
        Catch::Approx(0.5 * 0.20 * 0.20 * 10.0));
}

TEST_CASE("Annular volume rejects invalid geometry") {
  CHECK_THROWS_AS(lss::wellbore::annular_volume_per_radian_m3(0.0, 0.0, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::wellbore::annular_volume_per_radian_m3(0.1, -0.1, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::wellbore::annular_volume_per_radian_m3(0.1, 0.1, 1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::wellbore::annular_volume_per_radian_m3(0.2, 0.1, -1.0),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::wellbore::annular_volume_per_radian_m3(
                      std::numeric_limits<double>::infinity(), 0.0, 1.0),
                  std::invalid_argument);
}
