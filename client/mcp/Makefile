.PHONY: build clean run

APP_NAME=genesis-probe
BUILD_DIR=bin

build:
	@echo "Building $(APP_NAME)..."
	@mkdir -p $(BUILD_DIR)
	go build -o $(BUILD_DIR)/$(APP_NAME) ./cmd/genesis-probe

clean:
	@echo "Cleaning..."
	@rm -rf $(BUILD_DIR)

run: build
	@./$(BUILD_DIR)/$(APP_NAME) run --mcp
