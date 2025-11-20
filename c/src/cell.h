/**
 * cell.h - Tor Cell Format Implementation
 *
 * Implements Tor's basic communication unit (Cell).
 * Based on Tor Protocol Specification (tor-spec.txt)
 */

#ifndef CELL_H
#define CELL_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

/* Cell size constants (Extended for PQ-Ntor)
 * NOTE: Standard Tor uses 512 bytes, but PQ-Ntor requires:
 *   - CREATE2: ~820 bytes (onionskin)
 *   - EXTEND2: ~1082 bytes (hostname + port + handshake info + onionskin)
 * In production, this would use variable-length cells or multi-cell handshakes.
 * For this prototype, we use 2048-byte cells to accommodate all PQ operations.
 */
#define CELL_LEN 2048             // Extended for PQ crypto (was 512)
#define CELL_HEADER_LEN 5         // CircID (4) + Command (1)
#define CELL_PAYLOAD_LEN 2043     // CELL_LEN - CELL_HEADER_LEN

/* Variable-length cell */
#define VAR_CELL_HEADER_LEN 7     // CircID (4) + Command (1) + Length (2)
#define VAR_CELL_MAX_PAYLOAD 65535

/* Circuit ID */
typedef uint32_t circuit_id_t;

/* Cell command types */
typedef enum {
    CELL_PADDING       = 0,
    CELL_CREATE        = 1,   // Deprecated (RSA)
    CELL_CREATED       = 2,   // Deprecated (RSA)
    CELL_RELAY         = 3,
    CELL_DESTROY       = 4,
    CELL_CREATE_FAST   = 5,
    CELL_CREATED_FAST  = 6,
    CELL_VERSIONS      = 7,   // Variable-length
    CELL_NETINFO       = 8,
    CELL_RELAY_EARLY   = 9,
    CELL_CREATE2       = 10,  // Used for PQ-Ntor
    CELL_CREATED2      = 11,
    CELL_PADDING_NEGOTIATE = 12,

    /* For internal use */
    CELL_UNKNOWN       = 255
} cell_command_t;

/* RELAY cell commands (inside RELAY/RELAY_EARLY payload) */
typedef enum {
    RELAY_BEGIN        = 1,
    RELAY_DATA         = 2,
    RELAY_END          = 3,
    RELAY_CONNECTED    = 4,
    RELAY_SENDME       = 5,
    RELAY_EXTEND       = 6,   // Deprecated (TAP)
    RELAY_EXTENDED     = 7,   // Deprecated (TAP)
    RELAY_TRUNCATE     = 8,
    RELAY_TRUNCATED    = 9,
    RELAY_DROP         = 10,
    RELAY_RESOLVE      = 11,
    RELAY_RESOLVED     = 12,
    RELAY_BEGIN_DIR    = 13,
    RELAY_EXTEND2      = 14,  // Used for extending circuit with PQ-Ntor
    RELAY_EXTENDED2    = 15,

    RELAY_UNKNOWN      = 255
} relay_command_t;

/* Destroy reason codes */
typedef enum {
    DESTROY_NONE               = 0,
    DESTROY_PROTOCOL           = 1,
    DESTROY_INTERNAL           = 2,
    DESTROY_REQUESTED          = 3,
    DESTROY_HIBERNATING        = 4,
    DESTROY_RESOURCELIMIT      = 5,
    DESTROY_CONNECTFAILED      = 6,
    DESTROY_OR_IDENTITY        = 7,
    DESTROY_CHANNEL_CLOSED     = 8,
    DESTROY_FINISHED           = 9,
    DESTROY_TIMEOUT            = 10,
    DESTROY_NOROUTE            = 11,
    DESTROY_NOSUCHSERVICE      = 12
} destroy_reason_t;

/* Fixed-length cell structure */
typedef struct {
    circuit_id_t circ_id;
    uint8_t command;
    uint8_t payload[CELL_PAYLOAD_LEN];
} cell_t;

/* Variable-length cell structure */
typedef struct {
    circuit_id_t circ_id;
    uint8_t command;
    uint16_t payload_len;
    uint8_t *payload;  // Dynamically allocated
} var_cell_t;

