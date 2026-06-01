#include <stdexcept>
#include <vector>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "lot/BreakdownDetector.hpp"

TEST_CASE("Derivative drop detector returns not found for monotonic linear curve") {
  const lss::lot::BreakdownDetector detector;
  const std::vector<double> time_s{0.0, 1.0, 2.0, 3.0, 4.0};
  const std::vector<double> volume_m3{0.0, 1.0, 2.0, 3.0, 4.0};
  const std::vector<double> pressure_Pa{0.0, 10.0, 20.0, 30.0, 40.0};

  const auto result = detector.detect_derivative_drop(time_s, volume_m3, pressure_Pa);

  CHECK_FALSE(result.found);
  CHECK(result.method == "derivative_drop");
}

TEST_CASE("Derivative drop detector finds clear slope change") {
  const lss::lot::BreakdownDetector detector;
  const std::vector<double> time_s{0.0, 1.0, 2.0, 3.0, 4.0, 5.0};
  const std::vector<double> volume_m3{0.0, 1.0, 2.0, 3.0, 4.0, 5.0};
  const std::vector<double> pressure_Pa{0.0, 10.0, 20.0, 30.0, 32.0, 34.0};

  const auto result = detector.detect_derivative_drop(time_s, volume_m3, pressure_Pa);

  REQUIRE(result.found);
  CHECK(result.breakdown_index == 4);
  CHECK(result.breakdown_time_s == Catch::Approx(4.0));
  CHECK(result.breakdown_volume_m3 == Catch::Approx(4.0));
  CHECK(result.breakdown_pressure_Pa == Catch::Approx(32.0));
  CHECK(result.confidence > 0.0);
}

TEST_CASE("Derivative drop detector rejects mismatched vector sizes") {
  const lss::lot::BreakdownDetector detector;
  const std::vector<double> time_s{0.0, 1.0, 2.0, 3.0};
  const std::vector<double> volume_m3{0.0, 1.0, 2.0};
  const std::vector<double> pressure_Pa{0.0, 10.0, 20.0, 30.0};

  CHECK_THROWS_AS(detector.detect_derivative_drop(time_s, volume_m3, pressure_Pa),
                  std::invalid_argument);
}

TEST_CASE("Derivative drop detector rejects fewer than minimum points") {
  const lss::lot::BreakdownDetector detector;
  const std::vector<double> time_s{0.0, 1.0, 2.0};
  const std::vector<double> volume_m3{0.0, 1.0, 2.0};
  const std::vector<double> pressure_Pa{0.0, 10.0, 20.0};

  CHECK_THROWS_AS(detector.detect_derivative_drop(time_s, volume_m3, pressure_Pa),
                  std::invalid_argument);
}

TEST_CASE("Derivative drop detector preserves SI pressure and volume") {
  const lss::lot::BreakdownDetector detector;
  const std::vector<double> time_s{0.0, 10.0, 20.0, 30.0, 40.0, 50.0};
  const std::vector<double> volume_m3{0.0, 0.01, 0.02, 0.03, 0.04, 0.05};
  const std::vector<double> pressure_Pa{10000000.0, 20000000.0, 30000000.0,
                                        40000000.0, 40500000.0, 41000000.0};

  const auto result = detector.detect_derivative_drop(time_s, volume_m3, pressure_Pa);

  REQUIRE(result.found);
  CHECK(result.breakdown_volume_m3 == Catch::Approx(0.04));
  CHECK(result.breakdown_pressure_Pa == Catch::Approx(40500000.0));
}
