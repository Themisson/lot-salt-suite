#include "salt/SaltCreepAdapterState.hpp"

#include <cmath>
#include <stdexcept>
#include <string>

namespace lss::salt {
namespace {

void require_finite(double value, const char* field) {
  if (!std::isfinite(value)) {
    throw std::invalid_argument(std::string(field) + " must be finite");
  }
}

void require_nonnegative(double value, const char* field) {
  require_finite(value, field);
  if (value < 0.0) {
    throw std::invalid_argument(std::string(field) + " must be >= 0");
  }
}

}  // namespace

bool SaltCreepAdapterState::initialized() const {
  return initialized_;
}

double SaltCreepAdapterState::current_time_s() const {
  return current_time_s_;
}

double SaltCreepAdapterState::last_wall_pressure_Pa() const {
  return last_wall_pressure_Pa_;
}

double SaltCreepAdapterState::last_radial_displacement_m() const {
  return last_radial_displacement_m_;
}

double SaltCreepAdapterState::last_radial_closure_m() const {
  return last_radial_closure_m_;
}

int SaltCreepAdapterState::step_count() const {
  return step_count_;
}

void SaltCreepAdapterState::initialize(double initial_time_s,
                                       double initial_wall_pressure_Pa) {
  require_nonnegative(initial_time_s, "initial_time_s");
  require_nonnegative(initial_wall_pressure_Pa, "initial_wall_pressure_Pa");

  initialized_ = true;
  current_time_s_ = initial_time_s;
  last_wall_pressure_Pa_ = initial_wall_pressure_Pa;
  last_radial_displacement_m_ = 0.0;
  last_radial_closure_m_ = 0.0;
  step_count_ = 0;
}

void SaltCreepAdapterState::record_response(
    double time_s,
    double wall_pressure_Pa,
    const SaltCreepResponse& response) {
  if (!initialized_) {
    throw std::logic_error("SaltCreepAdapterState must be initialized first");
  }

  require_nonnegative(time_s, "time_s");
  require_nonnegative(wall_pressure_Pa, "wall_pressure_Pa");
  require_finite(response.radial_displacement_m,
                 "response.radial_displacement_m");
  require_nonnegative(response.radial_closure_m,
                      "response.radial_closure_m");
  require_finite(response.radial_strain, "response.radial_strain");
  require_nonnegative(response.effective_closure_pressure_Pa,
                      "response.effective_closure_pressure_Pa");
  if (!response.valid) {
    throw std::invalid_argument("response.valid must be true");
  }
  if (time_s < current_time_s_) {
    throw std::invalid_argument("time_s must be nondecreasing");
  }

  current_time_s_ = time_s;
  last_wall_pressure_Pa_ = wall_pressure_Pa;
  last_radial_displacement_m_ = response.radial_displacement_m;
  last_radial_closure_m_ = response.radial_closure_m;
  ++step_count_;
}

void SaltCreepAdapterState::reset() {
  initialized_ = false;
  current_time_s_ = 0.0;
  last_wall_pressure_Pa_ = 0.0;
  last_radial_displacement_m_ = 0.0;
  last_radial_closure_m_ = 0.0;
  step_count_ = 0;
}

}  // namespace lss::salt
