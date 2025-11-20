/**
 * cell.c - Tor Cell Format Implementation
 */

#include "cell.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <arpa/inet.h>  // For htonl, htons, ntohl, ntohs
#include <unistd.h>     // For read, write
#include <errno.h>

/*
 * Cell creation and destruction
 */

cell_t* cell_new(circuit_id_t circ_id, uint8_t command) {
    cell_t *cell = calloc(1, sizeof(cell_t));
    if (!cell) {
        return NULL;
    }
    cell->circ_id = circ_id;
    cell->command = command;
    return cell;
}

var_cell_t* var_cell_new(circuit_id_t circ_id, uint8_t command, uint16_t payload_len) {
    var_cell_t *cell = calloc(1, sizeof(var_cell_t));
    if (!cell) {
        return NULL;
    }

    cell->circ_id = circ_id;
    cell->command = command;
    cell->payload_len = payload_len;

    if (payload_len > 0) {
        cell->payload = calloc(payload_len, 1);
        if (!cell->payload) {
            free(cell);
            return NULL;
        }
    }

    return cell;
}

void cell_free(cell_t *cell) {
    if (cell) {
        // Clear sensitive data
        memset(cell, 0, sizeof(cell_t));
        free(cell);
    }
}

void var_cell_free(var_cell_t *cell) {
    if (cell) {
        if (cell->payload) {
            memset(cell->payload, 0, cell->payload_len);
            free(cell->payload);
        }
        memset(cell, 0, sizeof(var_cell_t));
        free(cell);
    }
}

/*
 * Serialization
 */

int cell_serialize(const cell_t *cell, uint8_t *buffer, size_t buffer_size) {
    if (!cell || !buffer || buffer_size < CELL_LEN) {
        return -1;
    }

    // CircID (4 bytes, network byte order)
    uint32_t circ_id_net = htonl(cell->circ_id);
    memcpy(buffer, &circ_id_net, 4);

    // Command (1 byte)
    buffer[4] = cell->command;

    // Payload (507 bytes)
    memcpy(buffer + 5, cell->payload, CELL_PAYLOAD_LEN);

    return CELL_LEN;
}

int var_cell_serialize(const var_cell_t *cell, uint8_t *buffer, size_t buffer_size) {
    if (!cell || !buffer) {
        return -1;
    }

    size_t total_len = VAR_CELL_HEADER_LEN + cell->payload_len;
    if (buffer_size < total_len) {
        return -1;
    }

    // CircID (4 bytes, network byte order)
    uint32_t circ_id_net = htonl(cell->circ_id);
    memcpy(buffer, &circ_id_net, 4);

    // Command (1 byte)
    buffer[4] = cell->command;

    // Length (2 bytes, network byte order)
    uint16_t len_net = htons(cell->payload_len);
    memcpy(buffer + 5, &len_net, 2);

    // Payload
    if (cell->payload_len > 0 && cell->payload) {
        memcpy(buffer + 7, cell->payload, cell->payload_len);
    }

    return total_len;
}

/*
 * Deserialization
 */

cell_t* cell_deserialize(const uint8_t *buffer, size_t buffer_size) {
    if (!buffer || buffer_size < CELL_LEN) {
        return NULL;
    }

    // Parse CircID
    uint32_t circ_id_net;
    memcpy(&circ_id_net, buffer, 4);
    circuit_id_t circ_id = ntohl(circ_id_net);

    // Parse command
    uint8_t command = buffer[4];

    // Create cell
    cell_t *cell = cell_new(circ_id, command);
    if (!cell) {
        return NULL;
    }

    // Copy payload
    memcpy(cell->payload, buffer + 5, CELL_PAYLOAD_LEN);

    return cell;
}

var_cell_t* var_cell_deserialize(const uint8_t *buffer, size_t buffer_size) {
    if (!buffer || buffer_size < VAR_CELL_HEADER_LEN) {
        return NULL;
    }

    // Parse CircID
    uint32_t circ_id_net;
    memcpy(&circ_id_net, buffer, 4);
    circuit_id_t circ_id = ntohl(circ_id_net);

    // Parse command
    uint8_t command = buffer[4];

    // Parse length
    uint16_t len_net;
    memcpy(&len_net, buffer + 5, 2);
    uint16_t payload_len = ntohs(len_net);

    // Check buffer size
    if (buffer_size < VAR_CELL_HEADER_LEN + payload_len) {
        return NULL;
    }

    // Create cell
    var_cell_t *cell = var_cell_new(circ_id, command, payload_len);
    if (!cell) {
        return NULL;
    }

    // Copy payload
    if (payload_len > 0) {
        memcpy(cell->payload, buffer + 7, payload_len);
    }

    return cell;
}

