### circom实现poseidon2哈希算法

Poseidon2是一种ZK-friendly的哈希算法，专为零知识证明优化，其核心特点包括：

- 基于置换-置换网络（SPN）：通过多轮非线性变换（S-box）和线性混合（MDS 矩阵）实现扩散。

- 低复杂度：在算术电路中只需少量乘法门（主要依赖域上的加法和$x^5$操作）。

- 参数化设计：可调整轮数（$R_F$ 完整轮 + $R_P$ 部分轮）和状态大小（$t$）。

在input.json中配置好输入，然后会在public.json中输出响应的哈希结果，verification_key.json是Groth16证明系统的核心验证密钥，用于验证零知识证明的正确性。

得到运行结果：
```
[INFO] snarkJS: Curve: bn-128
[INFO] snarkJS: # of Wires: 2548
[INFO] snarkJS: # of Constraints: 2548
[INFO] snarkJS: # of Private Inputs: 2
[INFO] snarkJS: # of Public Inputs: 1
[INFO] snarkJS: # of Labels: 5096
[INFO] snarkJS: # of Outputs: 1
[INFO] snarkJS: OK!
```

可以看到运行正常。