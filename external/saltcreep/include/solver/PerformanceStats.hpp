#pragma once

struct PerformanceStats {
    double time_assembly_s = 0.0;
    double time_solve_s = 0.0;
    double time_constitutive_s = 0.0;

    void add(const PerformanceStats& other) {
        time_assembly_s += other.time_assembly_s;
        time_solve_s += other.time_solve_s;
        time_constitutive_s += other.time_constitutive_s;
    }
};

int saltcreep_omp_max_threads();
