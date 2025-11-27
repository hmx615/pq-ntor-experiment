# Makefile for PQ-Ntor C Implementation

# 编译器设置
CC = gcc
CFLAGS = -Wall -Wextra -O2 -g -std=c99
LDFLAGS =

# liboqs 路径
LIBOQS_DIR = $(HOME)/_oqs
LIBOQS_INCLUDE = $(LIBOQS_DIR)/include
LIBOQS_LIB = $(LIBOQS_DIR)/lib

# 包含路径和库路径
INCLUDES = -I$(LIBOQS_INCLUDE) -Isrc
LIBS = -L$(LIBOQS_LIB) -loqs -lssl -lcrypto -Wl,-rpath,$(LIBOQS_LIB)

# 可选：编译 Kyber768 版本（默认 Kyber512）
# 取消注释下面这行来使用 Kyber768
# CFLAGS += -DUSE_KYBER768

# 源文件
SRC_DIR = src
TEST_DIR = tests
BENCHMARK_DIR = benchmark
PROGRAMS_DIR = programs

# 目标文件
SRCS = $(SRC_DIR)/kyber_kem.c $(SRC_DIR)/crypto_utils.c $(SRC_DIR)/pq_ntor.c $(SRC_DIR)/classic_ntor.c $(SRC_DIR)/cell.c $(SRC_DIR)/onion_crypto.c
OBJS = $(SRCS:.c=.o)

# 服务器程序
SERVER_SRCS = $(SRC_DIR)/directory_server.c $(SRC_DIR)/test_server.c
SERVER_OBJS = $(SERVER_SRCS:.c=.o)

# 测试程序
TEST_KYBER = test_kyber
TEST_KYBER_SRC = $(TEST_DIR)/test_kyber.c
TEST_CRYPTO = test_crypto
TEST_CRYPTO_SRC = $(TEST_DIR)/test_crypto.c
TEST_PQ_NTOR = test_pq_ntor
TEST_PQ_NTOR_SRC = $(TEST_DIR)/test_pq_ntor.c
TEST_CLASSIC_NTOR = test_classic_ntor
TEST_CLASSIC_NTOR_SRC = $(TEST_DIR)/test_classic_ntor.c
TEST_CELL = test_cell
TEST_CELL_SRC = $(TEST_DIR)/test_cell.c
TEST_ONION = test_onion
TEST_ONION_SRC = $(TEST_DIR)/test_onion.c

# 基准测试程序
BENCHMARK = benchmark_pq_ntor
BENCHMARK_SRC = $(BENCHMARK_DIR)/benchmark_pq_ntor.c

# 目录服务器程序
DIRECTORY = directory
DIRECTORY_SRC = $(PROGRAMS_DIR)/directory_main.c

# 中继节点程序
RELAY = relay
RELAY_SRC = $(PROGRAMS_DIR)/relay_main.c
RELAY_OBJS = $(SRC_DIR)/relay_node.o

# 客户端程序
CLIENT = client
CLIENT_SRC = $(PROGRAMS_DIR)/client_main.c
CLIENT_OBJS = $(SRC_DIR)/tor_client.o

# 主要目标
.PHONY: all clean test test-crypto test-pq-ntor test-classic-ntor test-cell test-onion test-all benchmark visualize directory relay client

all: $(TEST_KYBER) $(TEST_CRYPTO) $(TEST_PQ_NTOR) $(TEST_CLASSIC_NTOR) $(TEST_CELL) $(TEST_ONION) $(BENCHMARK) $(DIRECTORY) $(RELAY) $(CLIENT)

# 编译 Kyber 测试程序
$(TEST_KYBER): $(TEST_KYBER_SRC) $(SRC_DIR)/kyber_kem.o
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译加密工具测试程序
$(TEST_CRYPTO): $(TEST_CRYPTO_SRC) $(SRC_DIR)/crypto_utils.o
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译 PQ-Ntor 测试程序
$(TEST_PQ_NTOR): $(TEST_PQ_NTOR_SRC) $(OBJS)
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译 Classic NTOR 测试程序
$(TEST_CLASSIC_NTOR): $(TEST_CLASSIC_NTOR_SRC) $(SRC_DIR)/classic_ntor.o $(SRC_DIR)/crypto_utils.o
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译 Cell 测试程序
$(TEST_CELL): $(TEST_CELL_SRC) $(SRC_DIR)/cell.o
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译 Onion 测试程序
$(TEST_ONION): $(TEST_ONION_SRC) $(SRC_DIR)/cell.o $(SRC_DIR)/onion_crypto.o $(SRC_DIR)/crypto_utils.o
	@echo "Building $@..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译目标文件
%.o: %.c
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) $(INCLUDES) -c $< -o $@

# 运行 Kyber 测试
test: $(TEST_KYBER)
	@echo ""
	@echo "Running Kyber KEM test..."
	@echo "=============================="
	./$(TEST_KYBER)

# 运行加密工具测试
test-crypto: $(TEST_CRYPTO)
	@echo ""
	@echo "Running Crypto Utils test..."
	@echo "=============================="
	./$(TEST_CRYPTO)