/* RELAY cell payload structure (inside CELL_RELAY/CELL_RELAY_EARLY) */
typedef struct {
    uint8_t relay_command;
    uint16_t recognized;      // Should be 0 for recognized cells
    uint16_t stream_id;
    uint32_t digest;          // Running digest (first 4 bytes)
    uint16_t length;          // Actual data length
    uint8_t data[CELL_PAYLOAD_LEN - 11];  // 507 - 11 = 496 bytes
} relay_cell_t;

/* CREATE2 cell payload */
typedef struct {
    uint16_t handshake_type;  // 0x0002 for ntor, 0xXXXX for PQ-ntor
    uint16_t handshake_len;
    uint8_t handshake_data[CELL_PAYLOAD_LEN - 4];
} create2_cell_t;

/* CREATED2 cell payload */
typedef struct {
    uint16_t handshake_len;
    uint8_t handshake_data[CELL_PAYLOAD_LEN - 2];
} created2_cell_t;

/*
 * Cell creation functions
 */

/**
 * Create a new fixed-length cell
 */
cell_t* cell_new(circuit_id_t circ_id, uint8_t command);

/**
 * Create a new variable-length cell
 */
var_cell_t* var_cell_new(circuit_id_t circ_id, uint8_t command, uint16_t payload_len);

/**
 * Free a cell
 */
void cell_free(cell_t *cell);
void var_cell_free(var_cell_t *cell);

/*
 * Cell serialization/deserialization
 */

/**
 * Serialize cell to wire format
 * Returns number of bytes written, or -1 on error
 */
int cell_serialize(const cell_t *cell, uint8_t *buffer, size_t buffer_size);
int var_cell_serialize(const var_cell_t *cell, uint8_t *buffer, size_t buffer_size);

/**
 * Deserialize cell from wire format
 * Returns pointer to new cell, or NULL on error
 */
cell_t* cell_deserialize(const uint8_t *buffer, size_t buffer_size);
var_cell_t* var_cell_deserialize(const uint8_t *buffer, size_t buffer_size);

/*
 * Cell I/O functions (socket-based)
 */

/**
 * Send cell over socket
 * Returns 0 on success, -1 on error
 */
int cell_send(int sockfd, const cell_t *cell);
int var_cell_send(int sockfd, const var_cell_t *cell);

/**
 * Receive cell from socket
 * Returns pointer to new cell, or NULL on error
 */
cell_t* cell_recv(int sockfd);
var_cell_t* var_cell_recv(int sockfd, uint8_t command);

/*
 * Specialized cell creation
 */

/**
 * Create a CREATE2 cell for PQ-Ntor handshake
 */
cell_t* cell_create_create2(circuit_id_t circ_id,
                            uint16_t handshake_type,
                            const uint8_t *handshake_data,
                            uint16_t handshake_len);

/**
 * Create a CREATED2 cell
 */
cell_t* cell_create_created2(circuit_id_t circ_id,
                             const uint8_t *handshake_data,
                             uint16_t handshake_len);

/**
 * Create a DESTROY cell
 */
cell_t* cell_create_destroy(circuit_id_t circ_id, uint8_t reason);

/**
 * Create a RELAY cell
 */
cell_t* cell_create_relay(circuit_id_t circ_id,
                          uint8_t relay_command,
                          uint16_t stream_id,
                          const uint8_t *data,
                          uint16_t data_len);

/**
 * Create a RELAY_EARLY cell (for EXTEND2)
 */
cell_t* cell_create_relay_early(circuit_id_t circ_id,
                                uint8_t relay_command,
                                uint16_t stream_id,
                                const uint8_t *data,
                                uint16_t data_len);

/*
 * Utility functions
 */

/**
 * Check if command is variable-length
 */
bool cell_is_var_length(uint8_t command);

/**
 * Get command name (for debugging)
 */
const char* cell_command_to_string(uint8_t command);
const char* relay_command_to_string(uint8_t relay_command);

/**
 * Parse CREATE2 cell payload
 */
int cell_parse_create2(const cell_t *cell,
                       uint16_t *handshake_type,
                       uint8_t *handshake_data,
                       uint16_t *handshake_len);

/**
 * Parse CREATED2 cell payload
 */
int cell_parse_created2(const cell_t *cell,
                        uint8_t *handshake_data,
                        uint16_t *handshake_len);

/**
 * Parse RELAY cell payload
 */
int cell_parse_relay(const cell_t *cell, relay_cell_t *relay);

/**
 * Pack RELAY cell payload
 */
int cell_pack_relay(cell_t *cell, const relay_cell_t *relay);

#endif /* CELL_H */
