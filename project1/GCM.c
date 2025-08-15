#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#define ROTL(x, n) (((x) << (n)) | ((x) >> (32 - (n))))

const uint8_t SBOX[256] = {
    0xd6, 0x90, 0xe9, 0xfe, 0xcc, 0xe1, 0x3d, 0xb7, 0x16, 0xb6, 0x14, 0xc2, 0x28, 0xfb, 0x2c, 0x05,
    0x2b, 0x67, 0x9a, 0x76, 0x2a, 0xbe, 0x04, 0xc3, 0xaa, 0x44, 0x13, 0x26, 0x49, 0x86, 0x06, 0x99,
    0x9c, 0x42, 0x50, 0xf4, 0x91, 0xef, 0x98, 0x7a, 0x33, 0x54, 0x0b, 0x43, 0xed, 0xcf, 0xac, 0x62,
    0xe4, 0xb3, 0x1c, 0xa9, 0xc9, 0x08, 0xe8, 0x95, 0x80, 0xdf, 0x94, 0xfa, 0x75, 0x8f, 0x3f, 0xa6,
    0x47, 0x07, 0xa7, 0xfc, 0xf3, 0x73, 0x17, 0xba, 0x83, 0x59, 0x3c, 0x19, 0xe6, 0x85, 0x4f, 0xa8,
    0x68, 0x6b, 0x81, 0xb2, 0x71, 0x64, 0xda, 0x8b, 0xf8, 0xeb, 0x0f, 0x4b, 0x70, 0x56, 0x9d, 0x35,
    0x1e, 0x24, 0x0e, 0x5e, 0x63, 0x58, 0xd1, 0xa2, 0x25, 0x22, 0x7c, 0x3b, 0x01, 0x21, 0x78, 0x87,
    0xd4, 0x00, 0x46, 0x57, 0x9f, 0xd3, 0x27, 0x52, 0x4c, 0x36, 0x02, 0xe7, 0xa0, 0xc4, 0xc8, 0x9e,
    0xea, 0xbf, 0x8a, 0xd2, 0x40, 0xc7, 0x38, 0xb5, 0xa3, 0xf7, 0xf2, 0xce, 0xf9, 0x61, 0x15, 0xa1,
    0xe0, 0xae, 0x5d, 0xa4, 0x9b, 0x34, 0x1a, 0x55, 0xad, 0x93, 0x32, 0x30, 0xf5, 0x8c, 0xb1, 0xe3,
    0x1d, 0xf6, 0xe2, 0x2e, 0x82, 0x66, 0xca, 0x60, 0xc0, 0x29, 0x23, 0xab, 0x0d, 0x53, 0x4e, 0x6f,
    0xd5, 0xdb, 0x37, 0x45, 0xde, 0xfd, 0x8e, 0x2f, 0x03, 0xff, 0x6a, 0x72, 0x6d, 0x6c, 0x5b, 0x51,
    0x8d, 0x1b, 0xaf, 0x92, 0xbb, 0xdd, 0xbc, 0x7f, 0x11, 0xd9, 0x5c, 0x41, 0x1f, 0x10, 0x5a, 0xd8,
    0x0a, 0xc1, 0x31, 0x88, 0xa5, 0xcd, 0x7b, 0xbd, 0x2d, 0x74, 0xd0, 0x12, 0xb8, 0xe5, 0xb4, 0xb0,
    0x89, 0x69, 0x97, 0x4a, 0x0c, 0x96, 0x77, 0x7e, 0x65, 0xb9, 0xf1, 0x09, 0xc5, 0x6e, 0xc6, 0x84,
    0x18, 0xf0, 0x7d, 0xec, 0x3a, 0xdc, 0x4d, 0x20, 0x79, 0xee, 0x5f, 0x3e, 0xd7, 0xcb, 0x39, 0x48
};

