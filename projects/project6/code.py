import hashlib
import random
from typing import List, Tuple
def generate_large_prime(bits):
    def is_prime(n):
        if n < 2: return False
        for p in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
            if n % p == 0: return n == p
        d = n - 1
        s = 0
        while d % 2 == 0:
            d //= 2
            s += 1
        for a in [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]:
            if a >= n: continue
            x = pow(a, d, n)
            if x == 1 or x == n - 1: continue
            for _ in range(s - 1):
                x = pow(x, 2, n)
                if x == n - 1: break
            else:
                return False
        return True
    while True:
        p = random.getrandbits(bits)
        if p > 2 and is_prime(p):
            return p
class SimpleHomomorphicEncryption:
    def __init__(self, key_size=64):
        self.p = generate_large_prime(key_size)
        self.g = self.p + 1
    def encrypt(self, m):
        r = random.randint(1, self.p-1)
        return (pow(self.g, m, self.p**2) * pow(r, self.p, self.p**2)) % self.p**2
    def decrypt(self, c):
        L = lambda x: (x - 1) // self.p
        return (L(pow(c, self.p-1, self.p**2)) * pow(L(pow(self.g, self.p-1, self.p**2)), -1, self.p) % self.p)
    def add(self, c1, c2):
        return (c1 * c2) % self.p**2
    def add_scalar(self, c, s):
        return (c * pow(self.g, s, self.p**2)) % self.p**2
class PrivateIntersectionSum:
    def __init__(self, group_size=128):
        self.p = generate_large_prime(group_size)
        self.g = 2
    def _hash_to_group(self, x):
        h = hashlib.sha256(x.encode()).digest()
        return pow(self.g, int.from_bytes(h, 'big') % (self.p-1), self.p)
    def execute_protocol(self, party1_items, party2_data):
        k1 = random.randint(1, self.p-2)
        hashed_p1 = [self._hash_to_group(v) for v in party1_items]
        p1_to_p2 = [pow(h, k1, self.p) for h in hashed_p1]
        ahe = SimpleHomomorphicEncryption()
        k2 = random.randint(1, self.p-2)
        hashed_p2 = [self._hash_to_group(w) for w, _ in party2_data]
        p2_hashed = [pow(h, k2, self.p) for h in hashed_p2]
        p2_encrypted = [ahe.encrypt(t) for _, t in party2_data]
        combined = list(zip(p2_hashed, p2_encrypted))
        random.shuffle(combined)
        shuffled_hashes, shuffled_enc = zip(*combined)
        p1_hashed = [pow(h, k1, self.p) for h in shuffled_hashes]
        masks = [random.randint(0, 1000) for _ in shuffled_enc]
        masked_enc = [ahe.add_scalar(enc, m) for enc, m in zip(shuffled_enc, masks)]
        p1_final_hashes = [pow(pow(self._hash_to_group(v), k1, self.p), k2, self.p) 
                          for v in party1_items]
        intersection = set(p1_hashed) & set(p1_final_hashes)
        sum_ct = ahe.encrypt(0)
        for h, enc in zip(p1_hashed, masked_enc):
            if h in intersection:
                sum_ct = ahe.add(sum_ct, enc)
        masked_sum = ahe.decrypt(sum_ct)
        total_mask = sum(m for h, m in zip(p1_hashed, masks) if h in intersection)
        true_sum = masked_sum - total_mask
        return len(intersection), true_sum
if __name__ == "__main__":
    protocol = PrivateIntersectionSum()
    party1_data = ["user1", "user2", "user3", "user5"]
    party2_data = [("user1", 100), ("user2", 200), ("user3", 150), ("user4", 300)]
    size, total = protocol.execute_protocol(party1_data, party2_data)
    print(f"交集大小: {size}")
    print(f"关联值总和: {total}")
    print("实际交集:", set(party1_data) & set(w[0] for w in party2_data))