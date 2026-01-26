cmake_minimum_required(VERSION 3.20)
project(cpp_reference_engine LANGUAGES CXX)

# C++23 + compiler warnings
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
add_compile_options(-Wall -Wextra -Wpedantic -Wno-unused-parameter)

# Add LightGBM
add_subdirectory(LightGBM)

# Add Rapid Fuzz
add_subdirectory(rapid_fuzz)

# Subdirectories
add_subdirectory(cpp)    # Core C++ SDK + pybind11 + REST bindings
if(EXISTS "${CMAKE_SOURCE_DIR}/tests/CMakeLists.txt")
    add_subdirectory(tests)  # Unit tests for the SDK
endif()