static const uint32_t FK[4] = {0xa3b1bac6, 0x56aa3350, 0x677d9197, 0xb27022dc};
static const uint32_t CK[32] = {
    0x00070e15, 0x1c232a31, 0x383f464d, 0x545b6269,
    0x70777e85, 0x8c939aa1, 0xa8afb6bd, 0xc4cbd2d9,
    0xe0e7eef5, 0xfc030a11, 0x181f262d, 0x343b4249,
    0x50575e65, 0x6c737a81, 0x888f969d, 0xa4abb2b9,
    0xc0c7ced5, 0xdce3eaf1, 0xf8ff060d, 0x141b2229,
    0x30373e45, 0x4c535a61, 0x686f767d, 0x848b9299,
    0xa0a7aeb5, 0xbcc3cad1, 0xd8dfe6ed, 0xf4fb0209,
    0x10171e25, 0x2c333a41, 0x484f565d, 0x646b7279
};

static inline uint32_t load_u32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) | 
           ((uint32_t)p[2] << 8) | p[3];
}
static inline void store_u32(uint32_t v, uint8_t *p) {
    p[0] = v >> 24;
    p[1] = (v >> 16) & 0xFF;
    p[2] = (v >> 8) & 0xFF;
    p[3] = v & 0xFF;
}
uint32_t L_transform(uint32_t x) {
    return x ^ ROTL(x, 2) ^ ROTL(x, 10) ^ ROTL(x, 18) ^ ROTL(x, 24);
}
uint32_t F(uint32_t x, uint32_t rk) {
    uint32_t t = x ^ rk;
    uint32_t s = (SBOX[t >> 24] << 24) | (SBOX[(t >> 16) & 0xFF] << 16) | 
                 (SBOX[(t >> 8) & 0xFF] << 8) | SBOX[t & 0xFF];
    return L_transform(s);
}
void sm4_key_schedule(uint32_t *rk, const uint8_t *key) {
    uint32_t K[4];
    for (int i = 0; i < 4; i++) {
        K[i] = load_u32(key + i * 4) ^ FK[i];
    }
    for (int i = 0; i < 32; i++) {
        uint32_t t = K[(i+1)%4] ^ K[(i+2)%4] ^ K[(i+3)%4] ^ CK[i];
        uint32_t s = (SBOX[t >> 24] << 24) | (SBOX[(t >> 16) & 0xFF] << 16) | 
                     (SBOX[(t >> 8) & 0xFF] << 8) | SBOX[t & 0xFF];
        rk[i] = K[i%4] ^ (s ^ ROTL(s, 13) ^ ROTL(s, 23));
        K[i%4] = rk[i];
    }
}
void sm4_encrypt(const uint32_t *rk, const uint8_t *input, uint8_t *output) {
    uint32_t state[4];
    for (int i = 0; i < 4; i++) {
        state[i] = load_u32(input + i * 4);
    }
    for (int i = 0; i < 32; i++) {
        uint32_t tmp = F(state[1] ^ state[2] ^ state[3] ^ rk[i], state[0]);
        state[0] = state[1];
        state[1] = state[2];
        state[2] = state[3];
        state[3] = tmp;
    }
    for (int i = 0; i < 4; i++) {
        store_u32(state[3-i], output + i * 4);
    }
}
#define GCM_IV_SIZE     12
#define GCM_TAG_SIZE    16
void gf_multiply(const uint8_t *x, const uint8_t *y, uint8_t *z) {
    uint8_t v[16];
    uint8_t tmp;
    memset(z, 0, 16);
    memcpy(v, y, 16);
    for (int i = 0; i < 16; i++) {
        for (int j = 7; j >= 0; j--) {
            if ((x[i] >> j) & 1) {
                for (int k = 0; k < 16; k++) {
                    z[k] ^= v[k];
                }
            }
            tmp = v[15] & 0x01;
            for (int k = 15; k > 0; k--) {
                v[k] = (v[k] >> 1) | ((v[k-1] & 0x01) << 7);
            }
            v[0] >>= 1;
            if (tmp) {
                v[0] ^= 0xE1;
            }
        }
    }
}
void gcm_init_H(uint8_t *H, const uint32_t *rk) {
    uint8_t zero_block[16] = {0};
    sm4_encrypt(rk, zero_block, H);
}
void gcm_ghash(uint8_t *Y, const uint8_t *H, const uint8_t *data, size_t len) {
    uint8_t temp[16];
    for (size_t i = 0; i < len; i += 16) {
        for (int j = 0; j < 16 && (i+j) < len; j++) {
            Y[j] ^= data[i+j];
        }
        gf_multiply(Y, H, temp);
        memcpy(Y, temp, 16);
    }
}
void sm4_gcm_encrypt(
    const uint32_t *rk, 
    const uint8_t *iv,
    const uint8_t *aad,
    size_t aad_len,
    const uint8_t *plain,
    uint8_t *cipher,
    size_t len,
    uint8_t *tag
) {
    uint8_t H[16], J0[16], Y[16] = {0};
    gcm_init_H(H, rk);
    memset(J0, 0, 16);
    memcpy(J0, iv, GCM_IV_SIZE);
    J0[15] = 1;
    if (aad_len > 0) {
        gcm_ghash(Y, H, aad, aad_len);
    }
    uint8_t counter[16];
    memcpy(counter, J0, 16);
    counter[15]++;
    for (size_t i = 0; i < len; i += 16) {
        uint8_t keystream[16];
        sm4_encrypt(rk, counter, keystream);
        size_t block_len = (len - i) > 16 ? 16 : (len - i);
        for (size_t j = 0; j < block_len; j++) {
            cipher[i + j] = plain[i + j] ^ keystream[j];
        }
        for (int j = 15; j >= 0; j--) {
            if (++counter[j] != 0) break;
        }
    }
    gcm_ghash(Y, H, cipher, len);
    uint8_t len_block[16] = {0};
    for (int i = 0; i < 8; i++) {
        len_block[15-i] = (aad_len * 8) >> (i * 8);
        len_block[7-i] = (len * 8) >> (i * 8);
    }
    for (int i = 0; i < 16; i++) {
        Y[i] ^= len_block[i];
    }
    gf_multiply(Y, H, Y);
    uint8_t tag_key[16];
    sm4_encrypt(rk, J0, tag_key);
    for (int i = 0; i < 16; i++) {
        tag[i] = Y[i] ^ tag_key[i];
    }
}
void test_sm4_gcm() {
    uint8_t key[16] = {0x01,0x23,0x45,0x67,0x89,0xab,0xcd,0xef,0xfe,0xdc,0xba,0x98,0x76,0x54,0x32,0x10};
    uint8_t iv[GCM_IV_SIZE] = {0x00,0x11,0x22,0x33,0x44,0x55,0x66,0x77,0x88,0x99,0xaa,0xbb};
    uint8_t aad[] = {0xde,0xad,0xbe,0xef};
    uint8_t plain[1024], cipher[1024], decrypted[1024], tag[GCM_TAG_SIZE];
    uint32_t rk[32];
    
    // 填充测试数据
    for (size_t i = 0; i < sizeof(plain); i++) {
        plain[i] = i % 256;
    }
    
    // 生成轮密钥
    sm4_key_schedule(rk, key);
    
    // 测试加密
    clock_t start = clock();
    const int ITERATIONS = 1000;
    for (int i = 0; i < ITERATIONS; i++) {
        sm4_gcm_encrypt(rk, iv, aad, sizeof(aad), plain, cipher, sizeof(plain), tag);
    }
    clock_t end = clock();
    double time = (double)(end - start) / CLOCKS_PER_SEC;
    printf("Encryption Speed: %.2f MB/s\n", (ITERATIONS * sizeof(plain)) / time / 1000000);
    
    // 验证解密
    sm4_gcm_encrypt(rk, iv, aad, sizeof(aad), cipher, decrypted, sizeof(plain), tag);
    
    if (memcmp(plain, decrypted, sizeof(plain))) {
        printf("Decryption FAILED!\n");
    } else {
        printf("Decryption Verified\n");
    }
}

int main() {
    printf("=== SM4-GCM Test ===\n");
    test_sm4_gcm();
    return 0;
}