cmake_minimum_required(VERSION 3.1)
include(ExternalProject)
include(CheckCXXCompilerFlag)
include(CheckCCompilerFlag)


unset(PYTHON_VERSION)


find_package(PythonLibsNew EXACT ${PYTHON_VERSION} MODULE REQUIRED)

message(STATUS "Python version: ${PYTHON_VERSION}")
message(STATUS "Python lib:     ${PYTHON_LIBRARY}")
message(STATUS "Python include: ${PYTHON_INCLUDE_DIR}")
message(STATUS "Python interpreter: ${PYTHON_EXECUTABLE}")

set(PYBIND11_VERSION 2.2.1)
set(PYBIND11_SHA256 SHA256=53c373d7d0b0711fea96beba666a9985269dc9e43e6088ea73faaa89b07b972e)
set(PYBIND11_URL "${THIRD_PARTY_DIRECTORY}/pybind11-${PYBIND11_VERSION}.zip" CACHE STRING "URL to the Pybind11 repo")
ExternalProject_Add(lief_pybind11
  URL               ${PYBIND11_URL}
  URL_HASH          ${PYBIND11_SHA256}
  CONFIGURE_COMMAND ""
  BUILD_COMMAND     ""
  INSTALL_COMMAND   "")
ExternalProject_get_property(lief_pybind11 SOURCE_DIR)
set(PYBIND11_SOURCE_DIR "${SOURCE_DIR}")


# Define source files
set(LIEF_PYTHON_BASIC_SRC
  "${CMAKE_CURRENT_SOURCE_DIR}/pyLIEF.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/pyUtils.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/pyIterators.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/pyExceptions.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/pyLogger.cpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/encoding.cpp"
)

if (LIEF_ENABLE_JSON)
  set(LIEF_PYTHON_BASIC_SRC
    ${LIEF_PYTHON_BASIC_SRC}
    "${CMAKE_CURRENT_SOURCE_DIR}/pyJson.cpp"
  )
endif()

set(LIEF_PYTHON_SRC
  ${LIEF_PYTHON_BASIC_SRC}
)


set(LIEF_PYTHON_BASIC_HDR
  "${CMAKE_CURRENT_SOURCE_DIR}/pyIterators.hpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/pyLIEF.hpp"
  "${CMAKE_CURRENT_SOURCE_DIR}/encoding.hpp"
)

set(LIEF_PYTHON_HDR
  ${LIEF_PYTHON_BASIC_HDR}
)

source_group("Header Files" FILES ${LIEF_PYTHON_BASIC_HDR})

add_library(pyLIEF SHARED ${LIEF_PYTHON_SRC} ${LIEF_PYTHON_HDR})

target_include_directories(pyLIEF PUBLIC
  "${CMAKE_CURRENT_SOURCE_DIR}/"
  "${PYTHON_INCLUDE_DIR}"
  "${PYBIND11_SOURCE_DIR}/include")

add_definitions(-DELPP_NO_DEFAULT_LOG_FILE)

include("${CMAKE_CURRENT_SOURCE_DIR}/Abstract/CMakeLists.txt")

if(LIEF_ELF)
  include("${CMAKE_CURRENT_SOURCE_DIR}/ELF/CMakeLists.txt")
endif()

if(LIEF_PE)
  include("${CMAKE_CURRENT_SOURCE_DIR}/PE/CMakeLists.txt")
endif()

if(LIEF_MACHO)
  include("${CMAKE_CURRENT_SOURCE_DIR}/MachO/CMakeLists.txt")
endif()


target_compile_features(pyLIEF PRIVATE cxx_attribute_deprecated)

set_property(TARGET pyLIEF PROPERTY CXX_STANDARD          11)
set_property(TARGET pyLIEF PROPERTY CXX_STANDARD_REQUIRED ON)

if (MSVC)
  target_compile_options(pyLIEF PUBLIC /FIiso646.h)
	set_property(TARGET pyLIEF PROPERTY LINK_FLAGS /NODEFAULTLIB:MSVCRT)
endif()

set_target_properties(pyLIEF PROPERTIES PYTHON_VERSION ${PYTHON_VERSION})
set(PYLIEF_DEPS_LIBRARIES LIB_LIEF_STATIC)

if(LIEF_COVERAGE)
  target_compile_options(pyLIEF PRIVATE -g -O0 --coverage -fprofile-arcs -ftest-coverage)
  set(PYLIEF_DEPS_LIBRARIES ${PYLIEF_DEPS_LIBRARIES} gcov)
endif()

set(PYLIEF_COMPILE_FLAGS)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  CHECK_CXX_COMPILER_FLAG("-Wno-macro-redefined" HAS_NO_MACRO_REDEFINED)
  set(PYLIEF_COMPILE_FLAGS ${PYLIEF_COMPILE_FLAGS} -Wall -Wextra -Wpedantic)
  if (HAS_NO_MACRO_REDEFINED)
    set(PYLIEF_COMPILE_FLAGS ${PYLIEF_COMPILE_FLAGS} -Wno-macro-redefined)
  endif()

  target_compile_options(pyLIEF PRIVATE ${PYLIEF_COMPILE_FLAGS})
endif()

set_target_properties(pyLIEF PROPERTIES PREFIX "" OUTPUT_NAME "_pylief")
add_dependencies(pyLIEF lief_pybind11)

if(APPLE)
    set_target_properties(pyLIEF PROPERTIES MACOSX_RPATH ".")
    set_target_properties(pyLIEF PROPERTIES LINK_FLAGS "-undefined dynamic_lookup ")
endif()

set_target_properties(pyLIEF PROPERTIES PREFIX "")
if (UNIX)
  set_target_properties(pyLIEF PROPERTIES SUFFIX ".so")
elseif(WIN32)
  set_target_properties(pyLIEF PROPERTIES SUFFIX ".pyd")
endif()

get_target_property(suffix pyLIEF SUFFIX)
set(LIEF_LIBRARY_NAME "lief${suffix}")

if (WIN32)
  set(PYLIEF_DEPS_LIBRARIES ${PYLIEF_DEPS_LIBRARIES} ${PYTHON_LIBRARIES})
endif()

target_link_libraries(pyLIEF PUBLIC ${PYLIEF_DEPS_LIBRARIES})

add_custom_command(TARGET pyLIEF POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pyLIEF> ${PROJECT_BINARY_DIR}/api/python/lief
)

if (MSVC)
  add_custom_command(TARGET pyLIEF POST_BUILD
      COMMAND ${CMAKE_COMMAND} -E copy $<TARGET_FILE:pyLIEF> ${CMAKE_CURRENT_BINARY_DIR}
  )
endif()

configure_file("${CMAKE_CURRENT_SOURCE_DIR}/setup.py.in"    "${CMAKE_CURRENT_BINARY_DIR}/setup.py")
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/__init__.py.in" "${CMAKE_CURRENT_BINARY_DIR}/lief/__init__.py")
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/README"         "${CMAKE_CURRENT_BINARY_DIR}/README")
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/MANIFEST.in"    "${CMAKE_CURRENT_BINARY_DIR}/MANIFEST.in")
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/setup.cfg"      "${CMAKE_CURRENT_BINARY_DIR}/setup.cfg")

MESSAGE(STATUS "OS: ${CMAKE_HOST_SYSTEM}")

find_program(ENV_BINARY "env")

if (UNIX AND ENV_BINARY AND LIEF_INSTALL_PYTHON)
    install(CODE "execute_process(COMMAND ${ENV_BINARY} ${PYTHON_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/setup.py install)"
      COMPONENT python)
endif()


