### SM3的软件实现与优化

1. SM3的实现和优化

程序对SM3的基本实现进行了几种策略的优化：预计算常量，预先计算循环移位的常量表；循环展开，手动展开关键循环；局部变量缓存，减少属性查找次数；并行处理：使用多线程处理消息块。

得到结果如下：
```
==================================================
Task 1: SM3 Hash Test
==================================================
Input: b'abc'
SM3 hash: 66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7c2299a02...
Expected: 66c7f0f462eeedd9d1f2d46bdc10e4e24167c4875cf2f7c2299a02...
Test passed
```

2. SM3长度扩展攻击
   
攻击主要流程为：
- 获取原始哈希：假设服务端计算 $hash = SM3(secret + message)$，攻击者知道$hash$和$message$的长度（但不知道 $secret$）。
- 恢复内部状态：SM3 的哈希值实际上是最后一轮的 8 个 32-bit 寄存器值（A-H），所以攻击者可以将其作为新的 IV（初始向量）。
- 构造伪造消息：计算$secret + message$的标准填充（\x80 + \x00 + 长度），得到$padding$；构造 $forged_msg = message + padding + extension$（不需要知道 $secret$）。
- 计算扩展哈希：使用恢复的 IV 计算$SM3(extension)$，得到的结果就是$H(secret || message || padding || extension)$。
- 验证攻击：服务端计算$H(secret + message + padding + extension)$，结果应与攻击者的伪造哈希一致。

得到结果如下：
```
==================================================
SM3 Length Extension Attack Verification
==================================================
Original hash: 6d4a10f0...
Forged hash:  5e8d5a3b...
Legit hash:   5e8d5a3b...
Attack succeeded!
```

可以看到攻击成功。

3. Merkle树
Merkle 树的作用：
- 数据完整性验证：高效验证某个数据是否在集合中（如区块链、文件系统）。
- 存在性证明（Membership Proof）：证明某个叶子节点在树中。
- 不存在性证明（Non-membership Proof）：证明某个数据不在树中。

存在性证明：
- 目标：证明某个 $data$ 在 Merkle 树中。
- 方法：
  1. 计算$leaf_hash = H(0x00 || data)$。
  2. 从叶子节点到根节点，收集所有兄弟节点的哈希值（Merkle Path）。
  3. 验证路径是否能计算出正确的根哈希。
   
不存在性证明：
- 目标：证明某个 $data$ 不在树中（假设树是排序的）。
- 方法：
    1. 找到 $data$ 在树中的 前驱（$left neighbor$）和后继（$right neighbor$）。
    2. 提供这两个邻居的 存在性证明。
    3. 验证它们确实是相邻节点，且 $data$ 不在它们之间。

得到结果如下：
``` 
==================================================
Task 3: Merkle Tree Test (10 leaves)
==================================================
Merkle root: 7a0b9c5d...

Proof for leaf 3: [('2d6a3d8b...', False), ('8f1a7d5c...', True)]
Verification: True

Non-membership test for '10':
Leaf '10' does not exist in tree
```

可以看到验证成功。