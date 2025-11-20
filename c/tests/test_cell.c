/**
 * test_cell.c - Test Cell Format Implementation
 */

#include "../src/cell.h"
#include <stdio.h>
#include <string.h>
#include <assert.h>

void test_cell_creation() {
    printf("Testing cell creation...\n");

    cell_t *cell = cell_new(12345, CELL_CREATE2);
    assert(cell != NULL);
    assert(cell->circ_id == 12345);
    assert(cell->command == CELL_CREATE2);

    cell_free(cell);
    printf("  ✓ Cell creation\n");
}

void test_cell_serialization() {
    printf("Testing cell serialization...\n");

    // Create a cell
    cell_t *cell = cell_new(0xABCD, CELL_RELAY);
    assert(cell != NULL);

    // Fill payload with test data
    for (int i = 0; i < CELL_PAYLOAD_LEN; i++) {
        cell->payload[i] = i & 0xFF;
    }

    // Serialize
    uint8_t buffer[CELL_LEN];
    int len = cell_serialize(cell, buffer, sizeof(buffer));
    assert(len == CELL_LEN);

    // Check serialized format
    assert(buffer[0] == 0x00);  // CircID MSB
    assert(buffer[1] == 0x00);
    assert(buffer[2] == 0xAB);
    assert(buffer[3] == 0xCD);  // CircID LSB
    assert(buffer[4] == CELL_RELAY);  // Command

    // Deserialize
    cell_t *cell2 = cell_deserialize(buffer, len);
    assert(cell2 != NULL);
    assert(cell2->circ_id == 0xABCD);
    assert(cell2->command == CELL_RELAY);
    assert(memcmp(cell2->payload, cell->payload, CELL_PAYLOAD_LEN) == 0);

    cell_free(cell);
    cell_free(cell2);
    printf("  ✓ Cell serialization/deserialization\n");
}

void test_create2_cell() {
    printf("Testing CREATE2 cell...\n");

    uint8_t handshake_data[100];
    for (int i = 0; i < 100; i++) {
        handshake_data[i] = i;
    }

    cell_t *cell = cell_create_create2(1, 0x0002, handshake_data, 100);
    assert(cell != NULL);
    assert(cell->circ_id == 1);
    assert(cell->command == CELL_CREATE2);

    // Parse it back
    uint16_t htype, hlen;
    uint8_t hdata[512];
    int ret = cell_parse_create2(cell, &htype, hdata, &hlen);
    assert(ret == 0);
    assert(htype == 0x0002);
    assert(hlen == 100);
    assert(memcmp(hdata, handshake_data, 100) == 0);

    cell_free(cell);
    printf("  ✓ CREATE2 cell creation and parsing\n");
}

void test_created2_cell() {
    printf("Testing CREATED2 cell...\n");

    uint8_t handshake_data[150];
    for (int i = 0; i < 150; i++) {
        handshake_data[i] = 255 - i;
    }

    cell_t *cell = cell_create_created2(2, handshake_data, 150);
    assert(cell != NULL);
    assert(cell->circ_id == 2);
    assert(cell->command == CELL_CREATED2);

    // Parse it back
    uint16_t hlen;
    uint8_t hdata[512];
    int ret = cell_parse_created2(cell, hdata, &hlen);
    assert(ret == 0);
    assert(hlen == 150);
    assert(memcmp(hdata, handshake_data, 150) == 0);

    cell_free(cell);
    printf("  ✓ CREATED2 cell creation and parsing\n");
}

void test_relay_cell() {
    printf("Testing RELAY cell...\n");

    uint8_t test_data[] = "Hello, Tor!";
    cell_t *cell = cell_create_relay(100, RELAY_DATA, 42, test_data, sizeof(test_data));
    assert(cell != NULL);
    assert(cell->circ_id == 100);
    assert(cell->command == CELL_RELAY);

    // Parse it back
    relay_cell_t relay;
    int ret = cell_parse_relay(cell, &relay);
    assert(ret == 0);
    assert(relay.relay_command == RELAY_DATA);
    assert(relay.stream_id == 42);
    assert(relay.length == sizeof(test_data));
    assert(memcmp(relay.data, test_data, sizeof(test_data)) == 0);

    cell_free(cell);
    printf("  ✓ RELAY cell creation and parsing\n");
}

