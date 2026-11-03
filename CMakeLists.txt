cmake_minimum_required(VERSION 3.16)

if(NOT DEFINED IDF_TARGET)
    set(IDF_TARGET esp32c3)
endif()
set(PROJECT_VER "0.1.0")
set(COMPONENTS main)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# Keep the same target-based artifact names as the development CLI and CI.
string(REGEX REPLACE "^esp32(.+)$" "esp32-\\1" FIRMWARE_NAME "${IDF_TARGET}")
project(${FIRMWARE_NAME})
