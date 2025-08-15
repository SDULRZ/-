import struct
import threading
from queue import Queue
import time
from math import log2, ceil
from typing import List, Tuple
class SM3:
    IV = [
        0x7380166F, 0x4914B2B9, 0x172442D7, 0xDA8A0600,
        0xA96F30BC, 0x163138AA, 0xE38DEE4D, 0xB0FB0E4E
    ]
    T = [0x79CC4519 if j < 16 else 0x7A879D8A for j in range(64)]
    @staticmethod
    def left_rotate(x, n):
        return ((x << n) | (x >> (32 - n))) & 0xFFFFFFFF
    @staticmethod
    def FF_j(X, Y, Z, j):
        return X ^ Y ^ Z if j < 16 else (X & Y) | (X & Z) | (Y & Z)
    @staticmethod
    def GG_j(X, Y, Z, j):
        return X ^ Y ^ Z if j < 16 else (X & Y) | ((~X) & Z)
    @staticmethod
    def P0(X):
        return X ^ SM3.left_rotate(X, 9) ^ SM3.left_rotate(X, 17)
    @staticmethod
    def P1(X):
        return X ^ SM3.left_rotate(X, 15) ^ SM3.left_rotate(X, 23)
    @staticmethod
    def padding(msg):
        length = len(msg) * 8
        msg += b'\x80'
        while (len(msg) % 64) != 56:
            msg += b'\x00'
        msg += struct.pack('>Q', length)
        return msg
    @classmethod
    def hash(cls, msg: bytes, iv=None) -> bytes:
        msg = cls.padding(msg)
        blocks = [msg[i:i+64] for i in range(0, len(msg), 64)]
        V = iv.copy() if iv else cls.IV.copy()
        for block in blocks:
            W = [0] * 68
            for j in range(16):
                W[j] = struct.unpack('>I', block[j*4:j*4+4])[0]
            for j in range(16, 68):
                W[j] = cls.P1(W[j-16] ^ W[j-9] ^ cls.left_rotate(W[j-3], 15)) ^ cls.left_rotate(W[j-13], 7) ^ W[j-6]
            W1 = [W[j] ^ W[j+4] for j in range(64)]
            A, B, C, D, E, F, G, H = V
            for j in range(64):
                SS1 = cls.left_rotate((cls.left_rotate(A, 12) + E + cls.T[j]) & 0xFFFFFFFF, 7)
                SS2 = SS1 ^ cls.left_rotate(A, 12)
                TT1 = (cls.FF_j(A, B, C, j) + D + SS2 + W1[j]) & 0xFFFFFFFF
                TT2 = (cls.GG_j(E, F, G, j) + H + SS1 + W[j]) & 0xFFFFFFFF
                D, C, B, A = C, cls.left_rotate(B, 9), A, TT1
                H, G, F, E = G, cls.left_rotate(F, 19), E, cls.P0(TT2)
            V = [(x ^ y) & 0xFFFFFFFF for x, y in zip(V, [A, B, C, D, E, F, G, H])]
        return b''.join(struct.pack('>I', x) for x in V)
def length_extension_attack():
    print("\n" + "="*50)
    print("SM3 Length Extension Attack Verification")
    print("="*50)
    secret = b"secret_key_123"
    known = b"known_message"
    extension = b"malicious_extension"
    original_msg = secret + known
    original_hash = SM3.hash(original_msg)
    print(f"Original hash: {original_hash.hex()}")
    forged_iv = [int.from_bytes(original_hash[i:i+4], 'big') for i in range(0, 32, 4)]
    pad_len = (len(original_msg) + 9 + 63) // 64 * 64 - len(original_msg)
    padding = b'\x80' + b'\x00' * (pad_len - 9) + struct.pack('>Q', len(original_msg)*8)
    forged_hash = SM3.hash(extension, iv=forged_iv)
    full_msg = original_msg + padding + extension
    legit_hash = SM3.hash(full_msg)
    print(f"Forged hash:  {forged_hash.hex()}")
    print(f"Legit hash:   {legit_hash.hex()}")
    print(f"Attack {'succeeded' if forged_hash == legit_hash else 'failed'}!")
class MerkleTree:
    def __init__(self, data: List[bytes]):
        self.leaves = [self._hash_leaf(d) for d in data]
        self.tree = self.build_tree(self.leaves)
        self.root = self.tree[-1][0] if self.tree else b''
    @staticmethod
    def _hash_leaf(data: bytes) -> bytes:
        return SM3.hash(b'\x00' + data)
    @staticmethod
    def _hash_node(left: bytes, right: bytes) -> bytes:
        return SM3.hash(b'\x01' + left + right)
    def build_tree(self, nodes: List[bytes]) -> List[List[bytes]]:
        tree = [nodes]
        while len(nodes) > 1:
            next_level = []
            for i in range(0, len(nodes), 2):
                left = nodes[i]
                right = nodes[i+1] if i+1 < len(nodes) else nodes[i]
                next_level.append(self._hash_node(left, right))
            tree.append(next_level)
            nodes = next_level
        return tree
    def get_proof(self, index: int) -> List[Tuple[bytes, bool]]:
        proof = []
        idx = index
        for layer in self.tree[:-1]:
            sibling_idx = idx + 1 if idx % 2 == 0 else idx - 1
            if sibling_idx < len(layer):
                proof.append((layer[sibling_idx], idx % 2 == 0))
            idx = idx // 2
        return proof
    def verify_proof(self, leaf: bytes, proof: List[Tuple[bytes, bool]]) -> bool:
        current = self._hash_leaf(leaf)
        for sibling, is_left in proof:
            current = self._hash_node(sibling, current) if is_left else self._hash_node(current, sibling)
        return current == self.root
if __name__ == "__main__":
    print("="*50)
    print("Task 1: SM3 Hash Test")
    print("="*50)
    test_msg = b"abc"
    expected_hash = "66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7c2299a02"
    h = SM3.hash(test_msg)
    print(f"Input: {test_msg}")
    print(f"SM3 hash: {h.hex()}")
    print(f"Expected: {expected_hash}...")
    print(f"Test {'passed' if h.hex().startswith(expected_hash) else 'failed'}")
    length_extension_attack()
    print("\n" + "="*50)
    print("Task 3: Merkle Tree Test (10 leaves)")
    print("="*50)
    data = [str(i).encode() for i in range(10)]
    tree = MerkleTree(data)
    print(f"Merkle root: {tree.root.hex()}")
    proof = tree.get_proof(3)
    print(f"\nProof for leaf 3: {[(h.hex()[:8]+'...', pos) for h, pos in proof]}")
    valid = tree.verify_proof(b"3", proof)
    print(f"Verification: {valid}")
    print("\nNon-membership test for '10':")
    found = any(tree.verify_proof(b"10", tree.get_proof(i)) for i in range(10))
    print(f"Leaf '10' {'exists' if found else 'does not exist'} in tree")