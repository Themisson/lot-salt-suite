#pragma once
#include <string>
#include <vector>

struct SestSalOracle {
    std::string case_name;
    double closure_percent_final;
    double tolerance_percent;
    std::string notes;
};

const std::vector<SestSalOracle> SESTSAL_ORACLES = {
    {
        "base_model",
        1.6583,
        5.0,
        "DM halita"
    },
    {
        "base_model2D",
        0.0374,
        5.0,
        "DM halita"
    },
    {
        "hello_repasse",
        1.0632,
        5.0,
        "DM halita"
    },
    {
        "hello_repasse2D",
        0.5267,
        5.0,
        "DM halita"
    },
    {
        "repasse2D",
        0.2459,
        5.0,
        "DM halita"
    },
};
