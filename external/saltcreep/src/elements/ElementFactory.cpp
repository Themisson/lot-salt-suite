#include "elements/ElementFactory.hpp"

#include <stdexcept>

#include "elements/axisym_1d_L3.hpp"
#include "elements/axisym_2d_aq9.hpp"
#include "elements/axisym_2d_q8.hpp"
#include "elements/axisym_2d_q9.hpp"
#include "elements/axisym_2d_q4.hpp"
#include "elements/axisym_2d_t3.hpp"
#include "elements/axisym_2d_t6.hpp"

std::unique_ptr<Element> make_element(const std::string& element_type) {
    if (element_type == "axisym_1d_L3")
        return std::make_unique<AxisymL3>();
    if (element_type == "axisym_2d_Q4")
        return std::make_unique<AxisymQ4>();
    if (element_type == "axisym_2d_T3")
        return std::make_unique<AxisymT3>();
    if (element_type == "axisym_2d_Q8")
        return std::make_unique<AxisymQ8>();
    if (element_type == "axisym_2d_Q9")
        return std::make_unique<AxisymQ9>();
    if (element_type == "axisym_2d_AQ9")
        return std::make_unique<AxisymAQ9>();
    if (element_type == "axisym_2d_T6")
        return std::make_unique<AxisymT6>();

    throw std::invalid_argument("Unknown element.type: " + element_type);
}