/*
 * Socket I/O
 */

int cell_send(int sockfd, const cell_t *cell) {
    uint8_t buffer[CELL_LEN];
    int len = cell_serialize(cell, buffer, sizeof(buffer));
    if (len < 0) {
        return -1;
    }

    ssize_t sent = write(sockfd, buffer, len);
    if (sent != len) {
        return -1;
    }

    return 0;
}

int var_cell_send(int sockfd, const var_cell_t *cell) {
    size_t buffer_size = VAR_CELL_HEADER_LEN + cell->payload_len;
    uint8_t *buffer = malloc(buffer_size);
    if (!buffer) {
        return -1;
    }

    int len = var_cell_serialize(cell, buffer, buffer_size);
    if (len < 0) {
        free(buffer);
        return -1;
    }

    ssize_t sent = write(sockfd, buffer, len);
    free(buffer);

    if (sent != len) {
        return -1;
    }

    return 0;
}

cell_t* cell_recv(int sockfd) {
    uint8_t buffer[CELL_LEN];
    ssize_t received = 0;
    int retry_count = 0;
    const int MAX_RETRIES = 10;  // Limit retries for non-blocking sockets

    // Read full cell
    while (received < CELL_LEN) {
        ssize_t n = read(sockfd, buffer + received, CELL_LEN - received);
        if (n < 0) {
            if (errno == EAGAIN || errno == EWOULDBLOCK) {
                // Timeout or non-blocking socket with no data
                // For blocking sockets with SO_RCVTIMEO, this means timeout - return NULL
                // For non-blocking sockets, retry a limited number of times
                retry_count++;
                if (retry_count > MAX_RETRIES) {
                    // fprintf(stderr, "[cell_recv] Timeout after %d retries\n", retry_count);
                    return NULL;
                }
                usleep(1000);  // Wait 1ms before retry
                continue;
            }
            fprintf(stderr, "[cell_recv] Read error: %s\n", strerror(errno));
            return NULL;
        }
        if (n == 0) {
            // Connection closed
            fprintf(stderr, "[cell_recv] Connection closed (received %zd/%d bytes)\n",
                    received, CELL_LEN);
            return NULL;
        }
        received += n;
        retry_count = 0;  // Reset retry count on successful read
    }

    return cell_deserialize(buffer, CELL_LEN);
}

var_cell_t* var_cell_recv(int sockfd, uint8_t command) {
    uint8_t header[VAR_CELL_HEADER_LEN];
    ssize_t received = 0;

    // Read header
    while (received < VAR_CELL_HEADER_LEN) {
        ssize_t n = read(sockfd, header + received, VAR_CELL_HEADER_LEN - received);
        if (n <= 0) {
            return NULL;
        }
        received += n;
    }

    // Parse payload length
    uint16_t len_net;
    memcpy(&len_net, header + 5, 2);
    uint16_t payload_len = ntohs(len_net);

    // Allocate full buffer
    size_t total_len = VAR_CELL_HEADER_LEN + payload_len;
    uint8_t *buffer = malloc(total_len);
    if (!buffer) {
        return NULL;
    }

    // Copy header
    memcpy(buffer, header, VAR_CELL_HEADER_LEN);

    // Read payload
    received = 0;
    while (received < payload_len) {
        ssize_t n = read(sockfd, buffer + VAR_CELL_HEADER_LEN + received,
                        payload_len - received);
        if (n <= 0) {
            free(buffer);
            return NULL;
        }
        received += n;
    }

    var_cell_t *cell = var_cell_deserialize(buffer, total_len);
    free(buffer);
    return cell;
}

/*
 * Specialized cell creation
 */

cell_t* cell_create_create2(circuit_id_t circ_id,
                            uint16_t handshake_type,
                            const uint8_t *handshake_data,
                            uint16_t handshake_len) {
    if (!handshake_data || handshake_len > CELL_PAYLOAD_LEN - 4) {
        return NULL;
    }

    cell_t *cell = cell_new(circ_id, CELL_CREATE2);
    if (!cell) {
        return NULL;
    }

    // Pack CREATE2 payload
    uint16_t htype_net = htons(handshake_type);
    uint16_t hlen_net = htons(handshake_len);

    memcpy(cell->payload, &htype_net, 2);
    memcpy(cell->payload + 2, &hlen_net, 2);
    memcpy(cell->payload + 4, handshake_data, handshake_len);

    return cell;
}

