DOCKER_IMAGE ?= aabadie/dotbot:latest
DOCKER_TARGETS ?= all
PACKAGES_DIR_OPT ?=
SEGGER_DIR ?= /opt/segger
BUILD_CONFIG ?= Debug

.PHONY: all node gateway gateway-app gateway-net clean-gateway clean-gateway-app clean-gateway-net clean-node clean distclean docker

all: node gateway

node:
	@echo "\e[1mBuilding $@ application\e[0m"
	"$(SEGGER_DIR)/bin/emBuild" mari-node-nrf52840dk.emProject -project 03app_$@ -config $(BUILD_CONFIG) $(PACKAGES_DIR_OPT) -rebuild -verbose
	@echo "\e[1mOutput binary: app/03app_node/Output/nrf52840dk/$(BUILD_CONFIG)/Exe/03app_node-nrf52840dk.bin\e[0m"
	@echo "\e[1mDone\e[0m\n"

gateway: gateway-app gateway-net

gateway-app:
	@echo "\e[1mBuilding $@ application\e[0m"
	"$(SEGGER_DIR)/bin/emBuild" mari-gateway-app-nrf5340dk.emProject -project 03app_gateway_app -config $(BUILD_CONFIG) $(PACKAGES_DIR_OPT) -rebuild -verbose
	@echo "\e[1mOutput binary: app/03app_gateway_app/Output/nrf5340-app/$(BUILD_CONFIG)/Exe/03app_gateway_app-nrf5340-app.bin\e[0m"
	@echo "\e[1mDone\e[0m\n"

gateway-net:
	@echo "\e[1mBuilding $@ application\e[0m"
	"$(SEGGER_DIR)/bin/emBuild" mari-gateway-net-nrf5340dk.emProject -project 03app_gateway_net -config $(BUILD_CONFIG) $(PACKAGES_DIR_OPT) -rebuild -verbose
	@echo "\e[1mOutput binary: app/03app_gateway_net/Output/nrf5340-net/$(BUILD_CONFIG)/Exe/03app_gateway_net-nrf5340-net.bin\e[0m"
	@echo "\e[1mDone\e[0m\n"

clean-node:
	"$(SEGGER_DIR)/bin/emBuild" mari-node-nrf52840dk.emProject -config $(BUILD_CONFIG) -clean

clean-gateway: clean-gateway-app clean-gateway-net

clean-gateway-app:
	"$(SEGGER_DIR)/bin/emBuild" mari-gateway-app-nrf5340dk.emProject -config $(BUILD_CONFIG) -clean

clean-gateway-net:
	"$(SEGGER_DIR)/bin/emBuild" mari-gateway-net-nrf5340dk.emProject -config $(BUILD_CONFIG) -clean

clean: clean-node clean-gateway

distclean: clean

docker:
	docker run --rm -i \
		-e BUILD_CONFIG="$(BUILD_CONFIG)" \
		-e PACKAGES_DIR_OPT="-packagesdir $(SEGGER_DIR)/packages" \
		-e SEGGER_DIR="$(SEGGER_DIR)" \
		-v $(PWD):/dotbot $(DOCKER_IMAGE) \
		make $(DOCKER_TARGETS)
