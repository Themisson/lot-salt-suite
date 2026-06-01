#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include <cmath>

#include "constitutive/edmt.hpp"
#include "constitutive/double_mechanism.hpp"
#include "io/CaseParser.hpp"

// ── Shared test parameters ────────────────────────────────────────────────────
static DMParams halita_dm() {
    DMParams p;
    p.e0_s     = 5.5556e-10;
    p.sig0     = 9.762e6;
    p.T0       = 359.15;
    p.n1       = 3.223;
    p.n2       = 7.562;
    p.Q_over_R = 50208.0 / 8.314;
    return p;
}

static EdmtParams transient_params(double K1 = 2.0, double K2 = 5.0) {
    EdmtParams p;
    p.K1 = K1;
    p.K2 = K2;
    return p;
}

// Pure deviatoric: σ_ef = sigma_ef exactly
static Stress make_deviatoric(double sigma_ef) {
    return Stress{2.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, -1.0/3.0*sigma_ef, 0.0};
}

// ── Tests ─────────────────────────────────────────────────────────────────────

TEST_CASE("EDMT: initial rate equals (1+K1) times DM rate", "[edmt]") {
    auto dm  = halita_dm();
    auto ep  = transient_params(2.0, 5.0);
    EDMT edmt(dm, ep, 20.4e9, 0.36, /*include_secondary=*/true);
    DoubleMechanism dm_model(dm, 20.4e9, 0.36);

    Stress sigma = make_deviatoric(20.0e6);
    InternalState s0;  // eps_v_eff = 0

    double rate_edmt = edmt.evaluate(sigma, s0, dm.T0, 1.0).strain_rate_voigt.norm();
    double rate_dm   = dm_model.evaluate(sigma, s0, dm.T0, 1.0).strain_rate_voigt.norm();

    // At eps_v_eff=0: rate_EDMT = (1 + K1) * rate_DM
    REQUIRE(rate_edmt == Catch::Approx(rate_dm * (1.0 + ep.K1)).epsilon(1e-6));
}

TEST_CASE("EDMT: rate decreases monotonically with accumulated strain", "[edmt]") {
    auto dm = halita_dm();
    EDMT edmt(dm, transient_params(2.0, 5.0), 20.4e9, 0.36, true);
    Stress sigma = make_deviatoric(20.0e6);

    InternalState state;
    double prev_rate = 1e30;
    const double dt = 1000.0;

    for (int step = 0; step < 20; ++step) {
        auto result = edmt.evaluate(sigma, state, dm.T0, dt);
        double rate = result.strain_rate_voigt.norm();
        REQUIRE(rate < prev_rate);
        prev_rate = rate;
        state = result.updated_state;
    }
}

TEST_CASE("EDMT: hardening variable increases monotonically", "[edmt]") {
    auto dm = halita_dm();
    EDMT edmt(dm, transient_params(2.0, 5.0), 20.4e9, 0.36, true);
    Stress sigma = make_deviatoric(20.0e6);

    InternalState state;
    const double dt = 1000.0;

    for (int step = 0; step < 20; ++step) {
        double eps_before = state.eps_v_eff;
        state = edmt.evaluate(sigma, state, dm.T0, dt).updated_state;
        REQUIRE(state.eps_v_eff > eps_before);
    }
}

TEST_CASE("EDMT: rate saturates to DM rate (< 1% error)", "[edmt]") {
    // Fundamental correctness: under constant σ and T, EDMT → DM in steady state.
    auto dm = halita_dm();
    auto ep = transient_params(2.0, 5.0);
    EDMT edmt(dm, ep, 20.4e9, 0.36, /*include_secondary=*/true);
    DoubleMechanism dm_model(dm, 20.4e9, 0.36);

    Stress sigma = make_deviatoric(20.0e6);
    InternalState state_ref;
    double rate_DM = dm_model.evaluate(sigma, state_ref, dm.T0, 1.0).strain_rate_voigt.norm();

    // Large dt: accumulate eps_v_eff >> 1/K2 = 0.2 to drive exp(-K2*eps)→0
    InternalState state;
    const double dt = 1e6;
    for (int step = 0; step < 200; ++step)
        state = edmt.evaluate(sigma, state, dm.T0, dt).updated_state;

    double rate_final = edmt.evaluate(sigma, state, dm.T0, dt).strain_rate_voigt.norm();
    double rel_err = std::abs(rate_final - rate_DM) / rate_DM;

    REQUIRE(rel_err < 0.01);  // < 1% — docs requirement
}

TEST_CASE("EDMT primary-only: rate at large eps is much smaller than initial", "[edmt]") {
    // With include_secondary=false: ε̇ = ε̇_DM · K1 · exp(−K2 · εv).
    // Verify that at very large εv (eps_v_eff >> 1/K2), the rate is negligible.
    auto dm = halita_dm();
    EDMT edmt_pri(dm, transient_params(2.0, 5.0), 20.4e9, 0.36, /*include_secondary=*/false);

    Stress sigma = make_deviatoric(20.0e6);

    // Initial rate (eps_v_eff = 0)
    InternalState s0;
    double rate_initial = edmt_pri.evaluate(sigma, s0, dm.T0, 1.0).strain_rate_voigt.norm();

    // Saturated rate at eps_v_eff = 100 >> 1/K2 = 0.2
    InternalState s_large;
    s_large.eps_v_eff = 100.0;  // K2*eps = 500 → exp(-500) ≈ 0
    double rate_large_eps = edmt_pri.evaluate(sigma, s_large, dm.T0, 1.0).strain_rate_voigt.norm();

    // Rate should be negligibly small relative to initial (factor = K1*exp(-K2*100))
    REQUIRE(rate_large_eps < rate_initial * 1e-20);
}

TEST_CASE("EDMT: DM regression, InternalState field does not break DM", "[edmt][regression]") {
    // DoubleMechanism must return the same rate regardless of eps_v_eff,
    // and must NOT modify the state (DM has no memory).
    auto dm = halita_dm();
    DoubleMechanism dm_model(dm, 20.4e9, 0.36);
    Stress sigma = make_deviatoric(dm.sig0);

    InternalState s_zero;           // eps_v_eff = 0
    InternalState s_large;          // eps_v_eff = 999 (arbitrary large value)
    s_large.eps_v_eff = 999.0;

    double r0   = dm_model.evaluate(sigma, s_zero,  dm.T0, 1.0).strain_rate_voigt.norm();
    double r999 = dm_model.evaluate(sigma, s_large, dm.T0, 1.0).strain_rate_voigt.norm();

    // DM is memoryless — state must not affect result
    REQUIRE(r0 == Catch::Approx(r999).epsilon(1e-12));

    // State must be returned unchanged by DM
    auto res = dm_model.evaluate(sigma, s_zero, dm.T0, 1.0);
    REQUIRE(res.updated_state.eps_v_eff == Catch::Approx(0.0).margin(1e-30));
}
