/*
 * RSA Multi-Precision Modular Exponentiation (Bignum Modexp)
 * License: Public Domain / MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

#define BN_WORDS 32 /* 1024-bit or 2048-bit bignum */

typedef struct {
    uint32_t d[BN_WORDS];
    int len;
} bignum_t;

void bn_init(bignum_t *a) {
    memset(a->d, 0, sizeof(a->d));
    a->len = 0;
}

int bn_cmp(const bignum_t *a, const bignum_t *b) {
    for (int i = BN_WORDS - 1; i >= 0; i--) {
        if (a->d[i] > b->d[i]) return 1;
        if (a->d[i] < b->d[i]) return -1;
    }
    return 0;
}

/* Multi-precision addition with carry */
uint32_t bn_add(bignum_t *res, const bignum_t *a, const bignum_t *b) {
    uint64_t carry = 0;
    for (int i = 0; i < BN_WORDS; i++) {
        uint64_t sum = (uint64_t)a->d[i] + b->d[i] + carry;
        res->d[i] = (uint32_t)sum;
        carry = sum >> 32;
    }
    return (uint32_t)carry;
}

/* Multi-precision subtraction with borrow */
uint32_t bn_sub(bignum_t *res, const bignum_t *a, const bignum_t *b) {
    int64_t borrow = 0;
    for (int i = 0; i < BN_WORDS; i++) {
        int64_t diff = (int64_t)a->d[i] - b->d[i] - borrow;
        if (diff < 0) {
            diff += 0x100000000ULL;
            borrow = 1;
        } else {
            borrow = 0;
        }
        res->d[i] = (uint32_t)diff;
    }
    return (uint32_t)borrow;
}

/* Multi-precision multiply-accumulate */
void bn_mul(bignum_t *res, const bignum_t *a, const bignum_t *b) {
    uint32_t tmp[BN_WORDS * 2] = {0};
    for (int i = 0; i < BN_WORDS / 2; i++) {
        uint64_t carry = 0;
        for (int j = 0; j < BN_WORDS / 2; j++) {
            uint64_t prod = (uint64_t)a->d[i] * b->d[j] + tmp[i + j] + carry;
            tmp[i + j] = (uint32_t)prod;
            carry = prod >> 32;
        }
        tmp[i + BN_WORDS / 2] += (uint32_t)carry;
    }
    memcpy(res->d, tmp, BN_WORDS * sizeof(uint32_t));
}

/* Montgomery reduction or simple modular reduction */
void bn_mod(bignum_t *res, const bignum_t *a, const bignum_t *m) {
    bignum_t cur;
    memcpy(&cur, a, sizeof(bignum_t));
    while (bn_cmp(&cur, m) >= 0) {
        bn_sub(&cur, &cur, m);
    }
    memcpy(res, &cur, sizeof(bignum_t));
}

/* Modular exponentiation: res = base^exp mod modulus (Square-and-Multiply) */
void rsa_mod_exp(bignum_t *res, const bignum_t *base, const bignum_t *exp, const bignum_t *modulus) {
    bignum_t r;
    bn_init(&r);
    r.d[0] = 1;

    bignum_t b;
    bn_mod(&b, base, modulus);

    for (int i = BN_WORDS - 1; i >= 0; i--) {
        uint32_t w = exp->d[i];
        for (int bit = 31; bit >= 0; bit--) {
            /* Square */
            bignum_t sq;
            bn_mul(&sq, &r, &r);
            bn_mod(&r, &sq, modulus);

            /* Multiply if bit is 1 */
            if ((w >> bit) & 1) {
                bignum_t mul;
                bn_mul(&mul, &r, &b);
                bn_mod(&r, &mul, modulus);
            }
        }
    }
    memcpy(res, &r, sizeof(bignum_t));
}