void test_destroy_cell() {
    printf("Testing DESTROY cell...\n");

    cell_t *cell = cell_create_destroy(999, DESTROY_REQUESTED);
    assert(cell != NULL);
    assert(cell->circ_id == 999);
    assert(cell->command == CELL_DESTROY);
    assert(cell->payload[0] == DESTROY_REQUESTED);

    cell_free(cell);
    printf("  ✓ DESTROY cell creation\n");
}

void test_var_cell() {
    printf("Testing variable-length cell...\n");

    var_cell_t *cell = var_cell_new(5, CELL_VERSIONS, 10);
    assert(cell != NULL);
    assert(cell->circ_id == 5);
    assert(cell->command == CELL_VERSIONS);
    assert(cell->payload_len == 10);
    assert(cell->payload != NULL);

    // Fill with test data
    for (int i = 0; i < 10; i++) {
        cell->payload[i] = i * 10;
    }

    // Serialize
    uint8_t buffer[100];
    int len = var_cell_serialize(cell, buffer, sizeof(buffer));
    assert(len == VAR_CELL_HEADER_LEN + 10);

    // Deserialize
    var_cell_t *cell2 = var_cell_deserialize(buffer, len);
    assert(cell2 != NULL);
    assert(cell2->circ_id == 5);
    assert(cell2->command == CELL_VERSIONS);
    assert(cell2->payload_len == 10);
    assert(memcmp(cell2->payload, cell->payload, 10) == 0);

    var_cell_free(cell);
    var_cell_free(cell2);
    printf("  ✓ Variable-length cell\n");
}

void test_command_strings() {
    printf("Testing command name functions...\n");

    assert(strcmp(cell_command_to_string(CELL_CREATE2), "CREATE2") == 0);
    assert(strcmp(cell_command_to_string(CELL_RELAY), "RELAY") == 0);
    assert(strcmp(relay_command_to_string(RELAY_EXTEND2), "EXTEND2") == 0);
    assert(strcmp(relay_command_to_string(RELAY_DATA), "DATA") == 0);

    printf("  ✓ Command name functions\n");
}

void test_relay_pack_unpack() {
    printf("Testing RELAY pack/unpack...\n");

    relay_cell_t relay1;
    memset(&relay1, 0, sizeof(relay1));
    relay1.relay_command = RELAY_BEGIN;
    relay1.stream_id = 123;
    relay1.length = 20;
    memcpy(relay1.data, "www.example.com:443", 20);

    cell_t *cell = cell_new(50, CELL_RELAY);
    assert(cell != NULL);

    int ret = cell_pack_relay(cell, &relay1);
    assert(ret == 0);

    relay_cell_t relay2;
    ret = cell_parse_relay(cell, &relay2);
    assert(ret == 0);
    assert(relay2.relay_command == relay1.relay_command);
    assert(relay2.stream_id == relay1.stream_id);
    assert(relay2.length == relay1.length);
    assert(memcmp(relay2.data, relay1.data, relay1.length) == 0);

    cell_free(cell);
    printf("  ✓ RELAY pack/unpack\n");
}

int main() {
    printf("\n=== Cell Format Tests ===\n\n");

    test_cell_creation();
    test_cell_serialization();
    test_create2_cell();
    test_created2_cell();
    test_relay_cell();
    test_destroy_cell();
    test_var_cell();
    test_command_strings();
    test_relay_pack_unpack();

    printf("\n=== All Cell Tests Passed! ===\n\n");
    return 0;
}
