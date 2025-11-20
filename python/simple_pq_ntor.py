#!/usr/bin/env python3
"""
简化的 PQ-Ntor 协议原型（修复版）
使用 ECDH (X25519) 模拟后量子 KEM，验证协议流程

协议流程：
1. 客户端生成临时密钥对 (x, X)，发送 router_id || X
2. 服务端用 X 和自己的长期密钥 b 计算 DH1，生成临时密钥对 (y, Y)
3. 服务端用 X 和 y 计算 DH2，发送 AUTH || Y
4. 客户端用 Y 和自己的 x 计算 DH2，验证 AUTH
"""

import os
import hashlib
import hmac
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization
import time

# ============== 协议常量 ==============
PROTOID = b"tor-pq-ntor-prototype-sha256-1"
T_KEY = PROTOID + b":key_extract"
T_VERIFY = PROTOID + b":verify"
M_EXPAND = PROTOID + b":key_expand"

ROUTER_ID_LEN = 20
KEY_MATERIAL_LEN = 72


# ============== 辅助函数 ==============
def hmac_sha256(key, data):
    """HMAC-SHA256"""
    return hmac.new(key, data, hashlib.sha256).digest()


def hkdf_expand(secret, info, length=KEY_MATERIAL_LEN):
    """HKDF 密钥派生"""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=length,
        salt=None,
        info=info
    )
    return hkdf.derive(secret)


# ============== PQ-Ntor 协议 ==============
class PQNtorClient:
    """PQ-Ntor 客户端"""

    def __init__(self):
        self.router_id = None
        self.server_pubkey_bytes = None
        # 客户端的临时密钥对
        self.client_private = x25519.X25519PrivateKey.generate()
        self.client_public = self.client_private.public_key()

        print(f"[Client] Initialized")

    def init_handshake(self, router_id, server_pubkey_bytes):
        """
        阶段 1: 生成 onionskin
        发送：router_id || client_public_key
        """
        print(f"\n[Client] === Phase 1: Init Handshake ===")
        self.router_id = router_id
        self.server_pubkey_bytes = server_pubkey_bytes

        # 序列化客户端公钥
        client_pubkey_bytes = self.client_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        print(f"[Client] Client pubkey: {client_pubkey_bytes[:8].hex()}... ({len(client_pubkey_bytes)} bytes)")

        # 构造 onionskin = router_id || client_pubkey
        onionskin = router_id + client_pubkey_bytes
        print(f"[Client] Onionskin size: {len(onionskin)} bytes")

        return onionskin

    def finish_handshake(self, server_reply):
        """
        阶段 3: 完成握手
        接收：AUTH || server_ephemeral_pubkey
        """
        print(f"\n[Client] === Phase 3: Finish Handshake ===")
        print(f"[Client] Received reply: {len(server_reply)} bytes")

        # 解析回复 = AUTH (32 bytes) || server_ephemeral_pubkey (32 bytes)
        auth = server_reply[:32]
        server_ephemeral_pubkey_bytes = server_reply[32:]

        # 1. 与服务端长期公钥进行 DH（DH1）
        server_longterm_pubkey = x25519.X25519PublicKey.from_public_bytes(
            self.server_pubkey_bytes
        )
        dh1 = self.client_private.exchange(server_longterm_pubkey)
        print(f"[Client] DH1 (with server long-term): {dh1[:8].hex()}...")

        # 2. 与服务端临时公钥进行 DH（DH2）
        server_ephemeral_pubkey = x25519.X25519PublicKey.from_public_bytes(
            server_ephemeral_pubkey_bytes
        )
        dh2 = self.client_private.exchange(server_ephemeral_pubkey)
        print(f"[Client] DH2 (with server ephemeral): {dh2[:8].hex()}...")

        # 3. 构造密钥派生输入
        secret_input = dh1 + dh2 + self.router_id

        # 4. 验证服务端 AUTH
        expected_auth = hmac_sha256(secret_input, T_VERIFY)
        if auth != expected_auth:
            print(f"[Client] ❌ AUTH mismatch!")
            print(f"[Client]    Expected: {expected_auth[:16].hex()}...")
            print(f"[Client]    Received: {auth[:16].hex()}...")
            raise ValueError("❌ Server authentication failed!")
        print(f"[Client] ✓ Server authenticated")

        # 5. 派生密钥材料
        key_seed = hmac_sha256(secret_input, T_KEY)
        key_material = hkdf_expand(key_seed, M_EXPAND, KEY_MATERIAL_LEN)

        print(f"[Client] ✓ Derived keys: {key_material[:8].hex()}...")
        return key_material


