#include <stdexcept>

#include <catch2/catch_test_macros.hpp>

#include "lot/SaltDisplacementMode.hpp"

TEST_CASE("Salt displacement pre_iterative calls solver once per layer") {
  const auto result = lss::lot::plan_salt_displacement_execution(
      lss::lot::SaltDisplacementMode::PreIterative, {4, 7});

  CHECK(result.solve_calls == 4);
  CHECK(result.pre_iterative);
  CHECK_FALSE(result.legacy_inside_newton_preserved);
}

TEST_CASE("Salt displacement legacy_inside_newton preserves per-iteration calls") {
  const auto result = lss::lot::plan_salt_displacement_execution(
      lss::lot::SaltDisplacementMode::LegacyInsideNewton, {4, 7});

  CHECK(result.solve_calls == 28);
  CHECK(result.legacy_inside_newton_preserved);
  CHECK_FALSE(result.pre_iterative);
}

TEST_CASE("Salt displacement parser accepts supported modes") {
  CHECK(lss::lot::parse_salt_displacement_mode("pre_iterative") ==
        lss::lot::SaltDisplacementMode::PreIterative);
  CHECK(lss::lot::parse_salt_displacement_mode("legacy_inside_newton") ==
        lss::lot::SaltDisplacementMode::LegacyInsideNewton);
  CHECK(lss::lot::to_string(lss::lot::SaltDisplacementMode::PreIterative) ==
        "pre_iterative");
}

TEST_CASE("Salt displacement parser rejects invalid mode") {
  CHECK_THROWS_AS(lss::lot::parse_salt_displacement_mode("inside_picard"),
                  std::invalid_argument);
}

TEST_CASE("Salt displacement rejects negative counts") {
  CHECK_THROWS_AS(lss::lot::plan_salt_displacement_execution(
                      lss::lot::SaltDisplacementMode::PreIterative, {-1, 1}),
                  std::invalid_argument);
  CHECK_THROWS_AS(lss::lot::plan_salt_displacement_execution(
                      lss::lot::SaltDisplacementMode::LegacyInsideNewton,
                      {1, -1}),
                  std::invalid_argument);
}