# 运行 PQ-Ntor 测试
test-pq-ntor: $(TEST_PQ_NTOR)
	@echo ""
	@echo "Running PQ-Ntor test..."
	@echo "=============================="
	./$(TEST_PQ_NTOR)

# 运行 Classic NTOR 测试
test-classic-ntor: $(TEST_CLASSIC_NTOR)
	@echo ""
	@echo "Running Classic NTOR test..."
	@echo "=============================="
	./$(TEST_CLASSIC_NTOR)

# 运行 Cell 测试
test-cell: $(TEST_CELL)
	@echo ""
	@echo "Running Cell test..."
	@echo "=============================="
	./$(TEST_CELL)

# 运行 Onion 测试
test-onion: $(TEST_ONION)
	@echo ""
	@echo "Running Onion Encryption test..."
	@echo "=============================="
	./$(TEST_ONION)

# 运行所有测试
test-all: $(TEST_KYBER) $(TEST_CRYPTO) $(TEST_PQ_NTOR) $(TEST_CLASSIC_NTOR) $(TEST_CELL) $(TEST_ONION)
	@echo ""
	@echo "Running all tests..."
	@echo "=============================="
	./$(TEST_KYBER)
	@echo ""
	./$(TEST_CRYPTO)
	@echo ""
	./$(TEST_PQ_NTOR)
	@echo ""
	./$(TEST_CLASSIC_NTOR)
	@echo ""
	./$(TEST_CELL)
	@echo ""
	./$(TEST_ONION)

# 编译基准测试程序
$(BENCHMARK): $(BENCHMARK_SRC) $(OBJS)
	@echo "Building benchmark..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS) -lm
	@echo "✓ Built: $@"

# 编译目录服务器程序
$(DIRECTORY): $(DIRECTORY_SRC) $(SERVER_OBJS)
	@echo "Building directory server..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS) -lpthread
	@echo "✓ Built: $@"

# 编译中继节点程序
$(RELAY): $(RELAY_SRC) $(RELAY_OBJS) $(OBJS)
	@echo "Building relay node..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 编译客户端程序
$(CLIENT): $(CLIENT_SRC) $(CLIENT_OBJS) $(OBJS)
	@echo "Building client..."
	$(CC) $(CFLAGS) $(INCLUDES) -o $@ $^ $(LIBS)
	@echo "✓ Built: $@"

# 运行基准测试
benchmark: $(BENCHMARK)
	@echo ""
	@echo "Running performance benchmark..."
	@echo "=============================="
	./$(BENCHMARK)

# 可视化基准测试结果
visualize: benchmark
	@echo ""
	@echo "Generating visualizations..."
	@echo "=============================="
	@if command -v python3 > /dev/null; then \
		cd $(BENCHMARK_DIR) && python3 visualize.py; \
	else \
		echo "Error: python3 not found. Please install Python 3 to generate visualizations."; \
		exit 1; \
	fi

# 显示 liboqs 信息
info:
	@echo "=== Build Configuration ==="
	@echo "CC:              $(CC)"
	@echo "CFLAGS:          $(CFLAGS)"
	@echo "liboqs dir:      $(LIBOQS_DIR)"
	@echo "liboqs include:  $(LIBOQS_INCLUDE)"
	@echo "liboqs lib:      $(LIBOQS_LIB)"
	@echo "=========================="
	@echo ""
	@echo "Checking liboqs installation:"
	@ls -lh $(LIBOQS_LIB)/liboqs.so* 2>/dev/null || echo "  ⚠️  liboqs not found!"
	@echo ""

# 清理
clean:
	@echo "Cleaning..."
	rm -f $(OBJS) $(SERVER_OBJS) $(RELAY_OBJS) $(CLIENT_OBJS)
	rm -f $(TEST_KYBER) $(TEST_CRYPTO) $(TEST_PQ_NTOR) $(TEST_CLASSIC_NTOR) $(TEST_CELL) $(TEST_ONION) $(BENCHMARK) $(DIRECTORY) $(RELAY) $(CLIENT)
	rm -f $(BENCHMARK_DIR)/*.csv $(BENCHMARK_DIR)/*.png $(BENCHMARK_DIR)/*.tex
	@echo "✓ Clean complete"

# 帮助信息
help:
	@echo "PQ-Ntor C Implementation - Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  make              - Build all programs (default)"
	@echo "  make test         - Build and run Kyber KEM test"
	@echo "  make test-crypto  - Build and run Crypto Utils test"
	@echo "  make test-pq-ntor - Build and run PQ-Ntor test"
	@echo "  make test-cell    - Build and run Cell format test"
	@echo "  make test-onion   - Build and run Onion encryption test"
	@echo "  make test-all     - Build and run all tests"
	@echo "  make benchmark    - Build and run performance benchmark"
	@echo "  make visualize    - Run benchmark and generate visualizations"
	@echo "  make directory    - Build directory server"
	@echo "  make relay        - Build relay node"
	@echo "  make client       - Build Tor client"
	@echo "  make info         - Show build configuration"
	@echo "  make clean        - Remove compiled files"
	@echo "  make help         - Show this help message"
	@echo ""
	@echo "To use Kyber768 instead of Kyber512:"
	@echo "  make CFLAGS='$(CFLAGS) -DUSE_KYBER768'"
	@echo ""
