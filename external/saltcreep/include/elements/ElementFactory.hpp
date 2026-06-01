#pragma once
#include <memory>
#include <string>

#include "elements/Element.hpp"

std::unique_ptr<Element> make_element(const std::string& element_type);