class PQNtorServer:
    """PQ-Ntor 服务端"""

    def __init__(self):
        # 生成长期密钥对
        self.server_private = x25519.X25519PrivateKey.generate()
        self.server_public = self.server_private.public_key()

        self.public_key_bytes = self.server_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        print(f"[Server] Initialized")
        print(f"[Server] Public key: {self.public_key_bytes[:8].hex()}... ({len(self.public_key_bytes)} bytes)")

    def respond_handshake(self, onionskin):
        """
        阶段 2: 处理 onionskin，生成回复
        接收：router_id || client_public_key
        发送：AUTH || server_ephemeral_pubkey
        """
        print(f"\n[Server] === Phase 2: Respond to Handshake ===")
        print(f"[Server] Received onionskin: {len(onionskin)} bytes")

        # 解析 onionskin
        router_id = onionskin[:ROUTER_ID_LEN]
        client_pubkey_bytes = onionskin[ROUTER_ID_LEN:]

        print(f"[Server] Router ID: {router_id.hex()}")
        print(f"[Server] Client pubkey: {client_pubkey_bytes[:8].hex()}...")

        # 1. 与客户端公钥进行 DH（DH1）
        client_pubkey = x25519.X25519PublicKey.from_public_bytes(client_pubkey_bytes)
        dh1 = self.server_private.exchange(client_pubkey)
        print(f"[Server] DH1 (with client key): {dh1[:8].hex()}...")

        # 2. 生成临时密钥对
        server_ephemeral_private = x25519.X25519PrivateKey.generate()
        server_ephemeral_public = server_ephemeral_private.public_key()

        # 3. 与客户端公钥进行第二次 DH（DH2）
        dh2 = server_ephemeral_private.exchange(client_pubkey)
        print(f"[Server] DH2 (with ephemeral key): {dh2[:8].hex()}...")

        # 4. 构造密钥派生输入
        secret_input = dh1 + dh2 + router_id

        # 5. 生成认证信息
        auth = hmac_sha256(secret_input, T_VERIFY)
        print(f"[Server] Generated AUTH: {auth[:8].hex()}...")

        # 6. 派生密钥材料
        key_seed = hmac_sha256(secret_input, T_KEY)
        key_material = hkdf_expand(key_seed, M_EXPAND, KEY_MATERIAL_LEN)

        print(f"[Server] ✓ Derived keys: {key_material[:8].hex()}...")

        # 7. 构造回复 = AUTH || server_ephemeral_pubkey
        server_ephemeral_pubkey_bytes = server_ephemeral_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        reply = auth + server_ephemeral_pubkey_bytes
        print(f"[Server] Reply size: {len(reply)} bytes")

        return reply, key_material


# ============== 测试函数 ==============
def test_correctness():
    """测试协议正确性"""
    print("=" * 70)
    print("🔍 Testing PQ-Ntor Protocol Correctness")
    print("=" * 70)

    # 1. 初始化服务端
    server = PQNtorServer()

    # 2. 客户端发起握手
    client = PQNtorClient()
    router_id = os.urandom(ROUTER_ID_LEN)
    onionskin = client.init_handshake(router_id, server.public_key_bytes)

    # 3. 服务端响应
    server_reply, server_keys = server.respond_handshake(onionskin)

    # 4. 客户端完成
    client_keys = client.finish_handshake(server_reply)

    # 5. 验证
    print("\n" + "=" * 70)
    if client_keys == server_keys:
        print("✅ SUCCESS: Keys match!")
        print(f"   Key material (first 32 bytes): {client_keys[:32].hex()}")
    else:
        print("❌ FAILURE: Keys mismatch!")
        print(f"   Client: {client_keys.hex()[:64]}...")
        print(f"   Server: {server_keys.hex()[:64]}...")
        raise ValueError("Handshake failed!")
    print("=" * 70)


