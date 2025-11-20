# Makefile for Kyber test program on Phytium Pi
#
# Usage:
#   make              - Build test_kyber_simple
#   make clean        - Remove built files
#   make test         - Build and run test

CC = gcc
CFLAGS = -Wall -O2 -I$(HOME)/oqs/include
LDFLAGS = -L$(HOME)/oqs/lib -loqs -Wl,-rpath,$(HOME)/oqs/lib

TARGET = test_kyber_simple

all: $(TARGET)

$(TARGET): test_kyber_simple.c
	@echo "Building $(TARGET)..."
	$(CC) $(CFLAGS) -o $(TARGET) test_kyber_simple.c $(LDFLAGS)
	@echo "✅ Build successful!"
	@echo ""
	@echo "Run: ./$(TARGET)"

test: $(TARGET)
	@echo "Running test..."
	@./$(TARGET)

clean:
	rm -f $(TARGET)
	@echo "Cleaned."

.PHONY: all test clean
