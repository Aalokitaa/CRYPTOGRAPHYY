/*
 * mbedTLS-style 32-bit T-Table AES implementation
 * License: Apache-2.0 / MIT Dual License
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

#define ROTL8(x) (((x) << 8) | ((x) >> 24))
#define ROTL16(x) (((x) << 16) | ((x) >> 16))
#define ROTL24(x) (((x) << 24) | ((x) >> 8))

static const uint32_t RCON_32[10] = {
    0x01000000, 0x02000000, 0x04000000, 0x08000000,
    0x10000000, 0x20000000, 0x40000000, 0x80000000,
    0x1B000000, 0x36000000
};

static const uint8_t FSb[256] = {
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16
};

typedef struct {
    int nr;
    uint32_t rk[64];
} mbedtls_aes_context;

static uint32_t aes_sub_word(uint32_t w) {
    return ((uint32_t)FSb[(w >> 24) & 0xFF] << 24) |
           ((uint32_t)FSb[(w >> 16) & 0xFF] << 16) |
           ((uint32_t)FSb[(w >>  8) & 0xFF] <<  8) |
           ((uint32_t)FSb[(w      ) & 0xFF]      );
}

int mbedtls_aes_setkey_enc(mbedtls_aes_context *ctx, const uint8_t *key, unsigned int keybits) {
    unsigned int i;
    uint32_t *RK = ctx->rk;

    if (keybits == 128) {
        ctx->nr = 10;
        for (i = 0; i < 4; i++) {
            RK[i] = ((uint32_t)key[4 * i] << 24) |
                    ((uint32_t)key[4 * i + 1] << 16) |
                    ((uint32_t)key[4 * i + 2] << 8) |
                    ((uint32_t)key[4 * i + 3]);
        }
        for (i = 0; i < 10; i++) {
            RK[4] = RK[0] ^ RCON_32[i] ^ aes_sub_word(ROTL24(RK[3]));
            RK[5] = RK[1] ^ RK[4];
            RK[6] = RK[2] ^ RK[5];
            RK[7] = RK[3] ^ RK[6];
            RK += 4;
        }
    } else if (keybits == 256) {
        ctx->nr = 14;
        for (i = 0; i < 8; i++) {
            RK[i] = ((uint32_t)key[4 * i] << 24) |
                    ((uint32_t)key[4 * i + 1] << 16) |
                    ((uint32_t)key[4 * i + 2] << 8) |
                    ((uint32_t)key[4 * i + 3]);
        }
        for (i = 0; i < 7; i++) {
            RK[8]  = RK[0] ^ RCON_32[i] ^ aes_sub_word(ROTL24(RK[7]));
            RK[9]  = RK[1] ^ RK[8];
            RK[10] = RK[2] ^ RK[9];
            RK[11] = RK[3] ^ RK[10];
            if (i == 6) break;
            RK[12] = RK[4] ^ aes_sub_word(RK[11]);
            RK[13] = RK[5] ^ RK[12];
            RK[14] = RK[6] ^ RK[13];
            RK[15] = RK[7] ^ RK[14];
            RK += 8;
        }
    }
    return 0;
}

static uint32_t aes_ft_transform(uint8_t a, uint8_t b, uint8_t c, uint8_t d) {
    uint8_t fa = FSb[a];
    uint8_t fb = FSb[b];
    uint8_t fc = FSb[c];
    uint8_t fd = FSb[d];
    uint8_t xta = (fa << 1) ^ (((fa >> 7) & 1) * 0x1b);
    uint8_t xtb = (fb << 1) ^ (((fb >> 7) & 1) * 0x1b);
    uint8_t xtc = (fc << 1) ^ (((fc >> 7) & 1) * 0x1b);
    uint8_t xtd = (fd << 1) ^ (((fd >> 7) & 1) * 0x1b);

    uint8_t r0 = xta ^ fb ^ xtb ^ fc ^ fd;
    uint8_t r1 = fa ^ xtb ^ fc ^ xtc ^ fd;
    uint8_t r2 = fa ^ fb ^ xtc ^ fd ^ xtd;
    uint8_t r3 = fa ^ xta ^ fb ^ fc ^ xtd;

    return ((uint32_t)r0 << 24) | ((uint32_t)r1 << 16) | ((uint32_t)r2 << 8) | (uint32_t)r3;
}

int mbedtls_aes_crypt_ecb(mbedtls_aes_context *ctx, const uint8_t input[16], uint8_t output[16]) {
    int i;
    uint32_t *RK = ctx->rk;
    uint32_t X0, X1, X2, X3, Y0, Y1, Y2, Y3;

    X0 = ((uint32_t)input[0] << 24) | ((uint32_t)input[1] << 16) | ((uint32_t)input[2] << 8) | input[3];
    X1 = ((uint32_t)input[4] << 24) | ((uint32_t)input[5] << 16) | ((uint32_t)input[6] << 8) | input[7];
    X2 = ((uint32_t)input[8] << 24) | ((uint32_t)input[9] << 16) | ((uint32_t)input[10] << 8) | input[11];
    X3 = ((uint32_t)input[12] << 24) | ((uint32_t)input[13] << 16) | ((uint32_t)input[14] << 8) | input[15];

    X0 ^= *RK++; X1 ^= *RK++; X2 ^= *RK++; X3 ^= *RK++;

    for (i = (ctx->nr >> 1) - 1; i > 0; i--) {
        Y0 = *RK++ ^ aes_ft_transform((uint8_t)(X0 >> 24), (uint8_t)(X1 >> 16), (uint8_t)(X2 >> 8), (uint8_t)X3);
        Y1 = *RK++ ^ aes_ft_transform((uint8_t)(X1 >> 24), (uint8_t)(X2 >> 16), (uint8_t)(X3 >> 8), (uint8_t)X0);
        Y2 = *RK++ ^ aes_ft_transform((uint8_t)(X2 >> 24), (uint8_t)(X3 >> 16), (uint8_t)(X0 >> 8), (uint8_t)X1);
        Y3 = *RK++ ^ aes_ft_transform((uint8_t)(X3 >> 24), (uint8_t)(X0 >> 16), (uint8_t)(X1 >> 8), (uint8_t)X2);

        X0 = *RK++ ^ aes_ft_transform((uint8_t)(Y0 >> 24), (uint8_t)(Y1 >> 16), (uint8_t)(Y2 >> 8), (uint8_t)Y3);
        X1 = *RK++ ^ aes_ft_transform((uint8_t)(Y1 >> 24), (uint8_t)(Y2 >> 16), (uint8_t)(Y3 >> 8), (uint8_t)Y0);
        X2 = *RK++ ^ aes_ft_transform((uint8_t)(Y2 >> 24), (uint8_t)(Y3 >> 16), (uint8_t)(Y0 >> 8), (uint8_t)Y1);
        X3 = *RK++ ^ aes_ft_transform((uint8_t)(Y3 >> 24), (uint8_t)(Y0 >> 16), (uint8_t)(Y1 >> 8), (uint8_t)Y2);
    }

    Y0 = *RK++ ^ aes_ft_transform((uint8_t)(X0 >> 24), (uint8_t)(X1 >> 16), (uint8_t)(X2 >> 8), (uint8_t)X3);
    Y1 = *RK++ ^ aes_ft_transform((uint8_t)(X1 >> 24), (uint8_t)(X2 >> 16), (uint8_t)(X3 >> 8), (uint8_t)X0);
    Y2 = *RK++ ^ aes_ft_transform((uint8_t)(X2 >> 24), (uint8_t)(X3 >> 16), (uint8_t)(X0 >> 8), (uint8_t)X1);
    Y3 = *RK++ ^ aes_ft_transform((uint8_t)(X3 >> 24), (uint8_t)(X0 >> 16), (uint8_t)(X1 >> 8), (uint8_t)X2);

    output[0]  = (uint8_t)(FSb[(Y0 >> 24) & 0xFF]) ^ (uint8_t)(*RK >> 24);
    output[1]  = (uint8_t)(FSb[(Y1 >> 16) & 0xFF]) ^ (uint8_t)(*RK >> 16);
    output[2]  = (uint8_t)(FSb[(Y2 >>  8) & 0xFF]) ^ (uint8_t)(*RK >>  8);
    output[3]  = (uint8_t)(FSb[(Y3      ) & 0xFF]) ^ (uint8_t)(*RK++);
    output[4]  = (uint8_t)(FSb[(Y1 >> 24) & 0xFF]) ^ (uint8_t)(*RK >> 24);
    output[5]  = (uint8_t)(FSb[(Y2 >> 16) & 0xFF]) ^ (uint8_t)(*RK >> 16);
    output[6]  = (uint8_t)(FSb[(Y3 >>  8) & 0xFF]) ^ (uint8_t)(*RK >>  8);
    output[7]  = (uint8_t)(FSb[(Y0      ) & 0xFF]) ^ (uint8_t)(*RK++);
    output[8]  = (uint8_t)(FSb[(Y2 >> 24) & 0xFF]) ^ (uint8_t)(*RK >> 24);
    output[9]  = (uint8_t)(FSb[(Y3 >> 16) & 0xFF]) ^ (uint8_t)(*RK >> 16);
    output[10] = (uint8_t)(FSb[(Y0 >>  8) & 0xFF]) ^ (uint8_t)(*RK >>  8);
    output[11] = (uint8_t)(FSb[(Y1      ) & 0xFF]) ^ (uint8_t)(*RK++);
    output[12] = (uint8_t)(FSb[(Y3 >> 24) & 0xFF]) ^ (uint8_t)(*RK >> 24);
    output[13] = (uint8_t)(FSb[(Y0 >> 16) & 0xFF]) ^ (uint8_t)(*RK >> 16);
    output[14] = (uint8_t)(FSb[(Y1 >>  8) & 0xFF]) ^ (uint8_t)(*RK >>  8);
    output[15] = (uint8_t)(FSb[(Y2      ) & 0xFF]) ^ (uint8_t)(*RK++);

    return 0;
}
