# Default to Release
if(NOT CMAKE_BUILD_TYPE)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Build type" FORCE)
endif()
message(STATUS "CMAKE_BUILD_TYPE = ${CMAKE_BUILD_TYPE}")

# Simple optimization flags for Release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG -march=native")
endif()

# Silence deprecation noise from subprojects
set(CMAKE_WARN_DEPRECATED OFF CACHE BOOL "" FORCE)

# Resolve pybind11 from installed pip module
execute_process(
  COMMAND python3 -c "import pybind11, sys; sys.stdout.write(pybind11.get_cmake_dir())"
  OUTPUT_VARIABLE PYBIND11_CMAKE_DIR
  RESULT_VARIABLE PYBIND11_PY_OK
  OUTPUT_STRIP_TRAILING_WHITESPACE
  ERROR_QUIET
)
if(PYBIND11_PY_OK EQUAL 0 AND PYBIND11_CMAKE_DIR)
  list(APPEND CMAKE_PREFIX_PATH "${PYBIND11_CMAKE_DIR}")
endif()
set(PYBIND11_FINDPYTHON ON)
find_package(pybind11 REQUIRED)

# Get libcurl for api usage
find_package(CURL REQUIRED)
include(FetchContent)

# JSON Library
FetchContent_Declare(
    json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.2
)
FetchContent_MakeAvailable(json)

# ICU
find_package(ICU REQUIRED COMPONENTS uc i18n)

# Find rapidfuzz
execute_process(
    COMMAND python3 -c "import rapidfuzz; print(rapidfuzz.__path__)"
    OUTPUT_VARIABLE RAPIDFUZZ_PYTHON_PATH
    OUTPUT_STRIP_TRAILING_WHITESPACE
)
# Define the path to rapidfuzz headers
set(RAPIDFUZZ_INCLUDE_DIR "${RAPIDFUZZ_PYTHON_PATH}/src")

# CatBoost (prebuilt binary)
add_library(catboostmodel SHARED IMPORTED GLOBAL)
set_target_properties(catboostmodel PROPERTIES
    IMPORTED_LOCATION "${PROJECT_SOURCE_DIR}/catboost/catboost_native_build/catboost/libs/model_interface/libcatboostmodel.so"
    IMPORTED_SONAME "libcatboostmodel.so"
    INTERFACE_INCLUDE_DIRECTORIES "${PROJECT_SOURCE_DIR}/catboost/catboost/libs/model_interface"
)

# Core C++ SDK library
add_library(email_predictor_lib
    src/email_predictor/email_prediction_engine.cpp
    src/email_predictor/light_gbm_template_predictor.cpp
    src/email_predictor/catboost_template_predictor.cpp
    src/email_predictor/features/investor_feature_extractor.cpp
    src/email_predictor/features/builder/feature_matrix_builder.cpp
    src/email_predictor/local_part_resolver/resolve_email_local_part.cpp
    src/email_predictor/name_decomposer/name_decomposer.cpp
    src/string_normalization/splitter.cpp
    src/email_predictor/domain_resolver/domain_resolver.cpp
    src/third_party/enrichment/rocket_reach_client.cpp
    src/third_party/verification/hunter_client.cpp
    src/third_party/call_api.cpp
)

# Required for pybind11 to link this static lib into a shared object
set_target_properties(email_predictor_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)

# Public + Private includes
target_include_directories(email_predictor_lib
    PUBLIC
        $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>     # Public API headers
        $<INSTALL_INTERFACE:include>                               # For install()
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/src                            # Internal headers
        ${CURL_INCLUDE_DIRS}                                       # Add CURL headers
)
# Suppress third party warnings
target_include_directories(email_predictor_lib
    SYSTEM PRIVATE                                                 # Suppress warnings
        ${PROJECT_SOURCE_DIR}/LightGBM/include                     # LightGBM
        ${PROJECT_SOURCE_DIR}/catboost                             # Link and suppress CatBoost
        ${PROJECT_SOURCE_DIR}/catboost/catboost
)

# Link libraries
target_link_libraries(email_predictor_lib
    ICU::uc
    ICU::i18n
    _lightgbm
    catboostmodel
    rapidfuzz::rapidfuzz
    ${CURL_LIBRARIES}                                              # Add CURL libraries
)

# Enable strict warnings on this lib only
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU")
    target_compile_options(email_predictor_lib PRIVATE
        -Wall -Wextra -Wpedantic
        -Wconversion -Wsign-conversion -Wshadow -Wold-style-cast
        -Wnon-virtual-dtor -Wnull-dereference -Wduplicated-cond
        -Wduplicated-branches -Wlogical-op -Wuseless-cast
        -Wcast-align=strict -Wformat=2 -Wimplicit-fallthrough=5
        -Wdouble-promotion -Wmissing-declarations -Wmissing-include-dirs
        -Winvalid-pch -fstrict-aliasing -fno-common -fvisibility=hidden
        -fstack-protector-strong -pipe -pthread
        -Wno-unused-parameter
    )
endif()

# Python bindings module
pybind11_add_module(email_predictor
    src/bindings.cpp
)

# Make bindings link against the full C++ SDK
target_link_libraries(email_predictor 
    PRIVATE 
        email_predictor_lib
        pybind11::module
)

# Let bindings see public + private headers
target_include_directories(email_predictor
    PRIVATE
        ${CMAKE_CURRENT_SOURCE_DIR}/include
        ${CMAKE_CURRENT_SOURCE_DIR}/src
        ${PROJECT_SOURCE_DIR}/LightGBM/include
        ${PROJECT_SOURCE_DIR}/catboost
        ${PYBIND11_INCLUDE_DIRS}
)