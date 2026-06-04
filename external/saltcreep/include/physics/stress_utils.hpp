#pragma once

#include <algorithm>
#include <cmath>

#include "types.hpp"

namespace stress_utils {

inline double mean_stress(const Stress& sigma) {
    return (sigma[0] + sigma[1] + sigma[2]) / 3.0;
}

inline double sigma_theta(const Stress& sigma) {
    return sigma[1];
}

inline double sigma_theta_compression_positive(const Stress& sigma) {
    return -sigma_theta(sigma);
}

inline Stress deviatoric_stress(const Stress& sigma) {
    const double mean = mean_stress(sigma);
    Stress s = sigma;
    s[0] -= mean;
    s[1] -= mean;
    s[2] -= mean;
    s[3] = sigma[3];
    return s;
}

inline double j2_from_deviatoric(const Stress& s_dev) {
    return 0.5 * (s_dev[0] * s_dev[0] +
                  s_dev[1] * s_dev[1] +
                  s_dev[2] * s_dev[2] +
                  2.0 * s_dev[3] * s_dev[3]);
}

inline double j2(const Stress& sigma) {
    return j2_from_deviatoric(deviatoric_stress(sigma));
}

inline double von_mises_effective_stress(const Stress& sigma) {
    return std::sqrt(std::max(0.0, 3.0 * j2(sigma)));
}

} // namespace stress_utils
