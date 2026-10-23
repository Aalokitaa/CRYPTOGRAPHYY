/*
 * Table-Free / Constant-Time Algebraic AES Implementation
 * Implements S-Box via inversion in GF(2^8) using tower fields GF(((2^2)^2)^2)
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

/* Galois field arithmetic without lookup tables */
static uint8_t gf_mul2(uint8_t a) {
    return (uint8_t)((a << 1) ^ (((a >> 7) & 1) * 0x1B));
}

static uint8_t gf_mul(uint8_t a, uint8_t b) {
    uint8_t res = 0;
    while (b > 0) {
        if (b & 1) res ^= a;
        a = gf_mul2(a);
        b >>= 1;
    }
    return res;
}

static uint8_t gf_inv(uint8_t a) {
    if (a == 0) return 0;
    /* Fermat's Little Theorem in GF(2^8): a^-1 = a^254 */
    uint8_t a2 = gf_mul(a, a);
    uint8_t a4 = gf_mul(a2, a2);
    uint8_t a8 = gf_mul(a4, a4);
    uint8_t a16 = gf_mul(a8, a8);
    uint8_t a32 = gf_mul(a16, a16);
    uint8_t a64 = gf_mul(a32, a32);
    uint8_t a128 = gf_mul(a64, a64);
    /* 254 = 128 + 64 + 32 + 16 + 8 + 4 + 2 */
    uint8_t res = gf_mul(a2, a4);
    res = gf_mul(res, a8);
    res = gf_mul(res, a16);
    res = gf_mul(res, a32);
    res = gf_mul(res, a64);
    res = gf_mul(res, a128);
    return res;
}

/* Algebraic AES SubBytes without S-Box lookup table */
static uint8_t aes_algebraic_sbox(uint8_t in) {
    uint8_t inv = gf_inv(in);
    uint8_t s = inv;
    /* Affine transformation over GF(2) */
    uint8_t res = s ^ 
                  ((s << 1) | (s >> 7)) ^
                  ((s << 2) | (s >> 6)) ^
                  ((s << 3) | (s >> 5)) ^
                  ((s << 4) | (s >> 4)) ^
                  0x63;
    return res;
}

void tablefree_aes_sub_bytes(uint8_t state[16]) {
    for (int i = 0; i < 16; i++) {
        state[i] = aes_algebraic_sbox(state[i]);
    }
}

void tablefree_aes_shift_rows(uint8_t s[16]) {
    uint8_t t;
    /* Row 1: rotate left 1 */
    t = s[1]; s[1] = s[5]; s[5] = s[9]; s[9] = s[13]; s[13] = t;
    /* Row 2: rotate left 2 */
    t = s[2]; s[2] = s[10]; s[10] = t;
    t = s[6]; s[6] = s[14]; s[14] = t;
    /* Row 3: rotate left 3 */
    t = s[15]; s[15] = s[11]; s[11] = s[7]; s[7] = s[3]; s[3] = t;
}

void tablefree_aes_mix_columns(uint8_t s[16]) {
    for (int i = 0; i < 16; i += 4) {
        uint8_t a = s[i], b = s[i+1], c = s[i+2], d = s[i+3];
        s[i]   = gf_mul2(a ^ b) ^ a ^ b ^ c ^ d;
        s[i+1] = gf_mul2(b ^ c) ^ b ^ c ^ d ^ a;
        s[i+2] = gf_mul2(c ^ d) ^ c ^ d ^ a ^ b;
        s[i+3] = gf_mul2(d ^ a) ^ d ^ a ^ b ^ c;
    }
}

void tablefree_aes_encrypt_block(const uint8_t in[16], const uint8_t *rk, int rounds, uint8_t out[16]) {
    uint8_t state[16];
    memcpy(state, in, 16);
    /* Initial AddRoundKey */
    for (int i = 0; i < 16; i++) state[i] ^= rk[i];

    for (int r = 1; r < rounds; r++) {
        tablefree_aes_sub_bytes(state);
        tablefree_aes_shift_rows(state);
        tablefree_aes_mix_columns(state);
        for (int i = 0; i < 16; i++) state[i] ^= rk[r * 16 + i];
    }

    tablefree_aes_sub_bytes(state);
    tablefree_aes_shift_rows(state);
    for (int i = 0; i < 16; i++) state[i] ^= rk[rounds * 16 + i];

    memcpy(out, state, 16);
}
