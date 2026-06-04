#include <limits>
#include <stdexcept>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include "coupling/LotSaltHydrostaticContext.hpp"
#include "units/units.hpp"

namespace {

lss::core::CaseData make_case_data() {
  lss::core::CaseData data;
  data.lot.enabled = true;
  data.lot.shoe_depth_m = 3000.0;

  lss::core::FluidData fluid;
  fluid.id = "mud";
  fluid.density_kg_m3 = 1200.0;
  data.fluids.push_back(fluid);

  lss::core::AnnularData annular;
  annular.id = "annulus_a";
  annular.fluid_id = "mud";
  annular.top_m = 0.0;
  annular.base_m = 3000.0;
  data.annulars.push_back(annular);

  return data;
}

}  // namespace

TEST_CASE("LotSaltHydrostaticContext derives pressure for a single annular") {
  const auto data = make_case_data();

  const auto context =
      lss::coupling::make_lot_salt_hydrostatic_context(data);

  CHECK(context.depth_m == Catch::Approx(3000.0));
  CHECK(context.density_kg_m3 == Catch::Approx(1200.0));
  CHECK(context.hydrostatic_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(1200.0, 3000.0)));
  CHECK(context.annular_index == 0);
  CHECK(context.fluid_id == "mud");
  CHECK(context.source ==
        "lot.shoe_depth_m + annular.fluid_id + fluid.density_kg_m3");
}

TEST_CASE("LotSaltHydrostaticContext selects fluid referenced by annular") {
  auto data = make_case_data();

  lss::core::FluidData brine;
  brine.id = "brine";
  brine.density_kg_m3 = 1050.0;
  data.fluids.push_back(brine);

  data.annulars.front().fluid_id = "brine";

  const auto context =
      lss::coupling::make_lot_salt_hydrostatic_context(data);

  CHECK(context.fluid_id == "brine");
  CHECK(context.density_kg_m3 == Catch::Approx(1050.0));
  CHECK(context.hydrostatic_pressure_Pa ==
        Catch::Approx(units::hydrostatic_pressure_Pa(1050.0, 3000.0)));
}

TEST_CASE("LotSaltHydrostaticContext selects annular containing shoe depth") {
  auto data = make_case_data();
  data.lot.shoe_depth_m = 2500.0;
  data.annulars.clear();

  lss::core::AnnularData shallow;
  shallow.id = "shallow";
  shallow.fluid_id = "mud";
  shallow.top_m = 0.0;
  shallow.base_m = 1000.0;
  data.annulars.push_back(shallow);

  lss::core::AnnularData deep;
  deep.id = "deep";
  deep.fluid_id = "mud";
  deep.top_m = 1000.0;
  deep.base_m = 3000.0;
  data.annulars.push_back(deep);

  const auto context =
      lss::coupling::make_lot_salt_hydrostatic_context(data);

  CHECK(context.annular_index == 1);
  CHECK(context.depth_m == Catch::Approx(2500.0));
}

TEST_CASE("LotSaltHydrostaticContext rejects missing annular at shoe") {
  auto data = make_case_data();
  data.lot.shoe_depth_m = 4000.0;

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltHydrostaticContext rejects ambiguous annulars at shoe") {
  auto data = make_case_data();

  lss::core::AnnularData overlapping;
  overlapping.id = "annulus_b";
  overlapping.fluid_id = "mud";
  overlapping.top_m = 1000.0;
  overlapping.base_m = 3500.0;
  data.annulars.push_back(overlapping);

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltHydrostaticContext rejects missing referenced fluid") {
  auto data = make_case_data();
  data.annulars.front().fluid_id = "missing";

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltHydrostaticContext rejects invalid fluid density") {
  auto data = make_case_data();
  data.fluids.front().density_kg_m3 = -1.0;

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);

  data.fluids.front().density_kg_m3 =
      std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);

  data.fluids.front().density_kg_m3 = std::numeric_limits<double>::infinity();
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);
}

TEST_CASE("LotSaltHydrostaticContext rejects invalid shoe depth") {
  auto data = make_case_data();
  data.lot.shoe_depth_m = 0.0;

  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);

  data.lot.shoe_depth_m = -1.0;
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);

  data.lot.shoe_depth_m = std::numeric_limits<double>::quiet_NaN();
  CHECK_THROWS_AS(lss::coupling::make_lot_salt_hydrostatic_context(data),
                  std::invalid_argument);
}
