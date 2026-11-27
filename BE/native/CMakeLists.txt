cmake_minimum_required(VERSION 3.15)
project(asuna_vector_search LANGUAGES CXX)

add_library(asuna_vector_search SHARED vector_search.cpp)
target_compile_features(asuna_vector_search PRIVATE cxx_std_11)
set_target_properties(asuna_vector_search PROPERTIES
    CXX_VISIBILITY_PRESET hidden
    VISIBILITY_INLINES_HIDDEN YES
)
if(WIN32)
    set_target_properties(asuna_vector_search PROPERTIES PREFIX "")
endif()
if(MINGW)
    target_link_options(asuna_vector_search PRIVATE -static)
endif()
