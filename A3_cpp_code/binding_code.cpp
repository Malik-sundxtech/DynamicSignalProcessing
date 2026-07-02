// In this file all the C++ files are converted into usable Python methods.

// C++ is used for heavy algortyhems - numpy is already written in C and therefore not necesarilly faster in C++
// Normally filename should be .cpp but since it is a python dynamic extension module it is a .pyd file
// This file is converted into a .pyd file in build/release 


#include <pybind11/pybind11.h>
#include "math.h"

namespace py = pybind11;

PYBIND11_MODULE(binding_code, m, py::mod_gil_not_used()) {
    m.doc() = "pybind11 example plugin"; // optional module docstring

    m.def("add", &add, "A function that adds two numbers");
}