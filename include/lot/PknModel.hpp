#pragma once

#include "lot/PknInput.hpp"
#include "lot/PknResult.hpp"

namespace lss::lot {

[[nodiscard]] double effectiveCompressibility(double fluid_compressibility,
                                              double geometric_compressibility);

[[nodiscard]] double elasticAnnularGeometricCompressibility(
    double inner_radius_m, double outer_radius_m,
    double inner_wall_thickness_m, double inner_young_modulus_Pa,
    double inner_poisson_ratio, double formation_young_modulus_Pa,
    double formation_poisson_ratio);

[[nodiscard]] double volumetricPressureIncrement(double dV_effective,
                                                 double annular_volume,
                                                 double effective_compressibility);

class PknModel {
 public:
  [[nodiscard]] PknResult evaluate(const PknInput& input, double elapsed_time_s) const;
  [[nodiscard]] PknResult simulate(const PknInput& input) const;
};

}  // namespace lss::lot
