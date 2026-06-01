#pragma once

#include <memory>
#include <string>

#include "io/CaseParser.hpp"
#include "types.hpp"

// Dilatancy onset criteria used by tertiary damage models.
//
// Stress convention: code stresses are tension-positive, so hydrostatic
// compression has I1 < 0. The envelope formulas use I1_comp = -I1 where
// confinement should raise the dilatancy threshold.
class DilatancyEnvelope {
public:
    virtual ~DilatancyEnvelope() = default;

    virtual double dilatancy_function(double I1, double J2) const = 0;
    virtual std::string name() const = 0;

    double evaluate(const Stress& sigma) const;
};

class SpierEnvelope final : public DilatancyEnvelope {
public:
    explicit SpierEnvelope(const SpierParams& params);

    double dilatancy_function(double I1, double J2) const override;
    std::string name() const override { return "Spier"; }

private:
    SpierParams params_;
};

class RatiganEnvelope final : public DilatancyEnvelope {
public:
    explicit RatiganEnvelope(const RatiganParams& params);

    double dilatancy_function(double I1, double J2) const override;
    std::string name() const override { return "Ratigan"; }

private:
    RatiganParams params_;
};

class DeVriesEnvelope final : public DilatancyEnvelope {
public:
    explicit DeVriesEnvelope(const DeVriesParams& params);

    double dilatancy_function(double I1, double J2) const override;
    std::string name() const override { return "DeVries"; }

private:
    DeVriesParams params_;
};

class HunscheEnvelope final : public DilatancyEnvelope {
public:
    explicit HunscheEnvelope(const HunscheParams& params);

    double dilatancy_function(double I1, double J2) const override;
    std::string name() const override { return "Hunsche"; }

private:
    HunscheParams params_;
};

using HuenscheEnvelope = HunscheEnvelope;

std::unique_ptr<DilatancyEnvelope> make_dilatancy_envelope(const CaseData& cd);
