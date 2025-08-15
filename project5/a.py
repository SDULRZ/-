import time
import random
import hashlib
from typing import Tuple, List
from multiprocessing import Pool
P = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
A = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
B = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
Gx = 0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7
Gy = 0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0
N = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
class Point:
    def __init__(self, x, y, infinity=False):
        self.x = x
        self.y = y
        self.infinity = infinity
    def __eq__(self, other):
        if self.infinity and other.infinity:
            return True
        return self.x == other.x and self.y == other.y and self.infinity == other.infinity
    def __repr__(self):
        return f"Point({hex(self.x)}, {hex(self.y)})" if not self.infinity else "Point(INF)"
def point_add(p: Point, q: Point) -> Point:
    if p.infinity:
        return q
    if q.infinity:
        return p
    if p.x == q.x and p.y == q.y:
        return point_double(p)
    if p.x == q.x:
        return Point(0, 0, True) 
    lam = (q.y - p.y) * inv(q.x - p.x) % P
    x3 = (lam * lam - p.x - q.x) % P
    y3 = (lam * (p.x - x3) - p.y) % P
    return Point(x3, y3)
def point_double(p: Point) -> Point:
    if p.infinity:
        return p
    lam = (3 * p.x * p.x + A) * inv(2 * p.y) % P
    x3 = (lam * lam - 2 * p.x) % P
    y3 = (lam * (p.x - x3) - p.y) % P
    return Point(x3, y3)
def inv(a: int) -> int:
    return pow(a, P-2, P) if a != 0 else 0
def scalar_mul(point: Point, scalar: int) -> Point:
    if scalar == 0 or point.infinity:
        return Point(0, 0, True)
    result = Point(0, 0, True)
    addend = point
    while scalar > 0:
        if scalar & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        scalar >>= 1
    return result
class SM2:
    def __init__(self, enable_optimizations=True):
        self.enable_optimizations = enable_optimizations
        self.G = Point(Gx, Gy)
        self.n = N
        self.private_key = random.randint(1, self.n-1)
        self.public_key = scalar_mul(self.G, self.private_key)
        if enable_optimizations:
            self._precompute_table = self._precompute_fixed_base()
    def _precompute_fixed_base(self):
        table = {}
        window_size = 4
        max_val = 1 << window_size
        for i in range(max_val):
            table[i] = scalar_mul(self.G, i)
        return table
    def _scalar_mul_optimized(self, point: Point, scalar: int) -> Point:
        if scalar == 0 or point.infinity:
            return Point(0, 0, True) 
        window_size = 4
        result = Point(0, 0, True)
        scalar_bits = bin(scalar)[2:]
        for i in range(0, len(scalar_bits), window_size):
            chunk = scalar_bits[i:i+window_size]
            if not chunk:
                continue
            idx = int(chunk, 2)
            if not result.infinity:
                for _ in range(len(chunk)):
                    result = point_double(result)
                result = point_add(result, self._precompute_table[idx])
            else:
                result = self._precompute_table[idx] 
        return result
    def sign(self, data: bytes, k: int = None) -> Tuple[int, int]:
        e = self._hash(data)
        if k is None:
            k = random.randint(1, self.n-1)
        point = self._scalar_mul_optimized(self.G, k) if self.enable_optimizations else scalar_mul(self.G, k)
        x1 = point.x % self.n
        r = (e + x1) % self.n
        if r == 0 or r + k == self.n:
            return self.sign(data)
        s = (inv(1 + self.private_key) * (k - r * self.private_key)) % self.n
        if s == 0:
            return self.sign(data)
        return (r, s)
    def verify(self, data: bytes, signature: Tuple[int, int]) -> bool:
        r, s = signature
        if not (1 <= r < self.n and 1 <= s < self.n):
            return False
        e = self._hash(data)
        t = (r + s) % self.n
        if t == 0:
            return False
        sG = self._scalar_mul_optimized(self.G, s) if self.enable_optimizations else scalar_mul(self.G, s)
        tP = self._scalar_mul_optimized(self.public_key, t) if self.enable_optimizations else scalar_mul(self.public_key, t)
        point = point_add(sG, tP)
        if point.infinity:
            return False
        x1 = point.x % self.n
        return (r % self.n) == ((e + x1) % self.n)
    def _hash(self, data: bytes) -> int:
        return int.from_bytes(hashlib.sha256(data).digest(), 'big') % self.n
def verify_wrapper(args):
    data, signature, public_key_params, enable_opt = args
    public_key = Point(public_key_params[0], public_key_params[1])
    verifier = SM2(enable_optimizations=enable_opt)
    verifier.public_key = public_key
    return verifier.verify(data, signature)
def performance_test():
    test_results = []
    for opt in [False, True]:
        print(f"\n{'='*30}")
        print(f"测试模式: {'优化开启' if opt else '基础实现'}")
        sm2 = SM2(enable_optimizations=opt)
        data = b"Test data for SM2 performance"
        start = time.time()
        signatures = [sm2.sign(data) for _ in range(100)]
        sign_time = (time.time() - start)/100
        print(f"签名平均耗时: {sign_time*1000:.2f}ms")
        sig = signatures[0]
        start = time.time()
        for _ in range(100):
            sm2.verify(data, sig)
        verify_time = (time.time() - start)/100
        print(f"验证平均耗时: {verify_time*1000:.2f}ms")
        verify_args = [(data, sig, (sm2.public_key.x, sm2.public_key.y), opt) for sig in signatures]
        start = time.time()
        with Pool(processes=4) as pool:
            batch_results = pool.map(verify_wrapper, verify_args)
        batch_time = time.time() - start
        print(f"批量验证100个签名耗时: {batch_time*1000:.2f}ms (结果: {all(batch_results)})")
        test_results.append({
            'mode': 'optimized' if opt else 'baseline',
            'sign_time': sign_time,
            'verify_time': verify_time,
            'batch_time': batch_time
        })
    print("\n性能对比:")
    print(f"签名速度提升: {test_results[0]['sign_time']/test_results[1]['sign_time']:.1f}x")
    print(f"验证速度提升: {test_results[0]['verify_time']/test_results[1]['verify_time']:.1f}x")
    print(f"批量验证速度提升: {test_results[0]['batch_time']/test_results[1]['batch_time']:.1f}x")
if __name__ == "__main__":
    performance_test()