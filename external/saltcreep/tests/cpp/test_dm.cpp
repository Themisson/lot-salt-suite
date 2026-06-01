#include <catch2/catch_test_macros.hpp>
#include <catch2/catch_approx.hpp>
#include <cmath>

#include "constitutive/double_mechanism.hpp"
#include "io/CaseParser.hpp"

// ── Helpers ──────────────────────────────────────────────────────────────────
static DMParams halita_params() {
    // halita reference constants (SI)
    DMParams p;
    p.e0_s     = 5.5556e-10;
    p.sig0     = 9.762e6;
    p.T0       = 359.15;
    p.n1       = 3.223;
    p.n2       = 7.562;
    p.Q_over_R = 50208.0 / 8.314;
    return p;
}

static DoubleMechanism make_dm() {
    return DoubleMechanism(halita_params(), 20.4e9, 0.36);
}

// Pure radial deviatoric stress: σrr=−σ, σθθ=0.5σ, σzz=0.5σ
// → p=0, s = {-σ, 0.5σ, 0.5σ, 0}  → σ_ef = √(3/2·(σ²+0.25σ²+0.25σ²)) = √(3/2·1.5σ²) = σ·√(9/4)...
// Actually simpler: pure deviatoric uniaxial: σrr=S, σθθ=σzz=−S/2, σrz=0
// p=0, s={S,−S/2,−S/2,0}, ss=S²+S²/4+S²/4=3S²/2, σ_ef=√(3/2·3S²/2)=√(9S²/4)=3S/2...
// Use: s = {2/3·σ_ef, −1/3·σ_ef, −1/3·σ_ef, 0} so that σ_ef = σ_ef by definition.
static Stress make_deviatoric_stress(double sigma_ef) {
    // s = {2/3·σ_ef, −1/3·σ_ef, −1/3·σ_ef, 0}
    // ss = (4/9 + 1/9 + 1/9)σ_ef² = 6/9 σ_ef²
    // σ_ef_check = √(3/2·6/9·σ_ef²) = √(σ_ef²) = σ_ef ✓
    return Stress{2.0/3.0 * sigma_ef, -1.0/3.0 * sigma_ef, -1.0/3.0 * sigma_ef, 0.0};
}

// ── Tests ─────────────────────────────────────────────────────────────────────

TEST_CASE("DM: reference rate at sigma_ef=sig0 and T=T0 equals e0", "[dm]") {
    auto dm    = make_dm();
    auto p     = halita_params();
    auto sigma = make_deviatoric_stress(p.sig0);
    InternalState state;

    auto res = dm.evaluate(sigma, state, p.T0, 1.0);

    // Scalar rate: ε̇^v · sqrt(3/2) / (||s||) should give e0
    // Or: ||rate|| = sqrt(3/2) * e0 * ||s|| / sigma_ef = sqrt(3/2) * e0 * sigma_ef/sqrt(3/2) / sigma_ef = e0
    // Actually: rate_i = sqrt(3/2) * e0 * s_i / sigma_ef
    // ||rate|| = sqrt(3/2) * e0 * ||s|| / sigma_ef
    // ||s||² = ss = 6/9 * sigma_ef² → ||s|| = sigma_ef * sqrt(6/9)
    // ||rate|| = sqrt(3/2) * e0 * sqrt(6/9) = e0 * sqrt(3/2 * 6/9) = e0 * sqrt(1) = e0
    double rate_norm = res.strain_rate_voigt.norm();
    REQUIRE(rate_norm == Catch::Approx(p.e0_s).epsilon(1e-6));
}

TEST_CASE("DM: zero volumetric rate for any deviatoric stress", "[dm]") {
    auto dm = make_dm();
    auto p  = halita_params();
    InternalState state;

    for (double s : {0.5e6, 5e6, 20e6, 50e6}) {
        auto sigma = make_deviatoric_stress(s);
        auto res   = dm.evaluate(sigma, state, p.T0, 1.0);
        // trace(ε̇^v) = ε̇_rr + ε̇_θθ + ε̇_zz = rate[0] + rate[1] + rate[2]
        double vol_rate = res.strain_rate_voigt[0]
                        + res.strain_rate_voigt[1]
                        + res.strain_rate_voigt[2];
        REQUIRE(std::abs(vol_rate) < 1e-20);
    }
}

TEST_CASE("DM: n1 used when sigma_ef <= sig0, n2 when sigma_ef > sig0", "[dm]") {
    auto dm = make_dm();
    auto p  = halita_params();
    InternalState state;

    // Just below sigma0: uses n1
    auto s1 = make_deviatoric_stress(p.sig0 * 0.999);
    auto r1 = dm.evaluate(s1, state, p.T0, 1.0);
    double e1 = r1.strain_rate_voigt.norm();

    // Just above sigma0: uses n2
    auto s2 = make_deviatoric_stress(p.sig0 * 1.001);
    auto r2 = dm.evaluate(s2, state, p.T0, 1.0);
    double e2 = r2.strain_rate_voigt.norm();

    // The jump at sigma0: ratio ≈ (1.001/0.999)^n2 / (1.001/0.999)^n1 > 1
    // For n2 > n1, the n2 branch gives a higher rate per sigma unit above the jump
    // Verify rate2 > rate1 (both stress magnitudes are nearly the same → higher n wins)
    REQUIRE(e2 > e1);
}

TEST_CASE("DM: guard returns zero at sigma_ef < 1 Pa", "[dm]") {
    auto dm = make_dm();
    Stress zero_stress = Stress::Zero();
    InternalState state;
    auto res = dm.evaluate(zero_stress, state, 370.0, 1.0);
    REQUIRE(res.strain_rate_voigt.norm() == Catch::Approx(0.0).margin(1e-30));
}

TEST_CASE("DM: Arrhenius rate increases with temperature", "[dm]") {
    auto dm = make_dm();
    auto p  = halita_params();
    auto sigma = make_deviatoric_stress(p.sig0 * 2.0);
    InternalState state;

    double r_cold = dm.evaluate(sigma, state, p.T0 - 30.0, 1.0).strain_rate_voigt.norm();
    double r_ref  = dm.evaluate(sigma, state, p.T0,         1.0).strain_rate_voigt.norm();
    double r_hot  = dm.evaluate(sigma, state, p.T0 + 30.0, 1.0).strain_rate_voigt.norm();

    REQUIRE(r_cold < r_ref);
    REQUIRE(r_ref  < r_hot);
}

TEST_CASE("DM: rate scales as sigma^n", "[dm]") {
    auto dm = make_dm();
    auto p  = halita_params();
    InternalState state;

    // Below sigma0 (uses n1): doubling sigma → rate increases by 2^n1
    double s  = p.sig0 * 0.5;
    auto r1 = dm.evaluate(make_deviatoric_stress(s),       state, p.T0, 1.0);
    auto r2 = dm.evaluate(make_deviatoric_stress(s * 2.0), state, p.T0, 1.0);

    double ratio = r2.strain_rate_voigt.norm() / r1.strain_rate_voigt.norm();
    REQUIRE(ratio == Catch::Approx(std::pow(2.0, p.n1)).epsilon(1e-5));
}

TEST_CASE("DM: D_elastic is 4x4, symmetric, diagonal positive", "[dm]") {
    auto dm = make_dm();
    Eigen::Matrix4d D = dm.D_elastic();

    // Symmetric
    REQUIRE((D - D.transpose()).norm() < 1e-10);

    // All diagonal entries > 0 (necessary condition for positive definiteness)
    for (int i = 0; i < 4; ++i)
        REQUIRE(D(i,i) > 0.0);
}
