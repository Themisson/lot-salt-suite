#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <cmath>
#include <memory>
#include <vector>

#include "constitutive/dilatancy_envelope.hpp"
#include "constitutive/motta_v1.hpp"
#include "io/CaseParser.hpp"

namespace {
Stress make_triaxial(double mean_comp, double sqrt_j2) {
    const double q = std::sqrt(3.0) * sqrt_j2;
    const double sigma_ax = -(mean_comp + 2.0*q/3.0);
    const double sigma_rad = -(mean_comp - q/3.0);
    return Stress{sigma_rad, sigma_rad, sigma_ax, 0.0};
}

MottaV1Params motta_params() {
    MottaV1Params p;
    p.n_d = 2.0;
    p.A_d = 1.0e-10;
    p.m_d = 1.0;
    p.p_d = 0.0;
    p.D_max = 0.99;
    return p;
}

DMParams dm_params() {
    DMParams p;
    p.e0_s = 1.0e-12;
    p.sig0 = 1.0e6;
    p.T0 = 300.0;
    p.n1 = 3.0;
    p.n2 = 5.0;
    p.Q_over_R = 0.0;
    return p;
}

double eval_threshold(DilatancyEnvelope& envelope, double mean_comp, double sqrt_j2) {
    return envelope.evaluate(make_triaxial(mean_comp, sqrt_j2));
}
} // namespace

TEST_CASE("Dilatancy envelopes: hydrostatic compression is safe",
          "[dilatancy][sign]") {
    SpierEnvelope spier(SpierParams{0.25, 0.0});
    RatiganEnvelope ratigan(RatiganParams{0.81, 0.0, 1.0});
    DeVriesEnvelope devries(DeVriesParams{10.0e6, 1.0, 30.0e6});
    HunscheEnvelope hunsche(HunscheParams{10.0e6, 30.0e6, 1.0});

    const Stress hydro{-30.0e6, -30.0e6, -30.0e6, 0.0};
    REQUIRE(spier.evaluate(hydro) < 0.0);
    REQUIRE(ratigan.evaluate(hydro) < 0.0);
    REQUIRE(devries.evaluate(hydro) < 0.0);
    REQUIRE(hunsche.evaluate(hydro) < 0.0);
}

TEST_CASE("Dilatancy envelopes: each criterion fires at its configured level",
          "[dilatancy][threshold]") {
    const double mean = 10.0e6; // I1_comp = 30 MPa

    SpierEnvelope spier(SpierParams{0.25, 0.0});
    REQUIRE(eval_threshold(spier, mean, 7.49e6) < 0.0);
    REQUIRE(eval_threshold(spier, mean, 7.51e6) > 0.0);

    RatiganEnvelope ratigan(RatiganParams{0.81, 0.0, 1.0});
    REQUIRE(eval_threshold(ratigan, mean, 24.29e6) < 0.0);
    REQUIRE(eval_threshold(ratigan, mean, 24.31e6) > 0.0);

    DeVriesEnvelope devries(DeVriesParams{10.0e6, 1.0, 30.0e6});
    const double devries_limit = 10.0e6 * std::sinh(1.0);
    REQUIRE(eval_threshold(devries, mean, devries_limit - 1.0e4) < 0.0);
    REQUIRE(eval_threshold(devries, mean, devries_limit + 1.0e4) > 0.0);

    HunscheEnvelope hunsche(HunscheParams{10.0e6, 30.0e6, 1.0});
    REQUIRE(eval_threshold(hunsche, mean, 9.99e6) < 0.0);
    REQUIRE(eval_threshold(hunsche, mean, 10.01e6) > 0.0);
}

TEST_CASE("Dilatancy factory: YAML envelope name selects concrete implementation",
          "[dilatancy][parser]") {
    CaseData cd;
    cd.creep.dilatancy_envelope = "Ratigan";
    auto ratigan = make_dilatancy_envelope(cd);
    REQUIRE(ratigan->name() == "Ratigan");

    cd.creep.dilatancy_envelope = "DeVries";
    auto devries = make_dilatancy_envelope(cd);
    REQUIRE(devries->name() == "DeVries");

    cd.creep.dilatancy_envelope = "Hunsche";
    auto hunsche = make_dilatancy_envelope(cd);
    REQUIRE(hunsche->name() == "Hunsche");
}

TEST_CASE("MottaV1: damage curves diverge with different envelopes",
          "[dilatancy][motta][damage]") {
    const DMParams dm = dm_params();
    const MottaV1Params motta = motta_params();
    const Stress stress = make_triaxial(10.0e6, 12.0e6);
    const double T = 300.0;
    const double dt = 1.0;

    std::vector<std::unique_ptr<MottaV1>> models;
    models.push_back(std::make_unique<MottaV1>(
        dm, motta, std::make_unique<SpierEnvelope>(SpierParams{0.25, 0.0}), 20.0e9, 0.30));
    models.push_back(std::make_unique<MottaV1>(
        dm, motta, std::make_unique<RatiganEnvelope>(RatiganParams{0.81, 0.0, 1.0}), 20.0e9, 0.30));
    models.push_back(std::make_unique<MottaV1>(
        dm, motta, std::make_unique<DeVriesEnvelope>(DeVriesParams{10.0e6, 1.0, 30.0e6}), 20.0e9, 0.30));
    models.push_back(std::make_unique<MottaV1>(
        dm, motta, std::make_unique<HunscheEnvelope>(HunscheParams{10.0e6, 30.0e6, 1.0}), 20.0e9, 0.30));

    std::vector<double> final_D;
    for (const auto& model : models) {
        InternalState state;
        for (int i = 0; i < 50; ++i)
            state = model->evaluate(stress, state, T, dt).updated_state;
        final_D.push_back(state.damage_D);
    }

    REQUIRE(final_D[0] > final_D[3]);
    REQUIRE(final_D[3] > final_D[2]);
    REQUIRE(final_D[2] > final_D[1]);
    REQUIRE(final_D[1] == Catch::Approx(0.0).margin(1.0e-30));
}
