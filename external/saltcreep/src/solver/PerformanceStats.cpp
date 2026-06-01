#include "solver/PerformanceStats.hpp"

#ifdef _OPENMP
#include <omp.h>
#endif

int saltcreep_omp_max_threads() {
#ifdef _OPENMP
    return omp_get_max_threads();
#else
    return 1;
#endif
}
