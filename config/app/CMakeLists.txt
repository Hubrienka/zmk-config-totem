# Allow us to #include "mapping.h"
zephyr_include_directories(${CMAKE_CURRENT_SOURCE_DIR}/include)

# Tell Zephyr’s DTS compiler to pull in our combos
set(DTC_OVERLAY_FILE
  ${DTC_OVERLAY_FILE}
  ${CMAKE_CURRENT_SOURCE_DIR}/src/combos.keymap
)