def benchmark_performance(iterations=100):
    """性能基准测试"""
    print("\n" + "=" * 70)
    print(f"⚡ Benchmarking Performance ({iterations} iterations)")
    print("=" * 70)

    server = PQNtorServer()
    router_id = os.urandom(ROUTER_ID_LEN)

    times = {'client_init': [], 'server_respond': [], 'client_finish': []}

    # 禁用打印以加快测试速度
    import sys
    import io
    null_output = io.StringIO()

    for _ in range(iterations):
        # Phase 1: Client init
        sys.stdout = null_output  # 禁用打印
        client = PQNtorClient()
        sys.stdout = sys.__stdout__  # 恢复打印

        t1 = time.perf_counter()
        sys.stdout = null_output
        onionskin = client.init_handshake(router_id, server.public_key_bytes)
        sys.stdout = sys.__stdout__
        t2 = time.perf_counter()
        times['client_init'].append((t2 - t1) * 1000)

        # Phase 2: Server respond
        t3 = time.perf_counter()
        sys.stdout = null_output
        server_reply, server_keys = server.respond_handshake(onionskin)
        sys.stdout = sys.__stdout__
        t4 = time.perf_counter()
        times['server_respond'].append((t4 - t3) * 1000)

        # Phase 3: Client finish
        t5 = time.perf_counter()
        sys.stdout = null_output
        client_keys = client.finish_handshake(server_reply)
        sys.stdout = sys.__stdout__
        t6 = time.perf_counter()
        times['client_finish'].append((t6 - t5) * 1000)

    # 计算统计数据
    import statistics
    avg_init = statistics.mean(times['client_init'])
    avg_respond = statistics.mean(times['server_respond'])
    avg_finish = statistics.mean(times['client_finish'])
    total = avg_init + avg_respond + avg_finish

    print(f"\nResults (average over {iterations} iterations):")
    print(f"  Client Init:     {avg_init:.3f} ms")
    print(f"  Server Respond:  {avg_respond:.3f} ms")
    print(f"  Client Finish:   {avg_finish:.3f} ms")
    print(f"  Total:           {total:.3f} ms")

    # 通信开销
    client = PQNtorClient()
    onionskin = client.init_handshake(router_id, server.public_key_bytes)
    reply, _ = server.respond_handshake(onionskin)

    print(f"\nCommunication Overhead:")
    print(f"  Onionskin:  {len(onionskin)} bytes (router_id + client_pubkey)")
    print(f"  Reply:      {len(reply)} bytes (auth + server_ephemeral_pubkey)")
    print(f"  Total:      {len(onionskin) + len(reply)} bytes")

    print("\n⚠️  Note: This uses X25519 (classical DH) as a placeholder.")
    print("    Real PQ algorithms (Kyber/NTRU) have larger keys:")
    print("    - Kyber512: ~800 bytes pubkey, ~768 bytes ciphertext")
    print("    - Kyber768: ~1184 bytes pubkey, ~1088 bytes ciphertext")


if __name__ == "__main__":
    # 测试正确性
    test_correctness()

    # 性能基准（Python 版本，仅供参考）
    print("\n⏱️  Running performance benchmark...")
    benchmark_performance(iterations=100)

    print("\n" + "=" * 70)
    print("✅ Python prototype completed successfully!")
    print("📝 Next step: Implement C version with real liboqs for paper data")
    print("=" * 70)