cell_t* cell_create_created2(circuit_id_t circ_id,
                             const uint8_t *handshake_data,
                             uint16_t handshake_len) {
    if (!handshake_data || handshake_len > CELL_PAYLOAD_LEN - 2) {
        return NULL;
    }

    cell_t *cell = cell_new(circ_id, CELL_CREATED2);
    if (!cell) {
        return NULL;
    }

    // Pack CREATED2 payload
    uint16_t hlen_net = htons(handshake_len);
    memcpy(cell->payload, &hlen_net, 2);
    memcpy(cell->payload + 2, handshake_data, handshake_len);

    return cell;
}

cell_t* cell_create_destroy(circuit_id_t circ_id, uint8_t reason) {
    cell_t *cell = cell_new(circ_id, CELL_DESTROY);
    if (!cell) {
        return NULL;
    }

    cell->payload[0] = reason;
    return cell;
}

cell_t* cell_create_relay(circuit_id_t circ_id,
                          uint8_t relay_command,
                          uint16_t stream_id,
                          const uint8_t *data,
                          uint16_t data_len) {
    if (data_len > CELL_PAYLOAD_LEN - 11) {  // Max RELAY data size (payload - header)
        fprintf(stderr, "[cell_create_relay] Data too large: %u > %d\n", data_len, CELL_PAYLOAD_LEN - 11);
        return NULL;
    }

    cell_t *cell = cell_new(circ_id, CELL_RELAY);
    if (!cell) {
        return NULL;
    }

    relay_cell_t relay;
    memset(&relay, 0, sizeof(relay));

    relay.relay_command = relay_command;
    relay.recognized = 0;
    relay.stream_id = stream_id;
    relay.digest = 0;  // Will be filled by crypto layer
    relay.length = data_len;

    if (data && data_len > 0) {
        memcpy(relay.data, data, data_len);
    }

    cell_pack_relay(cell, &relay);
    return cell;
}

cell_t* cell_create_relay_early(circuit_id_t circ_id,
                                uint8_t relay_command,
                                uint16_t stream_id,
                                const uint8_t *data,
                                uint16_t data_len) {
    cell_t *cell = cell_create_relay(circ_id, relay_command, stream_id, data, data_len);
    if (cell) {
        cell->command = CELL_RELAY_EARLY;
    }
    return cell;
}

/*
 * Utility functions
 */

bool cell_is_var_length(uint8_t command) {
    return (command == CELL_VERSIONS ||
            command == CELL_PADDING_NEGOTIATE);
}

const char* cell_command_to_string(uint8_t command) {
    switch (command) {
        case CELL_PADDING: return "PADDING";
        case CELL_CREATE: return "CREATE";
        case CELL_CREATED: return "CREATED";
        case CELL_RELAY: return "RELAY";
        case CELL_DESTROY: return "DESTROY";
        case CELL_CREATE_FAST: return "CREATE_FAST";
        case CELL_CREATED_FAST: return "CREATED_FAST";
        case CELL_VERSIONS: return "VERSIONS";
        case CELL_NETINFO: return "NETINFO";
        case CELL_RELAY_EARLY: return "RELAY_EARLY";
        case CELL_CREATE2: return "CREATE2";
        case CELL_CREATED2: return "CREATED2";
        case CELL_PADDING_NEGOTIATE: return "PADDING_NEGOTIATE";
        default: return "UNKNOWN";
    }
}

const char* relay_command_to_string(uint8_t relay_command) {
    switch (relay_command) {
        case RELAY_BEGIN: return "BEGIN";
        case RELAY_DATA: return "DATA";
        case RELAY_END: return "END";
        case RELAY_CONNECTED: return "CONNECTED";
        case RELAY_SENDME: return "SENDME";
        case RELAY_EXTEND: return "EXTEND";
        case RELAY_EXTENDED: return "EXTENDED";
        case RELAY_TRUNCATE: return "TRUNCATE";
        case RELAY_TRUNCATED: return "TRUNCATED";
        case RELAY_DROP: return "DROP";
        case RELAY_RESOLVE: return "RESOLVE";
        case RELAY_RESOLVED: return "RESOLVED";
        case RELAY_BEGIN_DIR: return "BEGIN_DIR";
        case RELAY_EXTEND2: return "EXTEND2";
        case RELAY_EXTENDED2: return "EXTENDED2";
        default: return "UNKNOWN";
    }
}

