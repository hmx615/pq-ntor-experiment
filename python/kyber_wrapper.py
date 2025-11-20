#!/usr/bin/env python3
"""
简单的 Kyber KEM 封装 (使用 ctypes 调用 liboqs)
"""

import ctypes
import os
from typing import Tuple

# liboqs 库路径
LIBOQS_PATH = os.path.expanduser("~/_oqs/lib/liboqs.so.0.11.0")

class KyberKEM:
    """Kyber KEM 封装类"""

    # Kyber 参数 (Kyber512)
    ALGORITHM = "Kyber512"
    PUBLIC_KEY_LEN = 800
    SECRET_KEY_LEN = 1632
    CIPHERTEXT_LEN = 768
    SHARED_SECRET_LEN = 32

    def __init__(self):
        """初始化 liboqs 库"""
        if not os.path.exists(LIBOQS_PATH):
            raise FileNotFoundError(f"liboqs library not found at {LIBOQS_PATH}")

        self.lib = ctypes.CDLL(LIBOQS_PATH)

        # 定义函数签名
        # OQS_KEM *OQS_KEM_new(const char *method_name);
        self.lib.OQS_KEM_new.argtypes = [ctypes.c_char_p]
        self.lib.OQS_KEM_new.restype = ctypes.c_void_p

        # void OQS_KEM_free(OQS_KEM *kem);
        self.lib.OQS_KEM_free.argtypes = [ctypes.c_void_p]
        self.lib.OQS_KEM_free.restype = None

        # OQS_STATUS OQS_KEM_keypair(const OQS_KEM *kem, uint8_t *public_key, uint8_t *secret_key);
        self.lib.OQS_KEM_keypair.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
        self.lib.OQS_KEM_keypair.restype = ctypes.c_int

        # OQS_STATUS OQS_KEM_encaps(const OQS_KEM *kem, uint8_t *ciphertext, uint8_t *shared_secret, const uint8_t *public_key);
        self.lib.OQS_KEM_encaps.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self.lib.OQS_KEM_encaps.restype = ctypes.c_int

        # OQS_STATUS OQS_KEM_decaps(const OQS_KEM *kem, uint8_t *shared_secret, const uint8_t *ciphertext, const uint8_t *secret_key);
        self.lib.OQS_KEM_decaps.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        self.lib.OQS_KEM_decaps.restype = ctypes.c_int

        # 创建 KEM 实例
        self.kem = self.lib.OQS_KEM_new(self.ALGORITHM.encode('utf-8'))
        if not self.kem:
            raise RuntimeError(f"Failed to initialize {self.ALGORITHM}")

        print(f"[Kyber] Initialized {self.ALGORITHM}")
        print(f"[Kyber]   Public key: {self.PUBLIC_KEY_LEN} bytes")
        print(f"[Kyber]   Ciphertext: {self.CIPHERTEXT_LEN} bytes")
        print(f"[Kyber]   Shared secret: {self.SHARED_SECRET_LEN} bytes")

    def __del__(self):
        """清理资源"""
        if hasattr(self, 'kem') and self.kem:
            self.lib.OQS_KEM_free(self.kem)

    def keypair(self) -> Tuple[bytes, bytes]:
        """
        生成 Kyber 密钥对

        Returns:
            (public_key, secret_key)
        """
        public_key = ctypes.create_string_buffer(self.PUBLIC_KEY_LEN)
        secret_key = ctypes.create_string_buffer(self.SECRET_KEY_LEN)

        status = self.lib.OQS_KEM_keypair(self.kem, public_key, secret_key)
        if status != 0:  # OQS_SUCCESS = 0
            raise RuntimeError("Kyber keypair generation failed")

        return bytes(public_key), bytes(secret_key)

    def encapsulate(self, public_key: bytes) -> Tuple[bytes, bytes]:
        """
        封装：生成密文和共享密钥

        Args:
            public_key: 对方的公钥

        Returns:
            (ciphertext, shared_secret)
        """
        if len(public_key) != self.PUBLIC_KEY_LEN:
            raise ValueError(f"Invalid public key length: {len(public_key)} (expected {self.PUBLIC_KEY_LEN})")

        ciphertext = ctypes.create_string_buffer(self.CIPHERTEXT_LEN)
        shared_secret = ctypes.create_string_buffer(self.SHARED_SECRET_LEN)

        status = self.lib.OQS_KEM_encaps(self.kem, ciphertext, shared_secret, public_key)
        if status != 0:
            raise RuntimeError("Kyber encapsulation failed")

        return bytes(ciphertext), bytes(shared_secret)

    def decapsulate(self, ciphertext: bytes, secret_key: bytes) -> bytes:
        """
        解封装：从密文恢复共享密钥

        Args:
            ciphertext: 密文
            secret_key: 自己的私钥

        Returns:
            shared_secret
        """
        if len(ciphertext) != self.CIPHERTEXT_LEN:
            raise ValueError(f"Invalid ciphertext length: {len(ciphertext)} (expected {self.CIPHERTEXT_LEN})")
        if len(secret_key) != self.SECRET_KEY_LEN:
            raise ValueError(f"Invalid secret key length: {len(secret_key)} (expected {self.SECRET_KEY_LEN})")

        shared_secret = ctypes.create_string_buffer(self.SHARED_SECRET_LEN)

        status = self.lib.OQS_KEM_decaps(self.kem, shared_secret, ciphertext, secret_key)
        if status != 0:
            raise RuntimeError("Kyber decapsulation failed")

        return bytes(shared_secret)


def test_kyber():
    """测试 Kyber KEM 基本功能"""
    print("=" * 70)
    print("🧪 Testing Kyber KEM")
    print("=" * 70)

    kem = KyberKEM()

    # 1. 生成密钥对
    print("\n1. Generating keypair...")
    public_key, secret_key = kem.keypair()
    print(f"   Public key:  {public_key[:8].hex()}... ({len(public_key)} bytes)")
    print(f"   Secret key:  {secret_key[:8].hex()}... ({len(secret_key)} bytes)")

    # 2. 封装
    print("\n2. Encapsulating...")
    ciphertext, shared_secret_alice = kem.encapsulate(public_key)
    print(f"   Ciphertext:       {ciphertext[:8].hex()}... ({len(ciphertext)} bytes)")
    print(f"   Shared secret:    {shared_secret_alice[:8].hex()}... ({len(shared_secret_alice)} bytes)")

    # 3. 解封装
    print("\n3. Decapsulating...")
    shared_secret_bob = kem.decapsulate(ciphertext, secret_key)
    print(f"   Shared secret:    {shared_secret_bob[:8].hex()}... ({len(shared_secret_bob)} bytes)")

    # 4. 验证
    print("\n4. Verification:")
    if shared_secret_alice == shared_secret_bob:
        print("   ✅ SUCCESS: Shared secrets match!")
    else:
        print("   ❌ FAILURE: Shared secrets do NOT match!")
        raise ValueError("Kyber KEM test failed!")

    print("=" * 70)


if __name__ == "__main__":
    test_kyber()
