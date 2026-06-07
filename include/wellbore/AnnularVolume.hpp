#pragma once

namespace lss::wellbore {

[[nodiscard]] double annular_volume_per_radian_m3(double outer_radius_m,
                                                  double inner_radius_m,
                                                  double length_m);

[[nodiscard]] double annular_total_volume_m3(double outer_radius_m,
                                             double inner_radius_m,
                                             double length_m);

}  // namespace lss::wellbore