/*
 * Parsing functions
 */

int cell_parse_create2(const cell_t *cell,
                       uint16_t *handshake_type,
                       uint8_t *handshake_data,
                       uint16_t *handshake_len) {
    if (!cell || cell->command != CELL_CREATE2) {
        return -1;
    }

    // Parse handshake type
    uint16_t htype_net;
    memcpy(&htype_net, cell->payload, 2);
    *handshake_type = ntohs(htype_net);

    // Parse handshake length
    uint16_t hlen_net;
    memcpy(&hlen_net, cell->payload + 2, 2);
    *handshake_len = ntohs(hlen_net);

    // Check length
    if (*handshake_len > CELL_PAYLOAD_LEN - 4) {
        return -1;
    }

    // Copy handshake data
    if (handshake_data) {
        memcpy(handshake_data, cell->payload + 4, *handshake_len);
    }

    return 0;
}

int cell_parse_created2(const cell_t *cell,
                        uint8_t *handshake_data,
                        uint16_t *handshake_len) {
    if (!cell || cell->command != CELL_CREATED2) {
        return -1;
    }

    // Parse handshake length
    uint16_t hlen_net;
    memcpy(&hlen_net, cell->payload, 2);
    *handshake_len = ntohs(hlen_net);

    // Check length
    if (*handshake_len > CELL_PAYLOAD_LEN - 2) {
        return -1;
    }

    // Copy handshake data
    if (handshake_data) {
        memcpy(handshake_data, cell->payload + 2, *handshake_len);
    }

    return 0;
}

int cell_parse_relay(const cell_t *cell, relay_cell_t *relay) {
    if (!cell || !relay) {
        return -1;
    }

    if (cell->command != CELL_RELAY && cell->command != CELL_RELAY_EARLY) {
        return -1;
    }

    // Parse RELAY cell fields (all in network byte order)
    relay->relay_command = cell->payload[0];

    uint16_t recognized_net;
    memcpy(&recognized_net, cell->payload + 1, 2);
    relay->recognized = ntohs(recognized_net);

    uint16_t stream_id_net;
    memcpy(&stream_id_net, cell->payload + 3, 2);
    relay->stream_id = ntohs(stream_id_net);

    uint32_t digest_net;
    memcpy(&digest_net, cell->payload + 5, 4);
    relay->digest = ntohl(digest_net);

    uint16_t length_net;
    memcpy(&length_net, cell->payload + 9, 2);
    relay->length = ntohs(length_net);

    // Check length (dynamic based on cell size)
    if (relay->length > CELL_PAYLOAD_LEN - 11) {
        fprintf(stderr, "[cell_parse_relay] Invalid length: %u > %d\n",
                relay->length, CELL_PAYLOAD_LEN - 11);
        return -1;
    }

    // Copy data
    memcpy(relay->data, cell->payload + 11, relay->length);

    return 0;
}

int cell_pack_relay(cell_t *cell, const relay_cell_t *relay) {
    if (!cell || !relay) {
        return -1;
    }

    if (relay->length > CELL_PAYLOAD_LEN - 11) {
        fprintf(stderr, "[cell_pack_relay] Data too large: %u > %d\n",
                relay->length, CELL_PAYLOAD_LEN - 11);
        return -1;
    }

    // Clear payload first
    memset(cell->payload, 0, CELL_PAYLOAD_LEN);

    // Pack RELAY cell fields (all in network byte order)
    cell->payload[0] = relay->relay_command;

    uint16_t recognized_net = htons(relay->recognized);
    memcpy(cell->payload + 1, &recognized_net, 2);

    uint16_t stream_id_net = htons(relay->stream_id);
    memcpy(cell->payload + 3, &stream_id_net, 2);

    uint32_t digest_net = htonl(relay->digest);
    memcpy(cell->payload + 5, &digest_net, 4);

    uint16_t length_net = htons(relay->length);
    memcpy(cell->payload + 9, &length_net, 2);

    // Copy data
    if (relay->length > 0) {
        memcpy(cell->payload + 11, relay->data, relay->length);
    }

    return 0;
}
