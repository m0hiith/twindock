####################################################################
# Automatically-generated file. Do not edit!                       #
# Makefile Version 21                                              #
####################################################################

BASE_SDK_PATH = /Users/mohith/.silabs/slt/installs/conan/p/simpleca33d691c539/p
BASE_PKG_PATH = /Users/mohith/.silabs/slt/installs
UNAME:=$(shell $(POSIX_TOOL_PATH)uname -s | $(POSIX_TOOL_PATH)sed -e 's/^\(CYGWIN\).*/\1/' | $(POSIX_TOOL_PATH)sed -e 's/^\(MINGW\).*/\1/')
ifeq ($(UNAME),MINGW)
# Translate "C:/super" into "/C/super" for MinGW make.
SDK_PATH := /$(shell $(POSIX_TOOL_PATH)echo $(BASE_SDK_PATH) | sed s/://)
PKG_PATH := /$(shell $(POSIX_TOOL_PATH)echo $(BASE_PKG_PATH) | sed s/://)
endif
SDK_PATH ?= $(BASE_SDK_PATH)
PKG_PATH ?= $(BASE_PKG_PATH)
COPIED_SDK_PATH ?= simplicity_sdk_2026.6.1

# This uses the explicit build rules below
PROJECT_SOURCE_FILES =

C_SOURCE_FILES   += $(filter %.c, $(PROJECT_SOURCE_FILES))
CXX_SOURCE_FILES += $(filter %.cpp, $(PROJECT_SOURCE_FILES))
CXX_SOURCE_FILES += $(filter %.cc, $(PROJECT_SOURCE_FILES))
ASM_SOURCE_FILES += $(filter %.s, $(PROJECT_SOURCE_FILES))
ASM_SOURCE_FILES += $(filter %.S, $(PROJECT_SOURCE_FILES))
LIB_FILES        += $(filter %.a, $(PROJECT_SOURCE_FILES))

C_DEFS += \
 '-DSLI_SI91X_EMBEDDED_MQTT_CLIENT=1' \
 '-DSL_MQTT_CLIENT_MAX_RX_PAYLOAD_SIZE=5120' \
 '-DSL_SI91X_PRINT_DBG_LOG=1' \
 '-DconfigNUM_SDK_THREAD_LOCAL_STORAGE_POINTERS=2' \
 '-D_RTE_=1' \
 '-DSLI_CODE_CLASSIFICATION_GCC_USE_USED=1' \
 '-DSL_COMPONENT_CATALOG_PRESENT=1' \
 '-DSL_CODE_COMPONENT_FREERTOS_KERNEL=freertos_kernel' \
 '-DSL_CODE_COMPONENT_CORE=core' \
 '-DSL_CODE_COMPONENT_SLEEPTIMER=sleeptimer' \
 '-DSIWG917M111MGTBA=1' \
 '-DSLI_SI917=1' \
 '-DSLI_SI917B0=1' \
 '-DSLI_SI91X_MCU_ENABLE_FLASH_BASED_EXECUTION=1' \
 '-DSLI_SI91X_MCU_EXTERNAL_LDO_FOR_PSRAM=1' \
 '-DSI917_DEVKIT=1' \
 '-DSLI_SI91X_MCU_COMMON_FLASH_MODE=1' \
 '-DSLI_SI91X_MCU_CONFIG_RADIO_BOARD_BASE_VER=1' \
 '-DSLI_SI91X_MCU_CONFIG_RADIO_BOARD_VER2=1' \
 '-DSL_BOARD_NAME="BRD2605A"' \
 '-DSL_BOARD_REV="A02"' \
 '-DSL_CODE_COMPONENT_CMSIS_UDMA=cmsis_udma' \
 '-DSLI_SI91X_MCU_ENABLE_RAM_BASED_EXECUTION=1' \
 '-D__FREERTOS_OS_WISECONNECT=1' \
 '-DSRAM_BASE=0x0cUL' \
 '-DSRAM_SIZE=0x2fc00UL' \
 '-D_SI91X_DEVICE=1' \
 '-DSL_NET_COMPONENT_INCLUDED=1' \
 '-D__STATIC_INLINE=static inline' \
 '-DCLOCK_ROMDRIVER_PRESENT=1' \
 '-DULPSS_CLOCK_ROMDRIVER_PRESENT=1' \
 '-DSL_SI91X_BOARD_INIT=1' \
 '-DSLI_SI91X_MCU_ENABLE_IPMU_APIS=1' \
 '-DSL_CODE_COMPONENT_RSILIB_CHIP=rsilib_chip' \
 '-DSL_SI91X_SOC_MODE=1' \
 '-DCRC_ROMDRIVER_PRESENT=1' \
 '-DSL_CODE_COMPONENT_RSILIB_EGPIO=rsilib_egpio' \
 '-DSL_CODE_COMPONENT_RSILIB_SYSRTC=rsilib_sysrtc' \
 '-DTIMER_ROMDRIVER_PRESENT=1' \
 '-DDEBUG_ENABLE=1' \
 '-DDEBUG_UART=1' \
 '-DENABLE_DEBUG_MODULE=1' \
 '-DSLI_CAPTIVE_CORE_PRESENT=1' \
 '-DSL_LOG_SI91X_PLATFORM_CORE=1' \
 '-DSL_SI91X_SI917_RAM_MEM_CONFIG=1' \
 '-DSL_CODE_COMPONENT_SL_CLOCK_MANAGER=sl_clock_manager' \
 '-DUDMA_ROMDRIVER_PRESENT=1' \
 '-DSLI_SI91X_OFFLOAD_NETWORK_STACK=1' \
 '-DSI917=1' \
 '-DSLI_SI91X_ENABLE_OS=1' \
 '-DSLI_SI91X_MCU_INTERFACE=1' \
 '-DTA_DEEP_SLEEP_COMMON_FLASH=1' \
 '-DSI917_RGB_DRIVER_OLD=1' \
 '-DSLI_SI91X_SOCKETS=1' \
 '-DSL_CODE_COMPONENT_SI91X_WIRELESS=si91x_wireless' \
 '-DSL_ULP_TIMER=1' \
 '-DSL_SI91X_REQUIRES_INTF_PLL=1' \
 '-DSL_SI91X_USART_DMA=1' \
 '-DUSART_MODULE=1' \
 '-DIOSTREAM_USART=1' \
 '-DSI91X_PLATFORM=1' \
 '-DSI91X_SYSRTC_PRESENT=1' \
 '-DSL_CODE_COMPONENT_SLEEPTIMER_SI91X=sleeptimer_si91x' \
 '-DSL_SLEEP_TIMER=1' \
 '-D__WEAK=__attribute__((weak))' \
 '-DSL_CODE_COMPONENT_SLI_HAL_SI91X=sli_hal_si91x' \
 '-DSL_WIFI_COMPONENT_INCLUDED=1' \
 '-DSL_CODE_COMPONENT_SLI_ROUTING_UTILITY=sli_routing_utility' \
 '-DSL_CODE_COMPONENT_SLI_SI91X_WIFI_CMD_ENGINE=sli_si91x_wifi_cmd_engine' \
 '-DPLL_ROMDRIVER_PRESENT=1' \
 '-DSL_CODE_COMPONENT_SYSTEMLEVEL_PLL=systemlevel_pll'

ASM_DEFS += \
 '-DSLI_SI91X_EMBEDDED_MQTT_CLIENT=1' \
 '-DSL_MQTT_CLIENT_MAX_RX_PAYLOAD_SIZE=5120' \
 '-DSL_SI91X_PRINT_DBG_LOG=1' \
 '-DconfigNUM_SDK_THREAD_LOCAL_STORAGE_POINTERS=2' \
 '-D_RTE_=1' \
 '-DSLI_CODE_CLASSIFICATION_GCC_USE_USED=1' \
 '-DSL_COMPONENT_CATALOG_PRESENT=1' \
 '-DSL_CODE_COMPONENT_FREERTOS_KERNEL=freertos_kernel' \
 '-DSL_CODE_COMPONENT_CORE=core' \
 '-DSL_CODE_COMPONENT_SLEEPTIMER=sleeptimer' \
 '-DSIWG917M111MGTBA=1' \
 '-DSLI_SI917=1' \
 '-DSLI_SI917B0=1' \
 '-DSLI_SI91X_MCU_ENABLE_FLASH_BASED_EXECUTION=1' \
 '-DSLI_SI91X_MCU_EXTERNAL_LDO_FOR_PSRAM=1' \
 '-DSI917_DEVKIT=1' \
 '-DSLI_SI91X_MCU_COMMON_FLASH_MODE=1' \
 '-DSLI_SI91X_MCU_CONFIG_RADIO_BOARD_BASE_VER=1' \
 '-DSLI_SI91X_MCU_CONFIG_RADIO_BOARD_VER2=1' \
 '-DSL_BOARD_NAME="BRD2605A"' \
 '-DSL_BOARD_REV="A02"' \
 '-DSL_CODE_COMPONENT_CMSIS_UDMA=cmsis_udma' \
 '-DSLI_SI91X_MCU_ENABLE_RAM_BASED_EXECUTION=1' \
 '-D__FREERTOS_OS_WISECONNECT=1' \
 '-DSRAM_BASE=0x0cUL' \
 '-DSRAM_SIZE=0x2fc00UL' \
 '-D_SI91X_DEVICE=1' \
 '-DSL_NET_COMPONENT_INCLUDED=1' \
 '-D__STATIC_INLINE=static inline' \
 '-DCLOCK_ROMDRIVER_PRESENT=1' \
 '-DULPSS_CLOCK_ROMDRIVER_PRESENT=1' \
 '-DSL_SI91X_BOARD_INIT=1' \
 '-DSLI_SI91X_MCU_ENABLE_IPMU_APIS=1' \
 '-DSL_CODE_COMPONENT_RSILIB_CHIP=rsilib_chip' \
 '-DSL_SI91X_SOC_MODE=1' \
 '-DCRC_ROMDRIVER_PRESENT=1' \
 '-DSL_CODE_COMPONENT_RSILIB_EGPIO=rsilib_egpio' \
 '-DSL_CODE_COMPONENT_RSILIB_SYSRTC=rsilib_sysrtc' \
 '-DTIMER_ROMDRIVER_PRESENT=1' \
 '-DDEBUG_ENABLE=1' \
 '-DDEBUG_UART=1' \
 '-DENABLE_DEBUG_MODULE=1' \
 '-DSLI_CAPTIVE_CORE_PRESENT=1' \
 '-DSL_LOG_SI91X_PLATFORM_CORE=1' \
 '-DSL_SI91X_SI917_RAM_MEM_CONFIG=1' \
 '-DSL_CODE_COMPONENT_SL_CLOCK_MANAGER=sl_clock_manager' \
 '-DUDMA_ROMDRIVER_PRESENT=1' \
 '-DSLI_SI91X_OFFLOAD_NETWORK_STACK=1' \
 '-DSI917=1' \
 '-DSLI_SI91X_ENABLE_OS=1' \
 '-DSLI_SI91X_MCU_INTERFACE=1' \
 '-DTA_DEEP_SLEEP_COMMON_FLASH=1' \
 '-DSI917_RGB_DRIVER_OLD=1' \
 '-DSLI_SI91X_SOCKETS=1' \
 '-DSL_CODE_COMPONENT_SI91X_WIRELESS=si91x_wireless' \
 '-DSL_ULP_TIMER=1' \
 '-DSL_SI91X_REQUIRES_INTF_PLL=1' \
 '-DSL_SI91X_USART_DMA=1' \
 '-DUSART_MODULE=1' \
 '-DIOSTREAM_USART=1' \
 '-DSI91X_PLATFORM=1' \
 '-DSI91X_SYSRTC_PRESENT=1' \
 '-DSL_CODE_COMPONENT_SLEEPTIMER_SI91X=sleeptimer_si91x' \
 '-DSL_SLEEP_TIMER=1' \
 '-D__WEAK=__attribute__((weak))' \
 '-DSL_CODE_COMPONENT_SLI_HAL_SI91X=sli_hal_si91x' \
 '-DSL_WIFI_COMPONENT_INCLUDED=1' \
 '-DSL_CODE_COMPONENT_SLI_ROUTING_UTILITY=sli_routing_utility' \
 '-DSL_CODE_COMPONENT_SLI_SI91X_WIFI_CMD_ENGINE=sli_si91x_wifi_cmd_engine' \
 '-DPLL_ROMDRIVER_PRESENT=1' \
 '-DSL_CODE_COMPONENT_SYSTEMLEVEL_PLL=systemlevel_pll'

INCLUDES += \
 -Iconfig \
 -Iautogen \
 -I. \
 -I$(SDK_PATH)/platform_core/platform/common/inc \
 -I$(SDK_PATH)/cmsis/Core/Include \
 -I$(SDK_PATH)/cmsis/Core/Include/m-profile \
 -I$(SDK_PATH)/cmsis/Core/Include/a-profile \
 -I$(SDK_PATH)/cmsis/RTOS2/Include \
 -I$(SDK_PATH)/platform_core/platform/emlib/inc \
 -I$(SDK_PATH)/freertos/kernel/include \
 -I$(SDK_PATH)/freertos/cmsis/Include \
 -I$(SDK_PATH)/freertos/kernel/portable/GCC/ARM_CM4F \
 -I$(SDK_PATH)/platform_core/platform/service/iostream/inc \
 -I$(SDK_PATH)/platform_core/platform/service/sl_log/inc \
 -I$(SDK_PATH)/platform_core/platform/service/mem_pool/inc \
 -I$(SDK_PATH)/platform_core/platform/service/sl_main/inc \
 -I$(SDK_PATH)/platform_core/platform/service/sl_main/src \
 -I$(SDK_PATH)/platform_core/platform/service/sleeptimer/inc \
 -I$(SDK_PATH)/platform_core/platform/service/sleeptimer/src \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/bsd_socket/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/CMSIS/Driver/Include \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/mqtt/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/rom_driver/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/board/silabs/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/inc/mqtt/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_buffer_manager/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_command_engine/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_event_engine/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_queue_manager/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_routing_utility/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/inc \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/resources/certificates \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/resources/html \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/resources/other \
 -I$(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/inc

GROUP_START =-Wl,--start-group
GROUP_END =-Wl,--end-group

PROJECT_LIBS = \
 -lgcc \
 -lc \
 -lm \
 -lnosys

LIBS += $(GROUP_START) $(PROJECT_LIBS) $(GROUP_END)

LIB_FILES += $(filter %.a, $(PROJECT_LIBS))

C_FLAGS += \
 -mcpu=cortex-m4 \
 -mthumb \
 -mfpu=fpv4-sp-d16 \
 -mfloat-abi=softfp \
 -std=c18 \
 -Wall \
 -Wextra \
 -Os \
 -fdata-sections \
 -ffunction-sections \
 -fomit-frame-pointer \
 -g \
 --specs=nano.specs \
 -Wall -Werror -Wno-error=deprecated-declarations \
 -Wno-error=deprecated-declarations \
 -mcpu=cortex-m4 \
 -fno-lto

CXX_FLAGS += \
 -mcpu=cortex-m4 \
 -mthumb \
 -mfpu=fpv4-sp-d16 \
 -mfloat-abi=softfp \
 -std=c++17 \
 -fno-rtti \
 -fno-exceptions \
 -Wall \
 -Wextra \
 -Os \
 -fdata-sections \
 -ffunction-sections \
 -fomit-frame-pointer \
 -g \
 --specs=nano.specs \
 -Wall -Werror -Wno-error=deprecated-declarations \
 -Wno-error=deprecated-declarations \
 -mcpu=cortex-m4 \
 -fno-lto

ASM_FLAGS += \
 -mcpu=cortex-m4 \
 -mthumb \
 -mfpu=fpv4-sp-d16 \
 -mfloat-abi=softfp \
 -x assembler-with-cpp

LD_FLAGS += \
 -mcpu=cortex-m4 \
 -mthumb \
 -mfpu=fpv4-sp-d16 \
 -mfloat-abi=softfp \
 -T"autogen/linkerfile_SoC.ld" \
 --specs=nano.specs \
 -Wl,-Map=$(OUTPUT_DIR)/$(PROJECTNAME).map \
 -Wl,--wrap=main \
 -u _printf_float \
 -fno-lto \
 -Wl,--gc-sections


####################################################################
# Pre/Post Build Rules                                             #
####################################################################
pre-build:
	# No pre-build defined

post-build: $(OUTPUT_DIR)/$(PROJECTNAME).out
ifeq ($(POST_BUILD_EXE),)
		$(error POST_BUILD_EXE is not defined. Post-Build cannot run. Please set the STUDIO_ADAPTER_PACK_PATH to the post-build tool when generating or override the variable for this makefile)
endif
	@$(POSIX_TOOL_PATH)echo 'Running Project Post-Build'
	$(ECHO) @"$(POST_BUILD_EXE)" postbuild "./twindock_gw.slpb" --parameter build_dir:"$(OUTPUT_DIR)"

####################################################################
# SDK Build Rules                                                  #
####################################################################
$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/board/silabs/src/rsi_board.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/board/silabs/src/rsi_board.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/board/silabs/src/rsi_board.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/board/silabs/src/rsi_board.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/board/silabs/src/rsi_board.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/board/silabs/src/rsi_board.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/common/src/malloc_thread_safety.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/src/malloc_thread_safety.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/src/malloc_thread_safety.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/src/malloc_thread_safety.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/common/src/malloc_thread_safety.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/common/src/malloc_thread_safety.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/common/src/sl_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/src/sl_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/src/sl_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/common/src/sl_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/common/src/sl_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/common/src/sl_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/ipmu_apis.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/ipmu_apis.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/ipmu_apis.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/ipmu_apis.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/ipmu_apis.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/ipmu_apis.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/rsi_system_config_917.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/rsi_system_config_917.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/rsi_system_config_917.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/rsi_system_config_917.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/rsi_system_config_917.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/iPMU_prog/iPMU_dotc/rsi_system_config_917.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_deepsleep_soc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_deepsleep_soc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_deepsleep_soc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_deepsleep_soc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_deepsleep_soc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_deepsleep_soc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_ps_ram_func.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_ps_ram_func.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_ps_ram_func.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_ps_ram_func.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_ps_ram_func.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/rsi_ps_ram_func.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/startup_si91x.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/startup_si91x.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/startup_si91x.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/startup_si91x.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/startup_si91x.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/startup_si91x.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/system_si91x.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/system_si91x.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/system_si91x.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/system_si91x.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/system_si91x.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/chip/src/system_si91x.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/rsi_debug.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/rsi_debug.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/rsi_debug.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/rsi_debug.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/rsi_debug.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/rsi_debug.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/sl_si91x_stack_object_declare.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/sl_si91x_stack_object_declare.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/sl_si91x_stack_object_declare.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/sl_si91x_stack_object_declare.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/sl_si91x_stack_object_declare.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/common/src/sl_si91x_stack_object_declare.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config/src/rsi_nvic_priorities_config.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config/src/rsi_nvic_priorities_config.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config/src/rsi_nvic_priorities_config.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config/src/rsi_nvic_priorities_config.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config/src/rsi_nvic_priorities_config.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/core/config/src/rsi_nvic_priorities_config.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/UDMA.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/UDMA.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/UDMA.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/UDMA.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/UDMA.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/UDMA.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/USART.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/USART.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/USART.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/USART.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/USART.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/cmsis_driver/USART.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/src/sl_si91x_button.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/src/sl_si91x_button.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/src/sl_si91x_button.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/src/sl_si91x_button.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/src/sl_si91x_button.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/button/src/sl_si91x_button.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/src/sl_si91x_rgb_led.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/src/sl_si91x_rgb_led.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/src/sl_si91x_rgb_led.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/src/sl_si91x_rgb_led.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/src/sl_si91x_rgb_led.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/hardware_drivers/rgb_led/src/sl_si91x_rgb_led.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/aux_reference_volt_config.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/aux_reference_volt_config.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/aux_reference_volt_config.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/aux_reference_volt_config.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/aux_reference_volt_config.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/aux_reference_volt_config.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/clock_update.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/clock_update.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/clock_update.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/clock_update.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/clock_update.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/clock_update.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_adc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_adc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_adc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_adc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_adc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_adc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_crc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_crc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_crc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_crc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_crc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_crc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_dac.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_dac.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_dac.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_dac.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_dac.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_dac.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_egpio.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_egpio.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_egpio.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_egpio.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_egpio.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_egpio.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_opamp.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_opamp.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_opamp.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_opamp.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_opamp.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_opamp.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_sysrtc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_sysrtc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_sysrtc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_sysrtc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_sysrtc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_sysrtc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_timers.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_timers.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_timers.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_timers.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_timers.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_timers.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma_wrapper.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma_wrapper.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma_wrapper.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma_wrapper.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma_wrapper.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_udma_wrapper.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_usart.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_usart.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_usart.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_usart.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_usart.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/peripheral_drivers/src/rsi_usart.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/src/sl_si91x_clock_manager.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/src/sl_si91x_clock_manager.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/src/sl_si91x_clock_manager.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/src/sl_si91x_clock_manager.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/src/sl_si91x_clock_manager.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/clock_manager/src/sl_si91x_clock_manager.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/src/sl_iostream_usart_si91x.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/src/sl_iostream_usart_si91x.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/src/sl_iostream_usart_si91x.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/src/sl_iostream_usart_si91x.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/src/sl_iostream_usart_si91x.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/iostream/src/sl_iostream_usart_si91x.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_iostream_recommends.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_iostream_recommends.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_iostream_recommends.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_iostream_recommends.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_iostream_recommends.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_iostream_recommends.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_platform_specific.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_platform_specific.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_platform_specific.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_platform_specific.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_platform_specific.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sl_log/src/sl_log_platform_specific.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/src/sl_sleeptimer_hal_si91x_sysrtc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/src/sl_sleeptimer_hal_si91x_sysrtc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/src/sl_sleeptimer_hal_si91x_sysrtc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/src/sl_sleeptimer_hal_si91x_sysrtc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/src/sl_sleeptimer_hal_si91x_sysrtc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/service/sleeptimer/src/sl_sleeptimer_hal_si91x_sysrtc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_bod.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_bod.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_bod.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_bod.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_bod.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_bod.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ipmu.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ipmu.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ipmu.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ipmu.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ipmu.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ipmu.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_pll.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_pll.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_pll.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_pll.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_pll.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_pll.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_rtc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_rtc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_rtc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_rtc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_rtc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_rtc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_temp_sensor.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_temp_sensor.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_temp_sensor.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_temp_sensor.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_temp_sensor.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_temp_sensor.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_time_period.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_time_period.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_time_period.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_time_period.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_time_period.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_time_period.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ulpss_clk.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ulpss_clk.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ulpss_clk.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ulpss_clk.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ulpss_clk.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/systemlevel/src/rsi_ulpss_clk.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_adc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_adc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_adc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_adc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_adc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_adc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_bjt_temperature_sensor.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_bjt_temperature_sensor.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_bjt_temperature_sensor.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_bjt_temperature_sensor.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_bjt_temperature_sensor.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_bjt_temperature_sensor.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_dma.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_dma.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_dma.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_dma.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_dma.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_dma.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_driver_gpio.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_driver_gpio.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_driver_gpio.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_driver_gpio.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_driver_gpio.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_driver_gpio.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_ulp_timer.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_ulp_timer.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_ulp_timer.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_ulp_timer.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_ulp_timer.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_ulp_timer.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_usart.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_usart.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_usart.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_usart.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_usart.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_api/src/sl_si91x_usart.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/src/sl_si91x_peripheral_gpio.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/src/sl_si91x_peripheral_gpio.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/src/sl_si91x_peripheral_gpio.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/src/sl_si91x_peripheral_gpio.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/src/sl_si91x_peripheral_gpio.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/mcu/drivers/unified_peripheral_drivers/src/sl_si91x_peripheral_gpio.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_ram.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_ram.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_ram.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_ram.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_ram.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_ram.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_rom.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_rom.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_rom.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_rom.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_rom.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/rsi_hal_mcu_m4_rom.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform_wireless.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform_wireless.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform_wireless.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform_wireless.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform_wireless.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_platform_wireless.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_bus.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_bus.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_bus.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_bus.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_bus.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_bus.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_timer.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_timer.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_timer.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_timer.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_timer.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sl_si91x_timer.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sli_siwx917_soc.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sli_siwx917_soc.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sli_siwx917_soc.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sli_siwx917_soc.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sli_siwx917_soc.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/ahb_interface/src/sli_siwx917_soc.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/src/sl_si91x_errno.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/src/sl_si91x_errno.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/src/sl_si91x_errno.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/src/sl_si91x_errno.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/src/sl_si91x_errno.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/errno/src/sl_si91x_errno.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade/firmware_upgradation.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade/firmware_upgradation.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade/firmware_upgradation.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade/firmware_upgradation.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade/firmware_upgradation.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/firmware_upgrade/firmware_upgradation.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/host_mcu/si91x/siwx917_soc_ncp_host.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/host_mcu/si91x/siwx917_soc_ncp_host.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/host_mcu/si91x/siwx917_soc_ncp_host.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/host_mcu/si91x/siwx917_soc_ncp_host.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/host_mcu/si91x/siwx917_soc_ncp_host.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/host_mcu/si91x/siwx917_soc_ncp_host.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp/sl_net_ping.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp/sl_net_ping.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp/sl_net_ping.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp/sl_net_ping.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp/sl_net_ping.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/icmp/sl_net_ping.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_rsi_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_rsi_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_rsi_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_rsi_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_rsi_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_rsi_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_callback_framework.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_callback_framework.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_callback_framework.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_callback_framework.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_callback_framework.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_callback_framework.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_integration_handler.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_integration_handler.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_integration_handler.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_integration_handler.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_integration_handler.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_net_si91x_integration_handler.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_si91x_net_internal_stack.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_si91x_net_internal_stack.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_si91x_net_internal_stack.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_si91x_net_internal_stack.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_si91x_net_internal_stack.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sl_si91x_net_internal_stack.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sli_net_si91x_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sli_net_si91x_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sli_net_si91x_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sli_net_si91x_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sli_net_si91x_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sl_net/src/sli_net_si91x_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/src/sli_hal_si91x.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/src/sli_hal_si91x.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/src/sli_hal_si91x.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/src/sli_hal_si91x.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/src/sli_hal_si91x.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_hal_si91x/src/sli_hal_si91x.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine_config.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine_config.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine_config.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine_config.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine_config.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_command_engine/src/sli_si91x_wifi_command_engine_config.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/src/sli_si91x_wifi_event_handler.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/src/sli_si91x_wifi_event_handler.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/src/sli_si91x_wifi_event_handler.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/src/sli_si91x_wifi_event_handler.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/src/sli_si91x_wifi_event_handler.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/sli_si91x_wifi_event_handler/src/sli_si91x_wifi_event_handler.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/src/sl_si91x_socket_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/src/sl_si91x_socket_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/src/sl_si91x_socket_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/src/sl_si91x_socket_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/src/sl_si91x_socket_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/socket/src/sl_si91x_socket_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_rsi_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_rsi_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_rsi_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_rsi_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_rsi_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_rsi_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_si91x_driver.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_si91x_driver.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_si91x_driver.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_si91x_driver.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_si91x_driver.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sl_si91x_driver.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sli_si91x_driver.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sli_si91x_driver.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sli_si91x_driver.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sli_si91x_driver.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sli_si91x_driver.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/device/silabs/si91x/wireless/src/sli_si91x_driver.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/si91x/sl_wifi.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/si91x/sl_wifi.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/si91x/sl_wifi.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/si91x/sl_wifi.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/si91x/sl_wifi.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/si91x/sl_wifi.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_basic_credentials.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_basic_credentials.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_basic_credentials.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_basic_credentials.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_basic_credentials.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_basic_credentials.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_callback_framework.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_callback_framework.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_callback_framework.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_callback_framework.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_callback_framework.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sl_wifi_callback_framework.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sli_wifi_callback_framework.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sli_wifi_callback_framework.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sli_wifi_callback_framework.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/protocol/wifi/src/sli_wifi_callback_framework.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sli_wifi_callback_framework.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/protocol/wifi/src/sli_wifi_callback_framework.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/mqtt/si91x/sl_mqtt_client.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/mqtt/si91x/sl_mqtt_client.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/mqtt/si91x/sl_mqtt_client.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/mqtt/si91x/sl_mqtt_client.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/mqtt/si91x/sl_mqtt_client.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/mqtt/si91x/sl_mqtt_client.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/si91x/sl_net_credentials.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/si91x/sl_net_credentials.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/si91x/sl_net_credentials.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/si91x/sl_net_credentials.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/si91x/sl_net_credentials.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/si91x/sl_net_credentials.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_certificate_store.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_certificate_store.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_certificate_store.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_certificate_store.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_certificate_store.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_certificate_store.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_profiles.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_profiles.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_profiles.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_profiles.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_profiles.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sl_net_basic_profiles.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_common_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_common_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_common_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_common_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_common_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_common_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_credentials.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_credentials.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_credentials.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_credentials.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_credentials.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/service/network_manager/src/sli_net_credentials.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_buffer_manager/src/sli_buffer_manager.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_buffer_manager/src/sli_buffer_manager.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_buffer_manager/src/sli_buffer_manager.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_buffer_manager/src/sli_buffer_manager.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_buffer_manager/src/sli_buffer_manager.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_buffer_manager/src/sli_buffer_manager.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_command_engine/src/sli_command_engine.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_command_engine/src/sli_command_engine.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_command_engine/src/sli_command_engine.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_command_engine/src/sli_command_engine.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_command_engine/src/sli_command_engine.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_command_engine/src/sli_command_engine.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_event_engine/src/sli_event_engine.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_event_engine/src/sli_event_engine.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_event_engine/src/sli_event_engine.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_event_engine/src/sli_event_engine.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_event_engine/src/sli_event_engine.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_event_engine/src/sli_event_engine.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_queue_manager/src/sli_queue_manager.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_queue_manager/src/sli_queue_manager.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_queue_manager/src/sli_queue_manager.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_queue_manager/src/sli_queue_manager.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_queue_manager/src/sli_queue_manager.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_queue_manager/src/sli_queue_manager.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_routing_utility/src/sli_routing_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_routing_utility/src/sli_routing_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_routing_utility/src/sli_routing_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_routing_utility/src/sli_routing_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_routing_utility/src/sli_routing_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_routing_utility/src/sli_routing_utility.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_power_profile.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_power_profile.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_power_profile.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_power_profile.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_power_profile.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_power_profile.o

$(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_utility.o: $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_utility.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_utility.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/../../wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_utility.c
CDEPS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_utility.d
OBJS += $(OUTPUT_DIR)/sdk/_/_/wiseca1ca655dfba28/p/components/sli_wifi/src/sli_wifi_utility.o

$(OUTPUT_DIR)/sdk/cmsis/RTOS2/Source/os_systick.o: $(SDK_PATH)/cmsis/RTOS2/Source/os_systick.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/cmsis/RTOS2/Source/os_systick.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/cmsis/RTOS2/Source/os_systick.c
CDEPS += $(OUTPUT_DIR)/sdk/cmsis/RTOS2/Source/os_systick.d
OBJS += $(OUTPUT_DIR)/sdk/cmsis/RTOS2/Source/os_systick.o

$(OUTPUT_DIR)/sdk/freertos/cmsis/Source/cmsis_os2.o: $(SDK_PATH)/freertos/cmsis/Source/cmsis_os2.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/cmsis/Source/cmsis_os2.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/cmsis/Source/cmsis_os2.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/cmsis/Source/cmsis_os2.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/cmsis/Source/cmsis_os2.o

$(OUTPUT_DIR)/sdk/freertos/kernel/croutine.o: $(SDK_PATH)/freertos/kernel/croutine.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/croutine.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/croutine.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/croutine.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/croutine.o

$(OUTPUT_DIR)/sdk/freertos/kernel/event_groups.o: $(SDK_PATH)/freertos/kernel/event_groups.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/event_groups.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/event_groups.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/event_groups.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/event_groups.o

$(OUTPUT_DIR)/sdk/freertos/kernel/list.o: $(SDK_PATH)/freertos/kernel/list.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/list.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/list.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/list.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/list.o

$(OUTPUT_DIR)/sdk/freertos/kernel/portable/MemMang/heap_4.o: $(SDK_PATH)/freertos/kernel/portable/MemMang/heap_4.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/portable/MemMang/heap_4.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/portable/MemMang/heap_4.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/portable/MemMang/heap_4.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/portable/MemMang/heap_4.o

$(OUTPUT_DIR)/sdk/freertos/kernel/portable/SiliconLabs/SiWx91X/port.o: $(SDK_PATH)/freertos/kernel/portable/SiliconLabs/SiWx91X/port.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/portable/SiliconLabs/SiWx91X/port.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/portable/SiliconLabs/SiWx91X/port.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/portable/SiliconLabs/SiWx91X/port.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/portable/SiliconLabs/SiWx91X/port.o

$(OUTPUT_DIR)/sdk/freertos/kernel/queue.o: $(SDK_PATH)/freertos/kernel/queue.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/queue.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/queue.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/queue.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/queue.o

$(OUTPUT_DIR)/sdk/freertos/kernel/stream_buffer.o: $(SDK_PATH)/freertos/kernel/stream_buffer.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/stream_buffer.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/stream_buffer.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/stream_buffer.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/stream_buffer.o

$(OUTPUT_DIR)/sdk/freertos/kernel/tasks.o: $(SDK_PATH)/freertos/kernel/tasks.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/tasks.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/tasks.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/tasks.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/tasks.o

$(OUTPUT_DIR)/sdk/freertos/kernel/timers.o: $(SDK_PATH)/freertos/kernel/timers.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/freertos/kernel/timers.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/freertos/kernel/timers.c
CDEPS += $(OUTPUT_DIR)/sdk/freertos/kernel/timers.d
OBJS += $(OUTPUT_DIR)/sdk/freertos/kernel/timers.o

$(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_assert.o: $(SDK_PATH)/platform_core/platform/common/src/sl_assert.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/common/src/sl_assert.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/common/src/sl_assert.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_assert.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_assert.o

$(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_cmsis_os2_common.o: $(SDK_PATH)/platform_core/platform/common/src/sl_cmsis_os2_common.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/common/src/sl_cmsis_os2_common.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/common/src/sl_cmsis_os2_common.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_cmsis_os2_common.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_cmsis_os2_common.o

$(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_core_cortexm.o: $(SDK_PATH)/platform_core/platform/common/src/sl_core_cortexm.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/common/src/sl_core_cortexm.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/common/src/sl_core_cortexm.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_core_cortexm.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_core_cortexm.o

$(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_slist.o: $(SDK_PATH)/platform_core/platform/common/src/sl_slist.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/common/src/sl_slist.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/common/src/sl_slist.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_slist.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_slist.o

$(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_string.o: $(SDK_PATH)/platform_core/platform/common/src/sl_string.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/common/src/sl_string.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/common/src/sl_string.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_string.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sl_string.o

$(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sli_cmsis_os2_ext_task_register.o: $(SDK_PATH)/platform_core/platform/common/src/sli_cmsis_os2_ext_task_register.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/common/src/sli_cmsis_os2_ext_task_register.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/common/src/sli_cmsis_os2_ext_task_register.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sli_cmsis_os2_ext_task_register.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/common/src/sli_cmsis_os2_ext_task_register.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/iostream/src/sl_iostream.o: $(SDK_PATH)/platform_core/platform/service/iostream/src/sl_iostream.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/iostream/src/sl_iostream.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/iostream/src/sl_iostream.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/iostream/src/sl_iostream.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/iostream/src/sl_iostream.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/iostream/src/sl_iostream_retarget_stdio.o: $(SDK_PATH)/platform_core/platform/service/iostream/src/sl_iostream_retarget_stdio.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/iostream/src/sl_iostream_retarget_stdio.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/iostream/src/sl_iostream_retarget_stdio.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/iostream/src/sl_iostream_retarget_stdio.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/iostream/src/sl_iostream_retarget_stdio.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/mem_pool/src/sl_mem_pool.o: $(SDK_PATH)/platform_core/platform/service/mem_pool/src/sl_mem_pool.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/mem_pool/src/sl_mem_pool.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/mem_pool/src/sl_mem_pool.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/mem_pool/src/sl_mem_pool.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/mem_pool/src/sl_mem_pool.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/backend/iostream/src/sl_log_backend_iostream_formatted.o: $(SDK_PATH)/platform_core/platform/service/sl_log/backend/iostream/src/sl_log_backend_iostream_formatted.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_log/backend/iostream/src/sl_log_backend_iostream_formatted.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_log/backend/iostream/src/sl_log_backend_iostream_formatted.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/backend/iostream/src/sl_log_backend_iostream_formatted.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/backend/iostream/src/sl_log_backend_iostream_formatted.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/src/sl_log.o: $(SDK_PATH)/platform_core/platform/service/sl_log/src/sl_log.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_log/src/sl_log.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_log/src/sl_log.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/src/sl_log.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/src/sl_log.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/src/sl_log_weak.o: $(SDK_PATH)/platform_core/platform/service/sl_log/src/sl_log_weak.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_log/src/sl_log_weak.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_log/src/sl_log_weak.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/src/sl_log_weak.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_log/src/sl_log_weak.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/rtos/main_retarget.o: $(SDK_PATH)/platform_core/platform/service/sl_main/src/rtos/main_retarget.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_main/src/rtos/main_retarget.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_main/src/rtos/main_retarget.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/rtos/main_retarget.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/rtos/main_retarget.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_init.o: $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_init.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_init.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_init.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_init.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_init.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_init_memory.o: $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_init_memory.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_init_memory.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_init_memory.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_init_memory.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_init_memory.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_kernel.o: $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_kernel.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_kernel.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sl_main/src/sl_main_kernel.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_kernel.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sl_main/src/sl_main_kernel.o

$(OUTPUT_DIR)/sdk/platform_core/platform/service/sleeptimer/src/sl_sleeptimer.o: $(SDK_PATH)/platform_core/platform/service/sleeptimer/src/sl_sleeptimer.c
	@$(POSIX_TOOL_PATH)echo 'Building $(SDK_PATH)/platform_core/platform/service/sleeptimer/src/sl_sleeptimer.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ $(SDK_PATH)/platform_core/platform/service/sleeptimer/src/sl_sleeptimer.c
CDEPS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sleeptimer/src/sl_sleeptimer.d
OBJS += $(OUTPUT_DIR)/sdk/platform_core/platform/service/sleeptimer/src/sl_sleeptimer.o

$(OUTPUT_DIR)/project/app.o: app.c
	@$(POSIX_TOOL_PATH)echo 'Building app.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ app.c
CDEPS += $(OUTPUT_DIR)/project/app.d
OBJS += $(OUTPUT_DIR)/project/app.o

$(OUTPUT_DIR)/project/autogen/sl_event_handler.o: autogen/sl_event_handler.c
	@$(POSIX_TOOL_PATH)echo 'Building autogen/sl_event_handler.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ autogen/sl_event_handler.c
CDEPS += $(OUTPUT_DIR)/project/autogen/sl_event_handler.d
OBJS += $(OUTPUT_DIR)/project/autogen/sl_event_handler.o

$(OUTPUT_DIR)/project/autogen/sl_iostream_handles.o: autogen/sl_iostream_handles.c
	@$(POSIX_TOOL_PATH)echo 'Building autogen/sl_iostream_handles.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ autogen/sl_iostream_handles.c
CDEPS += $(OUTPUT_DIR)/project/autogen/sl_iostream_handles.d
OBJS += $(OUTPUT_DIR)/project/autogen/sl_iostream_handles.o

$(OUTPUT_DIR)/project/autogen/sl_iostream_init_si91x_uart.o: autogen/sl_iostream_init_si91x_uart.c
	@$(POSIX_TOOL_PATH)echo 'Building autogen/sl_iostream_init_si91x_uart.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ autogen/sl_iostream_init_si91x_uart.c
CDEPS += $(OUTPUT_DIR)/project/autogen/sl_iostream_init_si91x_uart.d
OBJS += $(OUTPUT_DIR)/project/autogen/sl_iostream_init_si91x_uart.o

$(OUTPUT_DIR)/project/autogen/sl_si91x_button_instances.o: autogen/sl_si91x_button_instances.c
	@$(POSIX_TOOL_PATH)echo 'Building autogen/sl_si91x_button_instances.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ autogen/sl_si91x_button_instances.c
CDEPS += $(OUTPUT_DIR)/project/autogen/sl_si91x_button_instances.d
OBJS += $(OUTPUT_DIR)/project/autogen/sl_si91x_button_instances.o

$(OUTPUT_DIR)/project/autogen/sl_si91x_rgb_led_instances.o: autogen/sl_si91x_rgb_led_instances.c
	@$(POSIX_TOOL_PATH)echo 'Building autogen/sl_si91x_rgb_led_instances.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ autogen/sl_si91x_rgb_led_instances.c
CDEPS += $(OUTPUT_DIR)/project/autogen/sl_si91x_rgb_led_instances.d
OBJS += $(OUTPUT_DIR)/project/autogen/sl_si91x_rgb_led_instances.o

$(OUTPUT_DIR)/project/main.o: main.c
	@$(POSIX_TOOL_PATH)echo 'Building main.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ main.c
CDEPS += $(OUTPUT_DIR)/project/main.d
OBJS += $(OUTPUT_DIR)/project/main.o

$(OUTPUT_DIR)/project/td_buttons.o: td_buttons.c
	@$(POSIX_TOOL_PATH)echo 'Building td_buttons.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ td_buttons.c
CDEPS += $(OUTPUT_DIR)/project/td_buttons.d
OBJS += $(OUTPUT_DIR)/project/td_buttons.o

$(OUTPUT_DIR)/project/td_leds.o: td_leds.c
	@$(POSIX_TOOL_PATH)echo 'Building td_leds.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ td_leds.c
CDEPS += $(OUTPUT_DIR)/project/td_leds.d
OBJS += $(OUTPUT_DIR)/project/td_leds.o

$(OUTPUT_DIR)/project/td_net.o: td_net.c
	@$(POSIX_TOOL_PATH)echo 'Building td_net.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ td_net.c
CDEPS += $(OUTPUT_DIR)/project/td_net.d
OBJS += $(OUTPUT_DIR)/project/td_net.o

$(OUTPUT_DIR)/project/td_status.o: td_status.c
	@$(POSIX_TOOL_PATH)echo 'Building td_status.c'
	@$(POSIX_TOOL_PATH)mkdir -p $(@D)
	$(ECHO)$(CC) $(CFLAGS) -c -o $@ td_status.c
CDEPS += $(OUTPUT_DIR)/project/td_status.d
OBJS += $(OUTPUT_DIR)/project/td_status.o

# Automatically-generated Simplicity Studio Metadata
# Please do not edit or delete these lines!
# SIMPLICITY_STUDIO_METADATA=eJztfQtz5DaS5l9xdMxezOxaRZXe6rM9IavVvdpptXpV6rHntjcYLBJV4ogv89GSPDH//QDwUQQJkAAJgGyP525ti0Xm92UikUi8//FqdX3z8f315fX938zV/ac317fmxzc3q1evX33352ff+/z5my8gTtww+P7zq+Vi//Mr+AQEdui4wRY++nT/du/s86s///D58+fguygO/w7sFL4SWD6AP2f2wg+dzAOLBKRZtMjsyzDYuNtF+uQGTmg/mtunxda2sVj4dQTi9GVlw3/Dj0tpr7Bw+AL8/99tQs8B8Q7BxvKId8o3XQ/s3nsbA3B3f7sq8B8w4hYEILZS4MAX0jgD+KHnBo/4ycbyEvjI6BOdeKZvuYGZpFacmqmVPJq2EhQ3TNIYWL6ZJQjpix36ipC8cAsl+34YKAIIQGo6YGNlHtTD8jKQyEZ4cjeuGYMtdF3TWStSI3HPl8/mOktTiBK5qqxFwLiBm5rrNNjXCbZUChZv16YHHC0YWCN1tWYTxr6VpgiorK1qwOwwBipE391fmW/AF9cG5vnyVDbrdWjFZTlnUCKsncog0jj0pApXV8G3kRvmxNU4P5b/ECkPUbAJhG164v6qxDUrGMe3lMrP21cdCAqb2MQDIEpdH8QjAb4z8qSr/sgNbC9zwEcrfYB/ZrGLMNPMccPXRpG3GWVqlsv6rnyO//pGTXZ5D/zIg7rJyy+tLA2hxfoTzIt3Vx/uV3ur9xc/LnwHA64z10vdoG7ntvG5AvJl6EdhAIK0TJPkiMbNSCHZtK3Ugi2YbADwBQl/sALHA7Fa4bZc4VUDnsuXbvqWfFX8ccrjBjA4B7ZCNTBMEd5gdFOrTg1Hsj6N/Le0mmRtGChKdNmlvkqVacPI1Aa3UDF6Zq7Cy4U3MMQObcyqdkBba1a8cANSy4GheYImDb60KBBckPzW7V21hCv8pzRzJy7MSVzbTV/MxHk0D/YPThYniyXV/I1PUS6DOpS4s0f5oOcz5heM7/J0tOcrxrewTLk+ZIUQKw191y4iRsMlYJ/C2gKUT1qBERnYoMC2Dg+dk/OlfXx4Dh8Spqr+MnKVDMjOIEDa4Yaf6tpNFfMsEMaQtP3ETcwwOSg6GYoZ0+BG0HdrAsFzMaiKBvOStEoiFanSCz2qVEIH9ow9K0ncjWvXhz+UFQwdcVzZ6NaCCTmmLECQ+YqNX0KMoQlVBrHqgLMDGefdOiKNjPiCu72upzqWEDDj6MZAOdUcYgxN2EGDqZdiojuQUVQ9GNBVMy0xxtnUSrNEuU1LEB6qlJyerU8zG47H5YmtRMNWYxjIk5rX2ArzGqWq9EJLaKTUlsUOZGwoRf9IwbOv2nkaUBJCq1rCO5DxoVUx0xJDWrzie6kZzoDvuesJeszAV5MTYH1wq1BDGOwMhQwTDxEp6N232NaRJvYMGKvQJPpA3yjGuoUcZFRLSy2/2qi79Ppc2McoAcqaXQfkd7w++rClS614C1IY4yB17dpQ8AVqFX++xfInoVjT6wuy63HLekVaWgcc7Quudv7uQAVE8usxqThesTR9iEGTzqrqYy6+rI0F0viwglZ6PQHrUR/vCk5n2FhDTUDgDCjj8e2ZdMfrL9FC3V3QrhbzqS7nArnVfPSzEvXlga4x1KNm0nLt1rUoK8KiySqQ5ISYCjmJgI0GvvUpQceWo9YD8CIFQ69sXXaAchRwgxTEgeVpVKEOObtMwofdrygMvelziZKJsoBdApQRug741WX07o6+Kk+u7FWmxHXE2TlysZVHvx83hMRpmAzOlYhCxjuTys6nyjQGAeFKgbgbLVjhwDswQ6FvzUJLBrUo3wQc395gcY8w9gN1QY2mwQ5SQs+7LlFhm1lTooUpqSTw4lMYw8L4RbtD1XBllUldrNaCaQB/dU1nrZqrtluRBRKAcuOKTg2U1kjdRaHag8flMuX+n+nT8h0XhUGzhNjNEdZBJUTM2o6qB6Wdv4YmNOSvL2DWikOD5aolOHVQqT6gT4sm6nShpucl5s/sH1pr0NEiFf6l7pddC+MZ31zn2w+Gzcz6e1EcYrcYPHefr8PZ2rY5YiYKCzGQ+kahj1FRMxoIg+fvrdj/cuqbfpQpIkoCSF97xlh95YAohjTRJn3Lc60EjFheR1GvD4hLTZrLjF+0SmHbFj2YX7EbRwG9muQB7NJf8XEA4HlErk6hRoodbDVYTRVYrJA6hBVeteYfySVVE9rNaWgTU+rSiNfozJ8DtS0EpUzD5GCs+TDxRqEWYgcUapiYqWs/yiVVEzqqTBmlsAqzmHsBVVPb5CXB3AZ3N+oK50wMUqwaN+bPlDYxAJ3jxK0v8q63aGVwh1eGsZv6ShWNnLlRUDHE9vE1a2gcZqkbjFg7yaJVlzyAWC1bcMAGDS/AJm9EasKiycYZQDo/gWELNY8UUG1KH0CwPPhNPrm65AHExm1AYZES2XLSnCoCSQJxzXW22YxJMlnU2vKHkIwyE/Ye0jB9icbk7UySLfkDScKWwrY8zwwyfw2zVzVMKSAD6T7FVhQp41mXPoBgFMaptfYUhOy65CHE4vDvMIYqsFpd8gBiv2QgU2CuSuwASgnwowcFYWUndwgpfGCZb8GmW0EhNqUPILhCIm4U8WsIH2Q/vCRRVZPREj+k928lI/o9LGal1CGE0DiugtLcyVXRGysj5bBh0xvg31iB2GJzwmgPwIrMo+HduabRSnWMgpmxA1C9BXblei7k+t5ai6zxoYj56fl8+fPYmRlkCAVmrSlpFEyNEmp2U6XvLi/HlMTF3Y15eXP0VkZR4MZCXmyoygOqaJQ8DQJotrNJVBtVfWxpLluX2BM4O7q+0ug0pQpRGrfztkmFb48tNfOUxqESJ0SCzBukkWmJFSKFUgaJjlKJEyORJwnyWFTyWDRER+y7Z4AZHw0fK96NrI+3ST5mXIwWE4JVZGQjZilKxuMmKhp6l9MCTeEDUuRKhD9ucXofQ59vJbrEwXzao2bBPrkJgGoFwE4P8ZmBR4sl34GB1RmGArMCDuDYp0451dDjzV8p354vn8ckXL6djV9j33mmoqisBzcauSFR8g5Hhlj3480nNL4p0hMbAuGEqQz+JBARIuLExbNxoLxgAV9XwBPDcfWylrZ1cnzsbNbWwRma7qtqjpFXCCP3cAM7qwE9Ds9hG6ik8bK8ypJGpbDB5DRslyanJdzIz0wrcvladXXaEzxkaTxwH4hKQY1UMy9vbCiNBdCEHW/v9shonGaRfsWauNI1Q7U0SswYbaXOAlujbhRkJdo5AER4yaiZhLr1a2GP0VBCpZWympnL6iCOQ74x8PHWRguDCUzpfrS2EmDyT7LKUYkEla4TOkddu04kqJL6btuRyOGr8tyPBFYeqfUq10BWoh2RLWrWr4UtXUMoPaejUTMCU4VG2isagalCI4EjpqVpNOTEabGoMUmdInDl5+T1pF+fYk1Y+Xrlt7rpDhVNWEV6+V8i7UoVmJPl3uM+HnExCbdMJd2A6i4kztU644qcPMK7hquoU7nOdITTnVYE6ty6kbIGaBl2Vt9p352nTKDKD4Lk5aDhGl2ZBPFsz4r5Jopl6dnL5DcTLhl3os/R3QNYdmYUu2HsolvGyvRJg18gnMr/2TQmDzzU7n6WNO91VW8rBvYoA3E7hE4l2RTmfdwmo+46sYs20Eqb7Mz3NmOhcoPM5c3qeqVi2vPNeLKd8kWWYojAEJUjVwLdBax6/KFwGKNe0gYuHCMnUa2kaHFSOtNZoL31rORhXgaoKOnQ//rgcl7aF4R06L66uJ6X7gUhLbp/nJvuH7Xp/ml1cXc/L+0rSr/FtQ7yM9eJmy+pLVVDtXeT1Mx3EqpfQ5FJWhYJrUdz09wUjYSEhqCpxhReJd+pPr25udCvR4kqU5Fp2iAp7QytTFSOsbDLZOyQCq1M9GtSwmodECgtMOKqMW6hI69s6SYsZTCR6g/1O7eyxIpTDQsYSw/pvQSsQUjCULu8Ra1KpseEikhHYO27aaxJSFpq32GCuVlAjwHcuVmASWgW1VTJFKboBXD8kpUGePr1RDojfPt6NiofddEDXwm0u1sSTXKCwFG7A6TfCAxGs6hADE9V286xjKIzzFHukqIzUuut+R1cE4R51nVg/wIB3vZCfP5QAO0qY/ZLc5zPF2sQSmgNcAQyuYKkRWoWPsQoJbUxjmYQnfWbLCViNVyL1CxKSU0qN+CyD37paqs5cblFuUTrJYlT3Ukd+wYRKrNZeBOjyJTW+UFXoSgopvb1GOLXoygsmhktCYxDX8mKHWWbKRFh23vUkyrvrFOtO67jK1lOjQFitXva+vSL1W1sQ/LBNnL5zjJTpGBFQM0eI6iEG6hdmdihYA1enYOq3RXW55/q9odh79hkidrtRn3uWRJQpuLG5btiSJGCBbwy9baR41tTKlgRUKZiFD6hoQrry6SeSrJQp+zTpO5awCtT75ckcqfUr8RXpmA8XWtYg1emHj5J1bxbLZ/h/6ZUtEVEscr6Bm07FVa3AbnC4b7YUZWiQ6+q5FYxm7jJzFS3mAigvHBiakXrPNQp7EVJgjqrk2pbJ/Eb2UcJC86NHkBseea4LVQM+cr2VFqOnpHTtoGq/ZQFBelOb2XPZgw2IAaBDcwvoZfq2DHao3AnKekmyGc1ssixUrX7p3u0bvJQc7RVPLkrFxTUHKpgTa5eQUGJevkA3MQKViSUqBhGlh9NrWJFQtUhZbrm4jp0lDrv1lZS4GB8hUr2H6c/SkmcfE+sYslBmYJV0j0DRetc1CiM1itPrmlJYvKzMnRNT6L0Vkdvi2L0stdVUNCYYU+ocCcptRn2hFo3eSjLsCd2ZZUT0Si9nVi9goLCDHtiBdXOsyOOVmylig/X5vFTgokaZfXMuHcpqW7WXd+Me5ezKp111zcl3aGi2mnpra5pzC4NVU5lugeTNxkFBUXq6VlV16meuoV1+VjIxApWJNSsPNO0TqJDQZVrJX4Bk8eXgoIa9WYQP5UuBUHC0eVQ6eSJKclEzQyspjUvHVoqXfcyh3wmVprPJNN3oBKF3acZRBuVwSaZg35KFcznPaZWsWKhUEnzAVgOmv+YhbJ1NiqnnCZWdsdC3ZTTxCoqXXOmfb1Zj6LK15zlsz1Ta1qSUHdfgX9kRpPWzjaT38jCuixwNy5w0GWxX8GKuqoYdC2rq5mHPHVA1aK6CmD999RMgQ/90UqzGJgJCJJQz0Q6U2k2J3V20LVMgqm0qjUSOwDMwNS2PoutKUlEncaZFxXL6yfVl6ChUFtt60LYmv5LrQohgrSOpKFudyJbULUwpC8iT6o0m5PaVmJSpVV1a6jBeVpNSSIqNJ6Brhq0bDZCk5YqQUN1WzitpjK6qzPswX2VW6SqUqmx154IM5bTdnH718qjmgbQWX/7BmQo3NSFr9lpr0dlHRetD9Fc0mXsMwrmD1bsPFkwaVYSwtdZmo68vJkhWcfpozl7LS1DsxiMHLsxGlbxmcURd4yS0XHiaGEJHeGBVTJkD7TiM4uSUdHgx9u16QHna63LBf1pKnMBTtbmGqNZOA2jcHRU59IUk9TnsnCICl1jNIvCmVHGkLwkKfA98AV4X0F/D80Xr0M99b5mmWp7ZIGtZjF35GeTKVaCq1nk7HmTKVZgq1lRqetYa4peSjfQAz/SOWFM06/BQdmqLdxRnDCiNDioWeZTneg0lZYEg3+Jwa+ytdBynnrN4uWqqgJbzUbcROOUA025OgF1bfFU2pXgytriqRQrsNXoNWGBKS0vvacGU9VTf2RwFIc2SGBbr3MFAlVXChE1uSPYatvPQVO0hq9IvxRyczUN69E1rDFQlv9Ppp3CLRz13Hsq/RoclOf/k+lJclCc/0+lpbQzZZk6Pj05ehaG0NQrwb+2WUThz8Q/aHa2ntwYeLCFFe5xtSSBOA7CgR036aOVrLFwTFJZt7s0poFhyAmJCnkO99qP7WI3zJvrpqq2N6yKKnkFqNWYQz9rWn/jxj6eJMmibWw5YHClIQqhIdVSmuxVZdLUpfnAGpfx8eiovDbz6TigastyKBhkApDOPfZCiqYbpCAO0I2PKSwh9UWXW4aMxHQeo3KFlsYIA6PpVpEAlqqTu5NtZqnruemLZuUYDBSVnGlbnreGypibGP76FMba/bWPi3zNcedgksKlwasqWVT7YeBGYdt8sALHU7h1rbdoGWR+g2liWYPLElaenBQmLy+zbWDr9C69qvaTUdXaTaXnV9sXcG0/kpP/F+aI0M2lyoMZom00EKVk+HWZyp2ppcUAL5LmCINjbUuU/0s6tDMgnVxXUecncECypu25sLRoWY56H4CRBHHIQwonJfn7M1rA6UsE1J2Rwqt+xUKDxtrSgh6dZaUIEy4qbYbUel6txbxtTFmtQ9EfCgPYc4dUtKlDwZWtEhpQwgZzddX8DnC5yuWzNZqV2oFKUsadRJs2qtyyeQiTYkBsY9nqlrXQy6gNLlc5N4Q9hNB+BOpmI+mKkcBylcLn7tqhpzNJ6ACXqxw6WHiq8N7ClqxaaqWZdp0qULnKTOF70l3uyd24Zo6vTZUG5mSTRjg4zX3SKGepcUwa45ETRm0Ov8nBWXOdOBrHZnNDF3WiAS13eJIoxSnGGEhdOeio1F9f09ql9vhGlktbTY1Uh6ZSRlA4o+OUeqqqvS4J44CN7vJkMPgqpxuGN9M9PXv1DXP7aFOJkw7uJNq0UWXltXrn8ePWgN+Ei6HwiIJvZ9IyW6Ss1EzLfXo+X56ieGIGdoSHQNQXUmmW4jmLxFcZ1ayH9W4MaaY9GlQ7HiwPFQE6dR5me+rLnLBLtfm3zUJuahJ5VroJ40n0a8CrUcwsCUysIcFDRXq5zqZSkcCXnk9WoW8a7VoUJCrYrODhLMJMqKA2FiOCSs+d53HSkUfOz3pQqLiaWeVhkQwT1y6GlnEkJO328tTSNTxAV41kIFs9TVOUDNVGTlUy1fKPplIpR5asTjiZ84UqnC56hF2Mra9hqpWuVB1fsmpZMl1tKrElq4SYoga6OrMvAWmm7n7nHiXZbGSr7VlB0aygYeiNq2GhKUNlKhMV6jpg4wbTtXRNDgoT+gk0pFBQpKDaU544VZRy0hPlkhBNk/A05UbMxhfqTDyq7+XdrTFDlepn9Gscdey2qsFV/W6CwG+wv0boqHWqlzB3GTIYVCRHxx0KUknHQr8+bXc8VKk6uY5fdazMSwmvw0LplxU4Jgi2MDuZcexkci5TRy0hlcmiMaPZzVPJAgEK5Oxt8htuhtg6awld7EIhF3UwCEr20I7qMBNrdDPUVWG1tuAjXGR0Cz+vRhB8Qfveiu3hX0cbSFDWHucJdFqYb9H77Ud5UmXdNZgsEUoFbtGbd8UV+IDr1Z6X+n5uulK5CajHnyjHDW5cLh8cGU4kreKibxiREm5KCxpIYh5C8qGKHQa/hw44B5K6E2ZtJa5t2jFw0FG9lidn+QdF1S48AbXpWig6uImtxtjTmZgZoz5FOhF5NBEJWOMaJlap17xIRutDWqm+d6uBpMJfFSswctOJgL+qUqQTcXyJSB057SiIYcOiDNYKNnKzqY/ZuM3gL281Dpv2gPU2jCRAKU9ehlPkfgmIUV4umvoFIEX104TdaGgivm7mXLNAdGCU7CypMKvRsBOZGlKAdWaJrn7N6Zhjai8SlyeesPqhX3VowUCVo4cN4hQGDdtKgZmkYSxn4JtbISr8SM00aTA6T8e+mS/hkbnfiqtKtGDnnqcH0vcfs+xUOx9SWo6FhDmBNt4F1FjGbiQxr+KgXccby10rcWmsJeeyHNTlZbaBpMmXftKje5zNrEA9bSqm7NZDmxotWAma6AvtFMTR/HXVWVc83sjo55W6Nxp1dPSKwFlAcpMCaAhnLdXkO3WwtSuAwd4BJbj5lRGKedZQxpI9gXJONNCtcIbXPeABW26b06C6QxhOUt4BgiySA04KbJJ8kRu7mgxfxgXZzJVzQxSDXiF+4ljKffL26JGpdupWO8JYahcUn5RcDUA1UObe46zTlel9u+OjWxhj0m81B4D3kNafiYiOOOe5quiAM+9YcaMYfMvzQttMH2JgwRBjbYCkMZ1cCzyEw8LgKoCW18gceKqRJCV3UxsWLnlrd1tly3FcdKdJfoOXrENVC+WLKkLFGFZCtp+4idQuHkm1JX8gTakduAZF0a5am54LADjbP5AYGUmKLfkDacoccWswFBxcY8cK+dy4vU9y47AOrdgRbhvwmkI9c5CtLbmYsZRojSVVCySLg1cq8bNOznZMZbgiYYhy23ElfnBKVkkp1sJnsbxrVdmU22Bjckr3wFZp6CbCGKrRk6+YKoEwhmrihoqpEgijqL4kcaraB5ogYwj/ApSGhibCGKpxcnR2rJhsA2MM3TCy/Egx3QbGXPuUaBh+nW02IOZckSSrf9kGljNc0xJbLRZoo82qM9ciKGXMo22OcvKljTYolW4Kkjlgw0uetzegoO4IbZyWWXcUbPFti63qjuh+Xe11R8HmWoo5SvcT3SmrwPHyjVza3a4OK83p6kIrl2sizczhCHqy3I0wROlsTSTtrvZLBjIwQXpA4EpzNkJq5W0trJm5G8lPlr+RtigdroU1MDEg5EjOCziYT5gVxGGWusG2HAzUWGcayNJqTUNuVW8oeDOrOQ2Gkv2waZfSE5moA+tS086a+U9Sizh2ScusOtL2NJfCiD2lg+c1iy1+sit0e9Or6Ap6BtEofIKxt9jdoZBuC2dmcUfBDsrKEI3jasZOKbrSF2tTiY6NgdL2G1LpjbWe7Mjctt/YiW1qxVFHt4UzhnR+CIqK28Hp5Jl4alpB9g/NiBSDJMxiG7BnbdvrhnYb0/rmehvmt56ScnVUTcgiAv7CjkcsJauUMOrcjH64Husz2Uex+wXty3sEL1gc+rdC9gw4YfYwrscbF3iOaVtYkArONBBhpmFqtcpMBVkGjhjfXzNYq9eWl7o+qt+qbMuEEWJrW0iqEoakaDFW2NHVMWuJH8CurH1qyNWkC3FDy1BBrMxybfED2KmyXEu6EDfUMONLIFRQawoXsxqe+q23XWrMx4QZwVZZWbNQhLj6LzATe3RT1W1LB84gvqqsSpE/pOydLZKqquVjgQgxBVakhFxNrmA7nNc4+Y1wJZfFR3Tw7CH1+48kJJTzwu2YjX071RC0UUkTMvAD8LzwKYy9EYtyGkRIkUJsYL/1i5u4YeAGI04nbvBpCpVV4GH6wDEzR+jnBg54XiBWMrTDBAxSprBylB9ojxrJfBQVg4yeGzwCBz7aWF4CaDrF4d+BnRrFJwZbaOrUDl/hlrv7qlt0sY1CXPruw26AdZamYTAEofZlN4QHnCHyy886hKPSeRAv0IdOoaurd++u7sy7+3vzMgw2ogCUz7vNM0CJ3VfdookD00Wk088xby71Bpbjg4XviImvfdYh/OLd1Yf7VSl8CwIQwyYQyU/jDFARO6T5Fmxk7IGiwLPtZQ5wPlrpww8Vr+8M4nntfTfAz9FjphEaEF2fJM6jUd1fjAYZq7/q20kEBeLtT8YlknadvypBgr9XjOBKkGWNk3V3f7s6GKoaw9rA99z1EGNvYgCztjAxHkEcAM9wh9GqxOQqDlSuSSYK49RaQzu/u7w0Lu5uzMubo7eSLFZuo3XDJIXV3h9ivB7RiWfCFFKBYB/4ZhSGnhrOKCAplIxmP2VLBiDCF9kpoV0JF2Q+/vhQhWCMgxcUItLO//ftzMhvFy4iR3HXsHF5s7peGW/yPwZEE6XkJuCBfXNYkyrbFGMD5+jzDjRg0U56mtDkceiXvjcRk9z/HtxoalNEIHYj2Em3PLN8pJhRa1fUdNUfdXzmUPWHJTay2WQBbCcB6m4qby15DWN7sCmdS9Qo7aO/yvQxq24FLx/k4zVT0KpuIAJxHISTMti4sY+tkkXb2NKf79QuY0IDgJPawrX9aDpwqLiObEO4msTbNRp6nLRkpussEOUzFXb7wvEZNDvDO8CS9rIqRqRsX1SM2NrBNl0sbl7crFjz9o4kxYC0rRtTWrv7ItGZMGtfkKi4lHSMSfWGu5ckBb4HdRce+RyzskEdDJ5MVyc+n81WWGDsASnfsuPwDdi4AT507/NuBvP9tbm6Pl/+bF7d/Hj15s3VG/Pmv9F85Pvrqw/3/FLqX5k3Fz+bdz+bHy/+9v724g2U//+u8NTZF8vL0OvHy4N9AdE5v49311D0mx/fme9v3/F+nffRP3y6MVdv/mLe/+fdFeTz/vbyAkq9v727eHdlfryFcq/uVgTDA14A8+7+yhQx9uXtmytop4vV6vrt9eXF/fXtB/Pd5aX5aXWF/u+NgF0ub28+3n5ABodyLqBVoI2uVmLFltOpBL29u7pC82HmX67uPly9J2xSzgaZ+WzQcJDL2zvSH9BwynBxq/dXVx/vr2+u7gihuySMW/T1T+/Ol6c3y+Xy5t39jxeideiUwF8Kf/7j/jgBP5s3l5/Mqw8XP76/Mt9CF/tP88cL6FLm1c9Xl5+Qp0mR/zOsLR9gBXr/5tZ8e3tnflzdXdwMlIzUNt9c/fUv1wJOW2cD3eAG1qBc2xvoGDJUvLz98Pb6nXl38eb61vzx9uLuDTak+deGi8kTDyUfDBVdiPhwcUMq/39+ycL0//549+bgZP/4Iv9LWOrd1V8pQi/2D4TlNYMAmlEyP725uSBDQX7WquNbo7wfemTb9zkj+i4Iwv//0/XqCpbXh6vL+4HlU1IhPt9/3r/cx//79F5IUqsthZL294/EJBX2gvXu+vJKoAg/XN3XSvD6w+X7T2/4WywTNrmwvbuEH76//kBqgZaguTZ84AYePnmGT+QlbMr/Yt7d3ry5u4ZVSLT9+/T+42pljhRSJSh5hbn+IBDKWL5hj/eKg40t5Fy0WnT98eaTefHxejW8mt+trt9f/2he/uf1R4JgDHsV7tpEU1jChl7dXhahntNL7i5HFS9dpat3H69vaTqBbeSGo8Wv/ra6u7+kyc8Pg+QFwInRcPXfXP346V3hD8MCYC7h08XdwABa+GIuBhb7p6FEcPZ9ATPFv17hFHRnioHtLsq4i77J+4t7mArdtFNbEXmFd+OcCNXqm6ubIlcYLLKVKhfR7ubiA+z7NBNmk5gv446isA0fU7/KwHP79i3uLsJW5qfbu7+g1uLyL0KZ5IBOb+5ctwIRrh4ncc/x7QV/I3p/AR356mPeZyGSV7GU+e7dj2Zh79v3b8YmpTCg/uXqXtgGAvZuOSLG/en67ur91YrsepejavlAmwAEbM3NohsoWOXurv77E6SyQuX5FlZmgVazkPBpBeObiZNZzkqDPyjDGd8317er+7srGBjwx8N7XLt4NUZG3kCNDqLMznxuWUaX3ixu9OEvJlzhhNzDNH+6uvgLQcA0rTSN3XWWAtP84x+fgPX4pz+NUfba/M+L91RNa9MMAgA/Xb+9HpGi0yne3cIO1AfYht/DzOT+by2irWPJxoCVkQHpcQO7bx/etfoKjUkBf3dMKh8wrOAy80FYEe6vbt5f/fXqfR476lx3Q+Rm5DXHzGA2F1vxy1ti/8HWbuZ21Ne4XvJ5XgpCyLLxYhqG3m1UaI7+uMZ7IKqni8xeoIFnKCjGCof4ccdbi00W2OihmQD874QwVL69QjUHx0qtKfEDKwhN24TFIAXdShLgr3vhq9dk4+OtMD3g+TuykQXtHvpuam5i6O9mFOLlAlMUfmiCZxtEkzlfaMZp6uoueNlai2HL0hj9ZT9YbtANXL22sKOsOceRguc9/0gH+KYBvom+HO0lzZEWNdBeaKWmtSatnoSbdDMEX6C083+t7NiNUgL8D9WGziwNtyAw8jfRjjFzFV4uvOb2QsnEym2EN1aEW179Vd9Ge3wDB1/lVPfJ5ZkG7OdnBvp//EerC6kA/8mK0b74ZGGh/Eu76St48JzG1pQEIuBYARplJyIDZROr0kKIgQniOIyTKWigN3z3V3zzU2PQ4VfFbZFsaNHMF6yzrYk7IgS6AzZW5qVcBHzrEeBDF63YX8BuyiK14i1ImwwYr7VaxD0fPvlerF0cSSF9yPx1g0TxTD14s1He8+GT74umec9ZnmghQW2eIRX0fA8+/16gqW6B7IJ+L5/dq6zWaS9Jne95m6gO+VEkQAad4cFqsHJC3K2WZEq0ZHZvE4R7+dNJCDEye0yr/ps+XyobGrPZ2u/9ZLXGX5SbSS2bQXZppyF7PxXPJrKNMkYi9mE2z3u3o/1X1DIquYjYhD1atrdBv+3tftNrIG3ERKzVPb65tyl/n8xq2gkK1b/uEbq9DXphD7+wV72guVrqpyhUWxkZ/t5We/VUxkTEHqwR5z2YbQM7+R79vsD/qds+qpnRe6WM19jDZuNGy0aywjaaiYXK8Tsz/9v0raiRrnjf7t1Y0fd/+OPtp/uPn+7NN9d3fzL+8MePd7f/dXV5j1bm/mmBvxrjaC26bkK7RQSLfe8maSWaTDo/fwPTKzQCg/8LJeroj+8dEMUAbbBx9hxge1Z+PXbDvv0IkuV1DRH0fox6IV7aXIpn7MwuUBgPYZL+XhpdAzZCdoVWXOT7yhauA+B/Hh7k1nXSRb78zFlnrufgiYXFNsgWtRi6topDA2vmrwlsvJ2/tEDls8A7sDyo279ySQ2rN71fUa9K6kLxQZLAgt7zQLBNH75v7ghT7U9oFEPEo+rv/+5T/wI+RTTEnvfF70pE/wWiv8zmlGJSShb9u1GFjdqR3YpbE6a1e08xTGx9vABASLEM/oEuLArSjYknF7QEDEx5a7OGMEbmfl+DYdXnYUWviCsLQ++WraXnbDxrS7sq7Dfog/BLNMC9Fz89Q2fc+mh/vv4ER6CoirfLwvq9qCQ2crOIG8Ms9HPBHTal0uNq2V4xl7GKW+gZ/lGJ23ty04c9nFjILM1Z082PDsExolj11mRZXEEZRs1lKE/b8+Wpv1wu/W265pt8U9d8iIqz3djOYBIGszIQOCCwX4YttZqPRgHMOpzWCCj/QqkxLYYENXatj0DRfFdeeoD/+ua7Pz/7KJ9Hpw1BKvDl5SI/IwNKCR032MJHn+7f7p19fvXnXEDp9NXuhsxe+KGTwQqcgDSLFpf4jJyP+WsfoY1/zIk/uYGDNj9unxZ4BwaUAGVFIE5fVjb89/f47p68QtWN37hIoyYm8aJ8rREyTeoGla6faTdLECUaQV7YoKsURD/84Y/FwVcg/hOiVf4I/zs/heEPfyyooUHn4j8/QEJ/whyKkxpQBI8sNDuV4niORZiOG78uheAn8MGf8gewMAgamgqoWJG2AmmKVwwKlYyhjtc4l1FILIJJE6p2c+GT2YWpRlSqxkVUxVQUrXFtvgpdHq8nS0HHTcZEnV3YsV3eYgP/c1iVLdvq7qumyOrz6ttXxQyReXd7e//q9at/fH51d/X+Am9Rr//0+dVryOHVP+EXq+ubj++vL6/v/2au7j+hE2TyTaQr+Pn/wO8L5lf5hTOw8Xj9P//7LbqAxw+/AAf+iVuQb6sXV+W1z/l7eUlivLKkX9/c4IffQFcJktfF0++hBq8e0jR6bRhPT09l8wAjlZEkRukBAB/tBN/cWfRzYT700HXw37wejT6JHJ+Q8QNy4+IYNeTCyTeRlcIIlyMt/h39ExXUzvalPj98frUzA9QYSfznt+NMWJ44ZryNAUBnyFxWtyN9W/2Gjgx7k2dhMOMif4Oq125U2j1PPBMffF78mOWjTex30jj0Wr/ia8cZ0tGhFfnnrZ/KmwXMLLHi1PwCy5glxQu3Zn4KXdcb6EIPVEjOTjTjbdTPwTdJp2ZqJY+s1wKQmkW7YeK8Imm9ku8YzQ+2NtGuTnOdBvssgdS3l1xvd5Rg/p7jW90v4KJ4iPolFecP872Eteh8E9oZ1jW0Hr37vdwNuouZfJP+ym43N+MNvL83Blvo6aazrr01m0iV2UUF/xpDVbnAI7+nbG/1/uJHfInat7ufUKi6rA6YLAqoY2FI7Vccb4ovTdtKLVjzGwLgK8TBqWhepevn1tdV+MjfSNoCWm+wZeAK4gZo6bfd/2Lh4NC/O0Cbb7ZkNuJMid2SyHiPIW9X5XsEtl+cV+W6Bz66AAp81dUL/t+iyHpd9Nts7FtA3IDUQqtmZ2Rk4k5HbPDyDN38RkjDchwzDSPXNlESv4iCLeO9KPLQscGoBcGjy4kZ2JHQ+0los9+HTVKACqDvBTPJ1okdu+sOrg7wYNfcLL5AtmW/i65DMMFz5MFyj00/2bJfxWWNtNhpzu/DZDFQ7iv9troq99vqjtVvd5dofktc/fl7ScouyW/RwK2PNHXTFzNxHs2D/YOTxcliSbsoMz9cs5pyfxj2PRr4G/hpMcww4HPcc/GPxL/cXTRqxf6XU9/0o2yMlMoGpi8uBl+ekF9dV60eMC3PtZKqMReQlv6Ke3rgOeX6lrznNKcRJgcDvg0TM3XtR4Ev86CCPkQn4qBv7c5vGfeXVkdQ++i6zR78Phn9ujckFErsLMepQ3F7qp2fkwQEP8tT4C38OEoEPy0vjy0HI3jVbXy+Qv3CG3QgUp+TsiRYaei7fVGD9XFlt2Gf12qaU53nNFQRojCGiUBLBQd+WqxuK258GSokykx8tWn6EvVGnS4hsCbblueZQeavYVwfIQlNaUfDRZTXEg/9HOap0DOGouMLWgZ+m8D+zcPQgsyHa/wx9bLopo7yJzQuN/RTNPgjyh3XH7E4SL+3Gj3F1hMkUEm7Af6NFWyNB2BF5tFQTisXvh4G79EdKyv3p+fz5c/4R0F5uRuKfUMWv9i3qNhF26OivLs/6r+/PvFMtGgi7gujfJJ4miYuSWtXCqEqvShGWKXIDB2YPnvQavktOv05OKdYeQS5+iScsuK+eMwlB8CGTYachKPF5xOUWmnWFy45JcEe8VaCJLfmrrAfkk/SoBH7JJVSmK5010WXxu8CyJhQVEhq1VcZMvOJOrTVwpchL+FoNPkE5Y4zXlK34wySD3zPXWO/Af6IINASY+KZ/6FtBPV69tocgVSprmyxRbFXUgcVTJ9UWO756UTQvdDixVEgPiw1NDhQWaR8MM4ildiCeyV1FNni4u41TORB4LQMhObKi992xqomz6VAF964m5uTJc58AF40tA1gS8XHKgTWyNJsy60+QLvKUUsjBWBXjlIKq+YW6Ojx0TLRKH1pBLzSAo2OjFacKhVVmDB+kS8871rIkYvsi/srWHIZleSYuYwblZmVSC3NLF14YWaJcl1FzkFIl+MdxG3OxMoVyZJdFaKrHLCSPLIUG5LrpNGlBQXx1DF384Hwj3zxQtn7TxurluDfHnBqvwZVxYN/FD2f/G98C2o+tXaImR8tlmi6YXcPKl7GVt5biywbJy6xtm2MCOoKvAECUQJ0YI+lBaWEkeVHEuRET74EKb+A0aaGUuLk6OxYgpyksahxoBR849YYQbhlqZyQ148bI1WOg+curMZIgKic4orF/LKOoTJCvGIoHcrBBQCc7R+Y9TkIYRnRqM8HGgCVpG95Xmib6QOamDcTawPSF9FCLaJyyYL3a9ad3DhWo9v0sHpoK5KgcfgE45P3VAiG3SliTFeiXGKUUqLc/EXJclGQsO1IDWkkHB9eoEBulJANumTZMer5ZoGtQHp+R48a9sWKbxWekov2v0Sy5ebmwD9LFI3inYvuE41i1PNG/+WEKXwW+RlMFF3+7G44Vqu08f4LubgIw4HpMM6J8ZIz+fLr9UGudLzVAi0yw6UvWXbdseSI3jXoudnXmawKTE6X4KoWymrzdgnAjrVMe5QdvtqmjnCNluKa+UE1QBYa3qdRtlhZ0tzIIU9+AF9DqzjD2EVrqFXAlMXBgBprMSd20eLHYvFY/peB70A33uR/lOvT8j/NSzkJgDDuW89KHvTDXh9c6gddXVxPAPpxAlB8Y6gaWA3++k6ZzZS5nTLXUmYKdI2zmjCHJavhjN1aDWmpNebBip0ndPdR+SAfDSUTjPyZckwiPSgwZZmwhVnsMCMVLR6q07REJVQtUWXpGoHYjR5AbHkVLtLSyiAU2IAYBDYwv4ReKitd6QHOL2/PIgdtmFOMhTIlyxnfG+eAQVLQ4YoSRi140GI9So0f5+JAcSwtyoANzP21AKGd8TqAtpHjW1qAksjVgeMeaPEE92B8H5kDBs946QCKnnwdML8ALU7wiyZnQzj5FhMdaHGgvGXFMLpCQqInxGnyhUQXDp6i1YdkPgDL2W1eUYpIbJNRipRp8nGEU+760oKXWBJmFnuAqo6Gf2RGSosLdWvY3QyF/RsETHQzFGOV3QwNMCjx1wCDUnINMHmmrAEoT8U0ABUBXgMSsUtNKRIOt5pwqnCrAy/ZHYs0HigO/XJQrsrLLfvRlZj3USDQI9t7lBfHWRgSBxxYEPKaPgaC3BEAFojU3j8DZOPK6/ExIOQOLjBAovAJxGZifVFeLDL7yAwIqR1XBobMbiQDAu/3Nu9Wy2f4Pz1gclbx9EHVlqsrA5HaNenAkN4tYWF5UZKgFkYaULlAP0/Q82PZY7JnQvykGJiYeyGBZWUGfXsr8aGLkutAP2aiDdTVq2lz22ZdU9lFytpPqEhHykbD3eZUtKwKBI68VJC9rY+Gqsi0NdT25kf5mB07nWqbhpQgtjZAIcByeZzcbmW+xhFffV3bNSRvppsm30kkt8A0ELRMVylA5En0AZp81fzlJ9xUmDi0QZKEEAoEicQ5cRpYDLZS5wnoGCn8VmQn3SAUiXMDNPnwQaSjRFBFN9HIi+KYoiA7paA8PTnyhibqALvtdvKW+9Dk46ioEgBFRZXyVbV91VhqrV4oxanVC5U4u3ohCyULYMKFToGN3DL9zH8ypQ53UWDyBEjmKi4myPrvKXYFdIFOFgPZkZKJK3PMgA2is7igA0rO9thQUidN6zDE0IDM+T0mCMMBlePKnOBhg9QcUDnYzgHVQ0mdRiph+mbvldRjHlBZe35FsWu/69KdKOYm/pgCf3Jj4MH+kWE9rPOzojYWGsLarSUea+EeBEkb5PtQsB1VIlRH7SuRPnIrZY/06DE1/a0/ru3qwUC7HVXKR0JhZTKrrQ35lS0qET0roF7qpQ4Nn8eurqagVBp/oQ4ALdd8ej5fnuKd3hpgxud+DKCyh4OGRpHj+Udoj7mKYExDCpUhoYONiuFtDRBm+ZpCrCKjFTgPayjG+DyvE4WsPFJgQBwHYX5AC/ovORUlF0pYJpcuhfLGjX0c4bNoG1voghLyQX7MmEYoKTZ7CJMU1e7iea2g0eVFJvpZjk6u7UeoXNAVoNHubGLZUqUYBfkluu+pfn4Luv7J9lyAL0n0PHTcq7lBt3Q/hfG40VdeWInZag+S6JFbvVj4pDhXidxi3YLwOWcislHFw9RdmQXQGBdQIBhX7iqaKwBwwxSFikcgKYcn+7toZ5IderIdf3fkSuQqdRzB0//4Bcs3CL7BV2YSvsuHZXt4Hu1L4ijwj19q0iccV6JtfpJo45ZbmYAuRpQaJQv5RVKExNcDsZQ2uA2RF4hK4bQ2WCkezQEUAOZgCLY8QD0/GEoBllvTTrI/uLuFO5VnV09k+XUniOy43geHNjrIagRJrLKwdvaTVkg5dRz60XgS9GoTBFs3AI3oTXlDnqYjSEi3ej8XGguZg3DdLHbdcVaxaPCNXhIy9jeyuBD3zNM8hHYRvUoKFGuQFORYAefYZVqyThzJSQIhvkhe8TNlfd0uSMmhm40kMY/uQFFXVC4JVLscUw4KeUAlqY0cv45bYwMy5RKdD4mC3WGSyw6tgcJEvefFXWhMCWPqaYdQ4ZrYISsGDlpAankypA0c2WALFAsFNDmu5ILArpangIWXDPOzoi5gcmsrcW2iKMbLHNETowllm5FXarmzADWTtXAJezvOmrss2EJghpOeQN87kSQLihorKYHBSWDzMEuK2EAeS8oLfzViiMgEFrdU975Vo9lefShblhzB+EBIqypxnZeoM0NHQZWguV0wGFBgbFEDAj6HUCeQKk74OhEOmdIFDmhTuqW6RfngZR+iGSWfaLlFX0gd0OrzyJVjWqKJbdIdW0N3Q4gSRZUtOIjT/JpdYCZpKHBSPDcEbJs3Lsx5JUmm+q9U0UOKDn6bX6recjLyMb+n8UoU9eC23FL5BlMR3RmDXAOH+igSqzuEh41SoU/z0ZQGw/pDIX6EtJIdIU2E2y8ZyECroImnQuw45A3wG1JqqTTJUkTrOIT1N9iWtbji2XguxJFT5gDtm5JL/ZtsRSzQ6vUJMaL0GcXbXqqcfOhi6IIFusx8v2zRGoyUJV56bRlDvKvVvRQvbaJzStpknCwu/4tBEmaxDRKj1vInhvWUVGuSds8XEfAXdt+WoH6RUex+QQnGI3jBItG/h4oMU6tFcagsdPfRxgWeY9rWcEG/ou1Fa8tLXR9VlxGi7Fy1gd/iTwdD45KSIKIs4yESgBUN/tZ/gTHr0U1l+EYpa4wuKNME8SiD5iJGkcBDz/WaLUmUBFLOFj0dU11Q1MO7MgQEPKS+ZzwAzwth/u/1bKlvfOaF274RtsYXMLB/cRM3DHoXlO4+DNMHnLI54HmBhKDv/hd+6IdO5oHPr15/fvUdlItu93p9c4MffvPse0Hyunj6/efPn189pGn02jCenp4Wub0XsP0wksT4mL+0AKhtR29+s85cGLsC/FkaZ/lD18F/Z/Yix13ku1GqRmiF/0yfIE90ztP2abG1bfxl5PiEqB8+fw6++eY7F11PhEyRfBNZKVqRgt9a/Dv6p4Fe+s5oqPUDNlhBDyqOJP7z239Uj66e8Y1HCfzpf5CFYuCHX4AD/9zAvhvYfbvKTYveg7xqnBMvWs/Iupe4U1vI+Bgm6Y/wY+crtPJsLPq7LeXZ0gEbK/NQzUfdneQrNOXnV1aWhlsQGLDm23hVLTBggmtXC01ie0bhILPL7ycw9f+++vaVHUYucN6iwbtXr1/9DzQ+tB3aUI/tjF6D3xXCPlrpA7aXXdyu6Jm+5QY4x07N1EoeyeVNYezC1tTyqu/wU7RXGHKHD5bfYlHoqCD4197B2enp+dlyucQ+wE/jbQzA3f3t6nIE9vJ4/wCinxyeCIKX0xZ5xTG/WF5W9VpFORwcnh3tn+0fHYtzwL3DGGzRilNnPaYYlsen+6fHh4dn5+Is0LFzNmWzqRiDY2iBs/2zw31xAo1TDL/YoT/KJc9PTs7PD86GlEixVhbzGENheXK+f3Z+eL5/OpbD2HLZOz/ePz06OTw7GMoEncQ6xjUPTk6QNZYDPAMPc41S/nz//Ojk9HhAgEDVAu0jRbHa2fnoKK9Ynh4eLM/Oz46GlkV+hXDi/jrOLMvl/vJ4eX6+PBQkcnd/Zb7JhyDRfd3DWozl8nx/CR1iQP1ch1bsFKpncX2TpKgFYEGcn5+fjaCQxqE3rEZAFzg8Pdk/F62SkTsqFJycHZ+c7B8eDaiI+FAUrPkwjff3Dw/OD08OBkDnjo8JPETmSBPsnZydHyHbcxd8mZhevLv6cL/aW72/+HHhOwOgT8+Pj89PT5bcdb9ERnXushpjHuhxR4cHhwfHp8JqwwKgrbcWtPrR4dHp8dEBf7ipwVeRN2cwNE07Oz4+Oz44W3K3BF0U7CEUDk/OTw8Oj/lTNBoDN3DRcjI0l2QPtsUpzExOT44GeQPJpMhVdodDCWfPR4eHp/vHx9yhkIfKsAx6f3lyBtslYQeB/7eAv0VoBBR1Z8WhYcJ6vKQFx7LH3ITeDUpC/R0fGJbjmCnsFNpmYPlgEQXbATzOTw5Ol4eHJ20L8POIIg8NAqMeTRS7MF6hMwYG8oFOug+7V8t2hRnDJwntgXxgsw27m4f7B+16w02oGGEeyADGkCPY2TyiJJCiDMwkWyd27K6HegvMI05hEnnYzuK4qTjAAynOZBEjNDQykMvZCcxnT5bnI7jglZvgOfJglyM2/WQ71En2T46W55RuMDcTPMZUHs8xlAXsgJ4eHh+etvufLB6wqgyK4ctj6JIHaAxICGpIjD49Pz07PKO1Wyyk1dW7d1d35t39vYkGmoa1DCfHZycHZzB7EihTVJLD8sQzlJ7CVJE/6uWp6cCsFKZl5zA75wZDY4fD/OQA5l+opeNtX9vzQQMST5R5wq7m4A73OktT1HaM63YcHx7B9BNqP5IGTnTWabA/blDkCPbEDs7PRTv/LDbLcWMRh2ewU3R0uC86glzRibdr0wPOqEGqo6Ojs/3T/eElVJLARhllj4ODw7Ozg7NBxbO7V2OMMc7PYE/l6PSUu0R4Zm+G9FNgr/XgCJIZ3Wsdgn9ycAT7SMcHQ7omjXpSdtcGmmH/+PCc1r4O5jHQMU9hcnN2cCrcQ/Lc4BHEaCWduQovF96Qhmrv4Bgmv6dL/tGrmhmq1REm7AtYXjisXsDUf3kKswHhERxKkBjlETCzOzmH1hgynMIiMsQgsDhOD1D6hyclV9c3H99fX17f/81c3X96c31rfry7/Xh1d399tXr1+tU/iBYdC/8HmvpE97Q4qxQ+/qsVu+iqvAQ9fo3+gV5A/3uFeXre+zDvy5WPX5f/gXzrtfEpQSca++GDmz4Yi3J7r4d2e+HPE8OK7Qf3C7qSyN6zPXfvy8lif3FwiP5GK6iMtRuUv5X/XsBs1bjMdU6MK/gkSoBRAn9b/kf0uL3OUbDt6AQNDootyS/AilvyDvYPTtocrDi9jdrWSdyn7fny1F8ul/42XVutD2GhJPOxLWTTYpjPeK+cRybNxPVRXx8tIUert5CBFieLZUtSwRdqMx+Nd5xKCv/M/4Fq35t8lvr3GvN7jfm9xvTXmH/Cpgg2PP91dXlvrm4/3V3i1ue7Pz/73jdFQ/b951fLxf7nV9+AwA4dN9jCB5/u3+6dfX715x8+B+XComJBkR86wPu+YzHRKs0cNyzWEr36phgLflnBEgDfV40xWgiE1gFtQs8B8TdonPb7MncvfkO/QkOWv7WXyHyTxe73VGtDRi6U9W8H+4gZ/NcGNePw39XBskat9TWYi3AMGpHOJUOyOXWCseh1LyFRQLEbkEWTutRGATsqDosUfSWUAlZ0IBYt5uIoBcyYWCxyHYNDCuh1oHERpA0bqaZJwxQiu5yA7JKbbHvMSRnHNhQftcZIlHJ+DbyuGNi5rkpRPOzEZJFtLEBTQK2BQCXSXnUlm0gbgWURxgosBZZhIPUSK9dlqaRUYlDJqG0P+OI/uWBLgSlIgO6IRF+8pSwg0eG6KVIXVipjSEXrJkiuwlXGjITpptRcJq2MVBOIj5b6NLsTj0mSNkejghwNJyf1nZF3Qmkd0mKouNYjJX7ezfBUbzRUbE38SNONZ5apsnpdxQbD5lJO6QSbAMxGnVzWKZ1HG4Kd51AmSKTzYQGxWLVWnqpg1ALhY6PCsWkgvSMetWWxKgjRcLg5KTISDaeXU3vlrFJqbTg+huSKWvUUSTxhjlrMSOJxjiLUZlhVMGSjCfJTZEE2Gu/ogRYDUuFEGSo1IRWOypCyzEE6LQoGlUtzUbp0Ik2A/sySNd3EyDSrexzzaZVaskl9rfYGZZIF5ebEG6133MBuvND2PysNfdfudjfqtBe0rxUYkYFNAGzr8NA5OV/ax4fn8CGhaPWXkZMuTxzdQRs9JNduT1RWxLDA7aNn+4mbmGFyULsBWjtXGoke4m7tI/BcTEyhKYMk7ctN1SjRS6i3JEIHmLZnJUl+cE/vSJ6qwqDz6C+PefBnEumzPwgyfxKDl8B9BKFCoC/FUxXuKuh+L54uivDGDtzrdXv7sOpoVuD9RGMwEckcuI8g7BYUR3Zpp7iD7iXpwSA8DccSud+O5cWVE9ixhCZJNobsSt5kDhn3Z2mtxr2zAyNbyeKUbRqJURnGBEr0EuJsQKaw/w6aJ+Shf6Tg2Z/GVRoEOEPgFFR30HwhcBKOJXJvdKE9IsMN8D13PbLfCHydrSpmjCNtDbezsIr3TLyNQFvvtsWzji+h5Ir7BHrKrhhlpBRgb6vDHiPV5PXljQklbOn/dRrNgu8Y2I1BasVbdF1sihazzkMHCquWL9OyBq5a2lGCeupAS/siQarT6C1Bdyas3U7a9NyOJ+HDi7fkVFA026jXr3PQ0qsL/P5KiZarPQHrcWq2FYlhlQ5d7gYCh1oyfHGYu6hZViwo7AJKtQpwGtsWfFoBr59r22uYxcAuH4mxsneNgCoTFkGysXSg2w0qyUkEbDRINzV1OiM+ZR6AF2kbSmJrsKPBR7u87X5y4nUi0topH6axURh6clqqUprmIFXCllGpTkNh3uXugPT6RqVvmcLUechMYdCGpqGeQbwUp2HCaCVrJsX7p8rUWX9Dh+CxCyG2RosMJVww27FmvUCy0JKQCZVq0uiPfvj1RxhzgO4KTeO9I8LRt6h/oT1u16i3mHBaHS8fgrU6jF9mYPoGG1771z+bQSE06KjskO8q2jR6l7cE12mI1ffpeY+qM9PTH+JtfK1yuTxeTsq2k6c90JTAuxHwOhWOKFPbKvAwQYLe4E/jozLI1Mw1mebV9G2dilDJTc29yWVoRW09au7kaG7sIFf6oQlL9mLBS3IpYev36wDfXdM9a+DvRfm1kN3zPvnc6da2Tekjs1i0gZQxCsZGRcpo4HbO/Vix/+XUN/0o00qRhOVaBUCdKXdAFAN05ZxjWp5rJX1LgaWo0QdvsJnnn6laDETh2gbsZVcckaKNXA2vg1v6K951C56lZ4IUYiRYr8VgVdNmrQKrixNeTeAf6aBUgzIEQngroqIjaA6GxOVWWYTJgRrFMcVGYRRgHYURJmbq2o86KNWgOsuiZdv8GrYu00LRyUuCpUtObeuK5DwMEkzErbozg00MQGP0rPFG3lHqckO33w3VbBEoyRs5R6MgYrB2BZA1I78HXfoKFBapOl4HrVrr6YAN6ubhA+A1kWSjd1DON2duoX6RNqJNzA565WleuqjV8TpoqVgMy6JEX/5KDo6DJLG2wFxnm438JIxFrI3aRTHK0NXzaZi+RPJzWibFFmoPRRinbQhnBpm/hox08qRA95B9iq0o0syyjtlBLwrjFJ3iqYtaHa+LVhz+HcZGbRar43XQ+iUDmTZTVWAdhBLgRw/aAskOrYsSPl/Gt2BTrK34mpgd9Fbo1Rut7BqQnbbDi2/0Ng8t0K6+sJVI71GweJVYXXTQiJ+2ctyhifVyypjXPbR3A/wbK6AtN6wp/ACsyDyS3RVqKlwSNgpOxg5WfNvMKt/j/R5S6pvtWLk/PZ8vf+4bN0f0tJmgRt8o+BklAWkTQu8uL/tsc3F3Y17eHL3lMQ4OhKprRWUhSN4o2RkEvLRxeFavUrET1HEMFhmik6SYUBOLSUrFDpgmGdpeF0q2pJhFBcKkQbZvium0wJi0UPOm3GEqEDaNvFFTzaNC2RHpG5ltzqcNGD3cjZWq0i8fRSzGDwk4sRyBY5S5xFQx0NzQpxzYbUJ2pGLVq76KxZR9/HzaykmhQduu02Oe3ATY+UWRh/j8mKPFkn14THXMXMd4rwNaO8RaJ9Z47Yyp9c758rkvcfDtrH9tp92cnGa99+BGzC0QnHsl2kPbH28+odGfdu7b/YkTpmyM/KOag8aJi0f3QXn2Mj5teHhcwE5hLW3r5PjY2aytgzM0qVCVvZEXsVGKQEVlwLLAM1cGsiNeclLpblQqGUymtH0YVF3dyM9MK3LHxHV1+hHs2DoxV+by/UykALk1McnJTdIkw7JAc1QlxlezzkOFJhsuHZBfR4kZo+1FWWBPrgWFD7ceDgARXnSE73SegyYtRnRdOqsN1xo2hkVAHIdjxqzGWwItBiOYcJXm2kqAOXayQw55kgoXe8dKrZmwJ6lw1yTbjsYfpCTPeUg6g+LaHNRo8OHWg8g7ZqFJixGXLvCLHGJyHQgmvNxnUiEIJrzcRx/dJo07+yS3rno8I98n2PDlifXkcmoVmmT4NMjvgphH5W2SEdDA/xLNhH7BRDgf7PqJ45BbxrvcSWV1CvKomdpxhiQPj6uxEegorLPpgsmOP8FlfNege3iHaoOpOkm7E7oILnxVmbw1J1yj2zShDNuz4jFTG7I06uWntNIT14fKc5cA6m5GsRvGLjrfu7pjZSpr57faFP7DJjeoUlE6Q1nCeT2Pcp0ZjBiKchbj9Cqxick46KY91h+7aKMJ1/B6vrcHf8BXsS5vVtcr3oH2N12CKe/TJ6U6ij0HQPf+TNN7KUxt1O1oYBMZObVq5qjFlHtsvfjyrWclD1+DihVRUQ2vDy6/Bv0KmqLarS6uvwbtCprC2n38OrT7OEi7T6uLu/uvQb+KqJpZLv7cYpaBmTMGE4q8m5Fnv+t0X4L2jGJpZ7wkl0rPJ0R2hkGS9Hz8g989Pr25uZgL65ILD+05xeGeWNu2t/7+JNve7O5j295z4V2SEeo0tUcGqIdlM17uPKyVJrxj2KE90lMdfprfqjvVUovS2knfAdUNmswBrb6FMtzDs5wmmy4gtEzWONW6SbMjLWMq+nXoOUxN9+vQk0lzUBUQGvamHwnOelso/NCP5p0+/rSP5qay5K9L+CDc3Sn7aDgbBM4UaxX7VWXwnCLWsuhMXz0p5xzTeYr5SH7K82yCEOsYao3hx/ZCvM81sLYd47ijolA+nUQAzaBiEnzIma8W1SnqJo3K9B5LWo2YxW5R1dB0Mg+9ZH0h5rjEwY3ltOhLEqfzaETZJ2VS+U7gxRIP41RgtvZRj6wDOvm8U8YUeBz6QrN1QguqkXDbe5yygd/pV60hqbPiXgSDP4qnWBnbp0kstjwWfQO2kTtmd7UiVSpa/GsdLftx3IWmClSpkRJzrylWnPZ5l9jaU1yKmyyZYtljn3OVtISU2bhjjp9VpEpBSkiRbeT41vxUqWgJKROFT6jTYn2ZoZ+R3MTUepqhsxWkhBT5JYnc+WlSshJSJZ5b61IjJaQIPunEvFstn+H/5qdSi94A5aYeZulUTWwLQfXtyMPpVanEPmS/Q5lslk1QNqQFQh+VBxTOU6U6OzHVvChJUAdphnrVqSlcFw7N5kYPILY8s2vp67g14pYz5ahOW8VqfXhBjMtprOzZjMEGxCCwgfkl9NLp1rr3qNZJlUvZfMQxixwrnWLnRI9+TXb825fjmTpiQYx/o5I1U0UKYtyK5AMhs1SlosatTBhZfjRPZSpqIpvLpx2N79CGY+S9qc7oo9MUqkM7cK1HHZzKzVKZkpmQKlUKN1uV6gz5VUMrmGaqU0lN88kzKOWaLtumGKTMugtiI3PB2anWSVU8F5ydfk12Qrng7LSpERPKBWepSEFMMBecpSri83UI14qtdJJjtni8jODHr9aUM3dd6ojN3k09c9flasKzd1NPeHUoIz7ptZ12QqVLF9FJFfdgpoG5ICagyJTrWjoVEVvakveCZ6lKRY1/Rcikc6gdqojOo/4CZlrjC2L8isw2dglPCKMP8ku+5qvQjh//rM+kc9wd+gjPc8+3zY+F2/xkrml/Ipj0z7b+i1b/ZL6aCKuSjxXPU5mKm6A65gOwHDDqNi3latU5ig7Tz1It+pVinepMvA6kQxnhtSAzWQfSo9KgtSD5WPg8dSqpiZ2A6B+Zo24eVqRRm5/CpS1Z4G5c4KDLKySvaanUmHZhS01BcpedyLKW6qP131MzBT4sOSvNYmAmIEjCKSfkmOqxmYppPO0UKlM9kfnT3UdYqjnxagq2TiQ9Md0yLyqWYc5QM4KcoF4Tzw6zdZpgbpgIXtM1XHWbEC2WyPRwX6SaoXpspuIxdYbqiSS71KA1R51Iery6zVargfo0w/CsdKKQG9JGzFGn7o6J1Axe+SL1Sqsa0kxSKcYSri7GU7TaTRrTe2xfF5TCWKxqfiV6DlduuouNhujYe/mRlJD0YMXOkwUTJKFAtM7SlHnlipQzgHKECeNV0zBGzqjRc69YTnfuT8FhOqdmWYrMxyuWys/6ibdr0wOOSu8sIObkngUl0j9rPKdz0JLEjDy0NBbhojWe0x3qk99a5oEvwFOwcXEdTumzNd2qZfsFI/6lW5GfzUyFkhL/QifPm5kKBSP+1RrTHmtG0UB4+xTwo+mnBGiaNJgJzTTjxHJ2dbzBjH8as9ozPi99CF6atxuheDnhyXg1a5QzugUj/u0dyeQDWzQ16rTEWqN56VFSEmqN5qVCwYhfg9kVgnAZzOFULKoiw47EiuLQBglswaafIaJqRaHHn/uA7cTrImkq1VgJaJJCPHfSwQO6LjVeQjnpzPQQXApZz/zmpUmD2aCcdGYakcwG5KTz0ofjfCWKNk9PzpSTcTRFSkryxrwZP7Aek8n5kxsDD7YVlAy98SaI4yDkuWeVPWJDHz/DgjV3gUq1DQxODipWfMbdvcTu9hBmyNH0+mhDe+SaFQ0hpXlv6d24sY8HKLNoG1uMS28JszS+sCZoxisrNdk3H1hdbXm/VhN5Pp9W1GrAW+ywSgUgVREzoFjTDVIQB+h0f3Q9+1RmzHUkIwidHccddLmwSS5HYyhE0OHSwN19Y2ap67npyyxUYfASLBXThvTWsETNTQx/fQrjmXheH0N+PXG6NaOCo5ESLTVUG2FQQyHNfLACx9O+OLm32BgUtSQhZe0oLTxRQ1uYpryMpMFIRpnPQbF+iqItxby0UpZFurYf9WeOBZUI3XMxURVHRI0Gj97csP7+RAXa4k0tSe7iYsSexmv+Lyk9RRyxyjHfswYFm7bnQr1pbeJUNoa1BTHLqw0nUb61gC1h6UsEdO8q5FW04jZQt4mbqh7t+putgYtpyIBRz4omNESbCU+0K7LVENGBMBMrQGEjogTqNmP13WlrXAclfnXy8ctZqLGjwkHfnRH/Nhd++z+ESTGAsLFs3VOm9HJoU+JXxw1hZhjaj0D3WDxdFZIOvxr49CI79KZvVjso8auDDmSaV/BtMRJQJrXSbCZaVFT46c/Ho4Qc6cnduGYue2LyDSYjhqxxYFAxZJ1LnnxkDbMgh6vbzDQNOpnrxJk6fy0MUvhRgxDfQAxhxfn0NEnNOEgO0XbqBqRLyb6mpEe3SYNyh149PWeu6DM/rURrnUt+7oDNPMqKwUvJgCirCers1U3V8LSPl+EcFnVnxL/NhSdPmsOMWtwaphk1tY/7g76dcWVKiApXRuA+PZ8vT1HdMQM7wp3OqQxWKlg8Z1FTUq+th/Wury0xF0Wl/2B5SC10ohts+6eyLqFhtfGkzY2viYs8K92E8Yy0aZASU8MsBc9SH4KdSAqyzualEMGKO+eowsCcdGkR41CnWeHCGVUfOjcRZ5vi/Dked+s8ek56F7u4OEb/oSAMU9Qus+k++qO1qc5KrWk7ZHRFSF68ykw6PcFQpHOagqKEfzQvBXI+nOTDmblRKOI+0SNMTLf+ZJMpdBXqrDgVyZK51YKSEacCiAFqoqrzNxKQZrrvq+lRic2RV0nPCoqAPc2liX0KUvmJKOeAjRvMrWVpMhuQoM5GHwoxQXWm2FHPqVDPrvrWcZ6TTpfRVOmcN5MxSunlyTx7GGjozFpN7nSruWskqt4YQUvbCu4KdQbTMoRZyirDIMgZC3ZfR9aUi0n6dNuxE1VsphopjQy5zfD8PWrErcAxQbCFrZ7kSMHEKZOGCQMIk1tj1qGbvdC0GUXUV2oBrSGWzWLCqss2HjklyaDN6Tcdzjdr3bt5j600M2iLRhR/T1slO8CDL2htfLHRSV18J2BmEtUITrSg1iI9RUwjSczDp0nLUVy6RVqGK1MfUx62HrUfkAVTLtklSqd1KMemeQUWR8XgnHWnLeJUWElKfQ2Ekzt+3lXaITfLi3lyCWX16dpKXNu0Y+CgI5UsT+UUI0WVLhYttWj8tW4nZyvAt2eckRNMrUInD6OvBnOFTnrZ1cpbXawkNa6vd27gD/W3SahzLUDl9je9KnTy4CsFDeMzHcbvGnyh8tW2IYlNun8DEpW56jljNmHmrDC1AZ6AYZubjPwG8ka5XVd6E4AU1RYTdkSsbasjoC7TQdva9WQKhRGMhqZk+kOhMywTcueiGZ1Jn/+jT/IECroq+m06/gwu/BrYIE5h1bKtFJhJGsYqB9W4VaGS4tBpUu5c+Sf2tnzqV/36ai7Xb5FRk38GmvbesHSunfkilE2gD5xgYsYFAR6ubqQ8g+AgXGfBw3oGlIX4asnUOEiL5W2B0mHffrpcPaZmezwVYSqTIfF9YgVaZDh1mDpUU3hwMZ+2VrpdsYSnt9JqXNEGX+oeb9FGGBJz1hoMsyOMbVLBdpYefMvNDyGdhGENm4fmCXz3ZDKiFXp3fQAesHXE+wbJHW43PdXHq7DoMc9RIem96IghTW4v/WEuU3olLINYRrvgdVA0o5ydxzU20kxlakeXaehA4XPTqmGQBraa/lIdRH157w6GayH3JZU6j+/roTum3e0bJczzqK5Bwva4H2EqH2oa2mb6EAMLVi5rA5T2/XO+uKvPQjbYZKFd1Q9P1CiSeIZQSGnXpqYqluO46MTa/GxztccuFUoVzklF7ra77SduoqHzQBJtofaQ1NA9aBBkdwSa5FwAwNn+gfJoRBJsofaQVD9O0+DHHJJh1XxdzBheJxyi16EVO50RGlMeMnvT2ISDkRRGRiy/WmxUXcxbgCpIOHby1RU6odTursoCtDPNqN4s1kFmserrVdhk2xT6MiT3wNZv3CZuH8noyZ+EJIHbRzJxw0lIEri9JF+SOJ2mxJvQfVR/ARNU+yZuH8k4OTo7noRmA7mPaBhZfjQJ0QaygjUSHiywbLMBMXUNhFhPqC1MZRe+BVZNf7Y5SO54tCAU9ozbapYD0m0Onelf8wP1nXpe6vT8dZAvd2zcEvdlbZuS2mCVL3fvMJLiy9q2D1HULB2iey/QIFfIF+NLcYS6KMVuUIeqnKCJL90FCAC1DkAoWBZ/E3904f+SgQxIatIIWYqLn8Cqyr/FQLoDkAhqPYDUsXSBFoOexox4X0tbxsFbYksWh1nqBttyEGWkDzekKfbiBlrlxxQW0j25gaHFM5r6lr7B5NLj2007zYK9FK9u7ScTd2XFu8RKCGJHT++sSrERQ0/1am84Yq/ypNKMwicYq4p1xdrJttClxwBtO1sqBRtbvHmnNFxNCw6pNHmjkeJdIVRyvJbTEyHbtuOdUKO6vG6yLXQeyvnGaH33idGpM1mItETNP8l4EoMkzGIb1OePmmsEdtsWkkbrVTOd9ZRUdyfuPlhEwF/YsfTFHhVto87O6CdhcPCPYvcL2qPxCF7wp+jf2vkzSHTyh8jxxgWeY9oW/kgfaxp0J9cwtVplpI8uA53N+NcM1sG15aWuj2qjXvsywZl8bQtJ0MiRBGTzws6tm1sLtIdfWed00qthMtmhhWIg1my9NmgPP73Wa2Ey2aEmFR8sq49cE5JtOQxYb7t0mpAJzslXc4mzsJls/ReYST266TTtTQd6L2O9lqWg9nmAs0US9LaHLGgmV2BFGunV0Dra57ye6WqcKzSD1U1opf0Pqd88HKmmgBdu5W9q2dFH4EaFwTTjA/C88CmMPelLExpUSCAmH9jL/OImbhi4gfTT+BqMmlD8BRumD61ZoZoObuCA5wXCUKcBpmCQSEwFiD/JP4gUPYq6B/MgXxfy+7eDfcQb/mvjBpYH/21s3NhHZ7Ib6RPkFNqP5vbJKOQZbaTU6d+VLwi2E0nHK5ZZS4bcSaWjrrM0DQPpsDWxdFwPONJBS5kURFTSna4+wHMeqEirq3fvru7Mu/t78zIMNlJRKbLp1pWt7k4kHY/ncFJxyObRoeTKWmA5Plj4jkTMmkwK4sW7qw/3K7mINZkURN+CjaPMSlIKpJXi7rVF4kVrmUXZEl3gEwuSSyJvwMbKvBTiQ+HAI57ghYKXoR/BL9Z4gBr+vI6dg5P9Y+v1/gL9v4v9A/hmZMVp80XfzhZW7C+eNj5s2Z6258tTf7lc+tt0bcFPEuex+YUd+kUbuIC/LmAwteE/XT+C+qP5Tvjw9cH+wcniZLFcmMv9g/3Do4Ojw+Xe4fJ0f7k8Ojo8r1rh78Cz7WUOcD5a6cMPu4YydzrDchwzDSPXNpEdFlGw/c4gvuCTEiFq2J5oeDFIE3SFokRp6E6JgdJgaQdog+24z80kWyd27K4H28gBHkjxwcRInouaqYGS8A4+8Bx5YYwW+yXboYLwRTHlhZecQqrQQX/XD6Gerx2AbBUhLX/4zmg/y/Mtoh7CZ9+h1PPv0Djwv1/98/8DEFXwTA===END_SIMPLICITY_STUDIO_METADATA
# END OF METADATA