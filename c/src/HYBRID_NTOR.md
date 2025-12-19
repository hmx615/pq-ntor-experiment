# Hybrid NTOR Protocol Implementation

## Overview

This implementation provides a **hybrid post-quantum key exchange** protocol combining:
- **Kyber-512** (NIST PQC standard, lattice-based KEM)
- **X25519** (Curve25519 ECDH)

The hybrid approach provides security against both classical and quantum adversaries, following the design principles from IETF draft-ietf-tls-hybrid-design.

## Files

| File | Description |
|------|-------------|
| `hybrid_ntor.h` | Protocol interface and data structures |
| `hybrid_ntor.c` | Core implementation (~450 lines) |
| `../tests/test_hybrid_ntor.c` | Unit tests and benchmarks |

## Protocol Design

### Message Sizes
- **Onionskin**: 852 bytes
  - Kyber-512 public key: 800 bytes
  - X25519 public key: 32 bytes
  - Relay identity: 20 bytes

- **Reply**: 832 bytes
  - Kyber-512 ciphertext: 768 bytes
  - X25519 public key: 32 bytes
  - AUTH tag: 32 bytes (HMAC-SHA256)

### Key Derivation

```
1. Client generates:
   - Kyber keypair (pk_kyber, sk_kyber)
   - X25519 keypair (pk_x25519, sk_x25519)

2. Server receives onionskin and:
   - Encapsulates to client's Kyber pk -> (ct_kyber, ss_kyber)
   - Generates X25519 keypair and computes ECDH -> ss_x25519

3. Hybrid shared secret combination:
   hybrid_ss = HKDF(kyber_ss || x25519_ss, "hybrid-ntor-combine")

4. Key derivation:
   transcript = kyber_pk || x25519_pk_client || kyber_ct || x25519_pk_server || relay_id
   (K_auth, K_enc) = HKDF(hybrid_ss, SHA256(transcript), "hybrid-ntor-keys")

5. Authentication:
   AUTH = HMAC(K_auth, transcript || "server")
```

### Security Properties
- **IND-CCA2**: From Kyber-512 KEM
- **Forward secrecy**: Ephemeral keys for both Kyber and X25519
- **Hybrid security**: Secure if either Kyber OR X25519 remains unbroken
- **Transcript binding**: All public values included in key derivation

## API Usage

### Client Side
```c
hybrid_ntor_client_state client_state;
uint8_t onionskin[HYBRID_NTOR_ONIONSKIN_LEN];
uint8_t relay_identity[20];

// Step 1: Create onionskin
hybrid_ntor_client_create_onionskin(&client_state, onionskin, relay_identity);

// Step 2: Send onionskin to server, receive reply
// ...

// Step 3: Complete handshake
uint8_t reply[HYBRID_NTOR_REPLY_LEN];
if (hybrid_ntor_client_finish_handshake(&client_state, reply) == HYBRID_NTOR_SUCCESS) {
    // client_state.k_enc contains the session key
}

// Cleanup
hybrid_ntor_client_state_cleanup(&client_state);
```

### Server Side
```c
hybrid_ntor_server_state server_state;
uint8_t reply[HYBRID_NTOR_REPLY_LEN];

// Process onionskin and create reply
if (hybrid_ntor_server_create_reply(&server_state, reply, onionskin, relay_identity)
    == HYBRID_NTOR_SUCCESS) {
    // server_state.k_enc contains the session key
}

// Cleanup
hybrid_ntor_server_state_cleanup(&server_state);
```

## Integration with Tor Circuit

The hybrid NTOR is integrated into:
- `relay_node.c`: `relay_node_handle_create2()` uses hybrid_ntor for circuit creation
- `tor_client.c`: `tor_client_create_first_hop()` and `extend_circuit()` use hybrid_ntor

To switch modes, modify the includes in these files:
- `#include "hybrid_ntor.h"` - Hybrid mode (Kyber + X25519)
- `#include "pq_ntor.h"` - Pure PQ mode (Kyber only)
- `#include "classic_ntor.h"` - Classic mode (X25519 only)

## Performance (Phytium Pi ARM64)

Typical performance on Phytium D2000 (ARM64):
- Client create onionskin: ~80 us
- Server create reply: ~90 us
- Client finish handshake: ~20 us
- **Total handshake: ~190 us**

## Dependencies

- **liboqs**: For Kyber-512 KEM (`OQS_KEM_kyber_512_*`)
- **OpenSSL 1.1.1+**: For X25519, HKDF, HMAC-SHA256

Note: OpenSSL 3.0+ specific headers (like `openssl/core_names.h`) are NOT required.

## Build

```bash
cd /home/ccc/pq-ntor-experiment/c
make clean
make all

# Run unit tests
./test_hybrid_ntor
```

## Testing on 7-Pi Cluster

```bash
# Start services (on respective Pis)
# Pi 185: ./directory 5000
# Pi 186: ./relay -r guard -p 6000
# Pi 187: ./relay -r middle -p 6001
# Pi 188: ./relay -r exit -p 6002
# Pi 189: python3 -m http.server 8000

# Run client
./client -d 192.168.5.185 -p 5000 -u http://192.168.5.189:8000/
```

## Version History

- **2025-12-12**: Initial hybrid implementation
  - Combined Kyber-512 + X25519
  - Integrated into relay_node and tor_client
  - Tested on 7-Pi Phytium cluster
  - Fixed OpenSSL 1.1.1 compatibility (removed core_names.h)

## References

- IETF draft-ietf-tls-hybrid-design
- NIST PQC Kyber specification
- Tor ntor handshake specification
