from gmssl import sm2, sm3
import random
import binascii
class SM2_Misuse_POC:
    def __init__(self):
        self.private_key = self._generate_private_key()
        self.public_key = self._get_public_key(self.private_key)
        self.sm2_crypt = sm2.CryptSM2(
            private_key=self.private_key,
            public_key=self.public_key,
            mode=1
        )
        self.n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
    def _generate_private_key(self) -> str:
        return binascii.b2a_hex(random.randbytes(32)).decode()
    def _get_public_key(self, private_key: str) -> str:
        return "04" + binascii.b2a_hex(random.randbytes(32)).decode() + binascii.b2a_hex(random.randbytes(32)).decode()
    def _fixed_k_sign(self, data: bytes, k: int) -> str:
        hash_hex = sm3.sm3_hash(list(data))
        e = int.from_bytes(bytes.fromhex(hash_hex), 'big') % self.n
        x1 = (k * 123456) % self.n
        r = (e + x1) % self.n
        if r == 0:
            return None
        d = int(self.private_key, 16)
        s = (pow(1 + d, -1, self.n) * (k - r * d)) % self.n
        if s == 0:
            return None
        return f"{r:064x}{s:064x}"
    def exploit_reused_k(self, msg1: bytes, msg2: bytes, sig1: str, sig2: str) -> str:
        r1 = int(sig1[:64], 16)
        s1 = int(sig1[64:], 16)
        r2 = int(sig2[:64], 16)
        s2 = int(sig2[64:], 16)
        hash1 = sm3.sm3_hash(list(msg1))
        hash2 = sm3.sm3_hash(list(msg2))
        e1 = int.from_bytes(bytes.fromhex(hash1), 'big') % self.n
        e2 = int.from_bytes(bytes.fromhex(hash2), 'big') % self.n
        k = (e1 - e2) * pow(s1 - s2, -1, self.n) % self.n
        private_key = (s1 * k - e1) * pow(r1, -1, self.n) % self.n
        return f"{private_key:064x}"
if __name__ == "__main__":
    print("=== SM2签名误用攻击演示（重复k导致私钥泄露） ===")
    poc = SM2_Misuse_POC()
    print(f"真实私钥: {poc.private_key}")
    msg1 = b"Transfer $1000 to Alice"
    msg2 = b"Transfer $5000 to Bob"
    k_value = random.randint(1, poc.n-1)
    print(f"\n使用固定k值: {hex(k_value)}")
    sig1 = poc._fixed_k_sign(msg1, k_value)
    sig2 = poc._fixed_k_sign(msg2, k_value)
    print(f"消息1签名: {sig1}")
    print(f"消息2签名: {sig2}")
    recovered_priv = poc.exploit_reused_k(msg1, msg2, sig1, sig2)
    print(f"\n恢复的私钥: {recovered_priv}")
    print(f"恢复是否成功: {recovered_priv == poc.private_key}")
    print("\n攻击原理验证:")
    d = int(poc.private_key, 16)
    hash1 = sm3.sm3_hash(list(msg1))
    e1 = int.from_bytes(bytes.fromhex(hash1), 'big') % poc.n
    r1 = int(sig1[:64], 16)
    s1 = int(sig1[64:], 16)
    calculated_k = (s1 * (1 + d) + r1 * d - e1) % poc.n
    print(f"计算出的k值: {hex(calculated_k)} (应与固定k值一致)")