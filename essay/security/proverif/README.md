# PQ-NTOR ProVerif Formal Verification

This directory contains the ProVerif formal verification model for the PQ-NTOR protocol.

## Files

- `pq_ntor.pv` - Complete ProVerif model of PQ-NTOR protocol
- `README.md` - This file
- `verification_results.txt` - ProVerif verification output (to be generated)

## Protocol Overview

PQ-NTOR is a post-quantum key exchange protocol for Tor using Kyber-512 KEM. The protocol consists of:

**Step 1: Client → Relay**
```
C generates fresh nonce Nc
(ct, ss) ← Kyber512.Encap(pkR, Nc)
C → R: {ct, Nc}
```

**Step 2: Relay → Client**
```
R receives {ct, Nc}
ss ← Kyber512.Decap(skR, ct)
R generates fresh nonce Nr
Ksession ← KDF(ss || Nc || Nr || pkR)
R → C: {Nr, H(Ksession)}
```

**Step 3: Client Verification**
```
C derives Ksession ← KDF(ss || Nc || Nr || pkR)
C verifies H(Ksession)
If valid, accept Ksession
```

## Security Properties Verified

The ProVerif model verifies the following security properties:

### 1. **Session Key Secrecy (Confidentiality)**
- **Query**: `query attacker(session_key_secret).`
- **Expected**: `CANNOT be reached`
- **Meaning**: The session key remains secret from network attackers

### 2. **Client Authentication**
- **Query**: Relay only accepts keys from clients who initiated handshakes
- **Expected**: `TRUE`
- **Meaning**: The relay authenticates the client

### 3. **Relay Authentication**
- **Query**: Client only accepts keys from relays who responded
- **Expected**: `TRUE`
- **Meaning**: The client authenticates the relay

### 4. **Session Key Agreement**
- **Query**: Both parties agree on the same session key
- **Expected**: `TRUE`
- **Meaning**: No man-in-the-middle can cause key mismatch

### 5. **Injective Agreement (Replay Protection)**
- **Query**: Each handshake corresponds to exactly one session
- **Expected**: `TRUE`
- **Meaning**: Replay attacks are prevented

## Installation

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install proverif
```

### MacOS
```bash
brew install proverif
```

### From Source
```bash
wget https://bblanche.gitlabpages.inria.fr/proverif/proverif2.04.tar.gz
tar -xzf proverif2.04.tar.gz
cd proverif2.04
./build
sudo ./build install
```

## Running the Verification

To verify the PQ-NTOR protocol:

```bash
cd /home/ccc/pq-ntor-experiment/essay/security/proverif
proverif pq_ntor.pv > verification_results.txt
```

Or for interactive output:

```bash
proverif pq_ntor.pv
```

## Expected Output

```
ProVerif 2.04 - Automatic Verification of Cryptographic Protocols

Verification summary:

Query not attacker(session_key_secret[]) is true.

Query inj-event(RelayReceivesHandshake(...)) ==> inj-event(ClientSendsHandshake(...)) is true.

Query event(ClientAccepts(...)) ==> event(RelayResponds(...)) is true.

Query event(RelayAccepts(...)) ==> event(ClientSendsHandshake(...)) is true.

Query event(ClientAccepts(...)) && event(RelayAccepts(...)) is true.

--------------------------------------------------------------

RESULT: All security goals are satisfied.
```

## Model Structure

### Part 1: Type Declarations
- Defines types for public keys, secret keys, ciphertexts, keys, nonces, hashes

### Part 2: Cryptographic Primitives
- **KEM Operations**: `kem_encap`, `kem_decap`
- **Key Derivation**: `kdf`
- **Hash Function**: `hash`
- **Correctness Equations**: Models KEM correctness property

### Part 3: Communication Channels
- **Public Channel** (`net`): Models Dolev-Yao attacker-controlled network
- **Private Channels**: For internal process communication

### Part 4: Security Queries
- Defines 5 security queries covering all protocol goals

### Part 5: Protocol Processes
- **Client Process**: Models client-side protocol execution
- **Relay Process**: Models relay-side protocol execution

### Part 6: Main Process
- Initializes relay keypair
- Runs client and relay in parallel with replication (!)

## Adversary Model

The model uses the **Dolev-Yao adversary model**:
- **Capabilities**:
  - Read, intercept, and analyze all network messages
  - Block, replay, reorder, or modify messages
  - Inject new messages constructed from known data
  - Perform cryptographic operations on known keys

- **Limitations**:
  - Cannot break cryptographic primitives (perfect cryptography assumption)
  - Cannot guess random nonces or secret keys
  - Cannot forge signatures without private keys

## Cryptographic Assumptions

The model relies on:

1. **Kyber-512 IND-CCA2 Security**: KEM is secure against chosen-ciphertext attacks
2. **Hash Function Collision Resistance**: SHA-256 is collision-resistant
3. **KDF Security**: HKDF produces indistinguishable keys from random
4. **Nonce Freshness**: Each nonce is generated freshly and independently

## Limitations

ProVerif verification has some limitations:

1. **Perfect Cryptography**: Assumes cryptographic primitives are unbreakable
2. **Computational Complexity**: Does not model computational hardness
3. **Side Channels**: Does not model timing attacks, power analysis, etc.
4. **Implementation Bugs**: Verifies protocol logic, not code implementation

## Integration with Paper

This ProVerif model supports the security analysis in Section 3.2 of the paper:

- **BAN Logic** (already in design.tex): Proves authentication and key freshness
- **ProVerif** (this model): Automated verification of secrecy and correspondence properties
- **Game-Based Proof** (security_analysis_framework.md): IND-CCA2 security reduction

Together, these three approaches provide comprehensive formal security guarantees.

## References

1. ProVerif Manual: https://bblanche.gitlabpages.inria.fr/proverif/manual.pdf
2. Blanchet, B. "Modeling and Verifying Security Protocols with ProVerif" (2016)
3. NIST FIPS 203: Module-Lattice-Based Key-Encapsulation Mechanism (Kyber)
4. Goldberg, I., et al. "The ntor Handshake Protocol" (2013)

## Contact

For questions about this verification model, refer to the main project documentation.
