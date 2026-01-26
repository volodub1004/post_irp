# Download and configure GTest automatically
include(FetchContent)
FetchContent_Declare(
  googletest
  URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  DOWNLOAD_EXTRACT_TIMESTAMP true
)
FetchContent_MakeAvailable(googletest)

enable_testing()

add_executable(test_email_predictor
    test_domain_resolver.cpp
    test_email_template_predictor.cpp
    test_engine_integration.cpp
    test_feature_matrix_builder.cpp
    test_german_char_normalization.cpp
    test_investor_feature_extractor.cpp
    test_name_decomposer.cpp
    test_nfkd_normalize.cpp
    test_predictor.cpp
    test_resolve_email_local_part.cpp
    test_string_splitter.cpp
    test_template_loader.cpp
    test_template_token_parsing.cpp
    test_to_lower.cpp
    test_unseen_validation.cpp
)

target_include_directories(test_email_predictor PRIVATE
    ${PROJECT_SOURCE_DIR}/cpp/include
    ${PROJECT_SOURCE_DIR}/cpp/src
    ${PROJECT_SOURCE_DIR}/LightGBM/include
    ${PROJECT_SOURCE_DIR}/catboost
    ${PROJECT_SOURCE_DIR}/catboost/catboost
    ${PROJECT_SOURCE_DIR}/catboost/catboost/libs/model_interface
    ${PROJECT_SOURCE_DIR}/catboost_native_build
)

find_package(ICU REQUIRED COMPONENTS uc i18n)

target_link_libraries(test_email_predictor
    email_predictor_lib
    gtest_main
    ICU::uc
    ICU::i18n
)

include(GoogleTest)
gtest_discover_tests(test_email_predictor)
