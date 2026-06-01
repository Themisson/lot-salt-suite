#include "constitutive/dilatancy_envelope.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace {
Stress deviatoric(const Stress& sigma) {
    const double p = (sigma[0] + sigma[1] + sigma[2]) / 3.0;
    Stress s = sigma;
    s[0] -= p;
    s[1] -= p;
    s[2] -= p;
    return s;
}

double sqrt_j2(double J2) {
    return std::sqrt(std::max(0.0, J2));
}

double confinement_from_I1(double I1) {
    return std::max(0.0, -I1);
}

void require_positive(double value, const char* label) {
    if (!(value > 0.0))
        throw std::invalid_argument(std::string(label) + " must be positive");
}
} // namespace

double DilatancyEnvelope::evaluate(const Stress& sigma) const {
    const Stress s = deviatoric(sigma);
    const double J2 = 0.5 * (s[0]*s[0] + s[1]*s[1] + s[2]*s[2] + 2.0*s[3]*s[3]);
    const double I1 = sigma[0] + sigma[1] + sigma[2];
    return dilatancy_function(I1, J2);
}

SpierEnvelope::SpierEnvelope(const SpierParams& params)
    : params_(params) {
    if (params_.a < 0.0 || params_.b_Pa < 0.0)
        throw std::invalid_argument("SpierEnvelope: parameters must be non-negative");
}

double SpierEnvelope::dilatancy_function(double I1, double J2) const {
    return sqrt_j2(J2) + params_.a * I1 - params_.b_Pa;
}

RatiganEnvelope::RatiganEnvelope(const RatiganParams& params)
    : params_(params) {
    if (params_.c < 0.0 || params_.d_Pa < 0.0)
        throw std::invalid_argument("RatiganEnvelope: c and d_Pa must be non-negative");
    require_positive(params_.m, "RatiganEnvelope: m");
}

double RatiganEnvelope::dilatancy_function(double I1, double J2) const {
    const double I1_comp = confinement_from_I1(I1);
    const double threshold = params_.c * std::pow(I1_comp + params_.d_Pa, params_.m);
    return sqrt_j2(J2) - threshold;
}

DeVriesEnvelope::DeVriesEnvelope(const DeVriesParams& params)
    : params_(params) {
    if (params_.e_Pa < 0.0 || params_.f < 0.0)
        throw std::invalid_argument("DeVriesEnvelope: e_Pa and f must be non-negative");
    require_positive(params_.sigma0_Pa, "DeVriesEnvelope: sigma0_Pa");
}

double DeVriesEnvelope::dilatancy_function(double I1, double J2) const {
    const double I1_comp = confinement_from_I1(I1);
    const double threshold = params_.e_Pa * std::sinh(params_.f * I1_comp / params_.sigma0_Pa);
    return sqrt_j2(J2) - threshold;
}

HunscheEnvelope::HunscheEnvelope(const HunscheParams& params)
    : params_(params) {
    if (params_.g_Pa < 0.0)
        throw std::invalid_argument("HunscheEnvelope: g_Pa must be non-negative");
    require_positive(params_.I1_ref_Pa, "HunscheEnvelope: I1_ref_Pa");
    require_positive(params_.h, "HunscheEnvelope: h");
}

double HunscheEnvelope::dilatancy_function(double I1, double J2) const {
    const double I1_comp = confinement_from_I1(I1);
    const double threshold = params_.g_Pa * std::pow(I1_comp / params_.I1_ref_Pa, params_.h);
    return sqrt_j2(J2) - threshold;
}

std::unique_ptr<DilatancyEnvelope> make_dilatancy_envelope(const CaseData& cd) {
    const std::string& type = cd.creep.dilatancy_envelope;
    if (type == "Spier")
        return std::make_unique<SpierEnvelope>(cd.spier);
    if (type == "Ratigan")
        return std::make_unique<RatiganEnvelope>(cd.ratigan);
    if (type == "DeVries")
        return std::make_unique<DeVriesEnvelope>(cd.devries);
    if (type == "Hunsche" || type == "Huensche")
        return std::make_unique<HunscheEnvelope>(cd.hunsche);
    throw std::runtime_error("unknown dilatancy_envelope: " + type);
}
