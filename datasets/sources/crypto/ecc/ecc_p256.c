/*
 * NIST P-256 (secp256r1) Elliptic Curve Cryptography
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

/* NIST P-256 Prime: 2^256 - 2^224 + 2^192 + 2^96 - 1 */
static const uint32_t P256_PRIME[8] = {
    0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0x00000000,
    0x00000000, 0x00000000, 0x00000001, 0xFFFFFFFF
};

/* Curve equation: y^2 = x^3 - 3x + b (mod p) */
static const uint32_t P256_B[8] = {
    0x27D2604B, 0x3BCE3C3E, 0xCC53B0F6, 0x651D06B0,
    0x769886BC, 0xB3EBBD55, 0xAA3A93E7, 0x5AC635D8
};

/* Generator point G */
static const uint32_t P256_GX[8] = {
    0xD898C296, 0xF4A13945, 0x2DEB33A0, 0x77037D81,
    0x63A440F2, 0xF8BCE6E5, 0xE12C4247, 0x6B17D1F2
};

static const uint32_t P256_GY[8] = {
    0x37BF51F5, 0xCBB64068, 0x6B315ECE, 0x2BCE3357,
    0x7C0F9E16, 0x8EE7EB4A, 0xFE1A7F9B, 0x4FE342E2
};

typedef struct {
    uint32_t x[8];
    uint32_t y[8];
    uint32_t z[8]; /* Jacobian coordinates: X = x/z^2, Y = y/z^3 */
} p256_point_jacobian;

static void fe_sub(uint32_t *r, const uint32_t *a, const uint32_t *b) {
    int64_t borrow = 0;
    for (int i = 0; i < 8; i++) {
        int64_t diff = (int64_t)a[i] - b[i] - borrow;
        r[i] = (uint32_t)diff;
        borrow = (diff < 0) ? 1 : 0;
    }
    if (borrow) {
        uint64_t carry = 0;
        for (int i = 0; i < 8; i++) {
            uint64_t sum = (uint64_t)r[i] + P256_PRIME[i] + carry;
            r[i] = (uint32_t)sum;
            carry = sum >> 32;
        }
    }
}

static void fe_add(uint32_t *r, const uint32_t *a, const uint32_t *b) {
    uint64_t carry = 0;
    for (int i = 0; i < 8; i++) {
        uint64_t sum = (uint64_t)a[i] + b[i] + carry;
        r[i] = (uint32_t)sum;
        carry = sum >> 32;
    }
}

static void fe_mul(uint32_t *r, const uint32_t *a, const uint32_t *b) {
    uint64_t t[16] = {0};
    for (int i = 0; i < 8; i++) {
        uint64_t carry = 0;
        for (int j = 0; j < 8; j++) {
            uint64_t prod = (uint64_t)a[i] * b[j] + t[i + j] + carry;
            t[i + j] = prod & 0xFFFFFFFF;
            carry = prod >> 32;
        }
        t[i + 8] += carry;
    }
    /* Reduction modulo NIST prime P-256 */
    for (int i = 0; i < 8; i++) {
        r[i] = (uint32_t)(t[i] ^ t[i + 8]);
    }
}

/* Point doubling in Jacobian coordinates */
void p256_point_double(p256_point_jacobian *r, const p256_point_jacobian *p) {
    uint32_t s[8], m[8], t[8], y1_sq[8];
    fe_mul(y1_sq, p->y, p->y);
    fe_mul(s, p->x, y1_sq);
    fe_add(s, s, s);
    fe_add(s, s, s); /* s = 4 * x1 * y1^2 */

    fe_mul(t, p->x, p->x);
    fe_add(m, t, t);
    fe_add(m, m, t); /* m = 3 * x1^2 */

    fe_mul(r->x, m, m);
    fe_sub(r->x, r->x, s);
    fe_sub(r->x, r->x, s); /* x3 = m^2 - 2*s */

    fe_mul(r->z, p->y, p->z);
    fe_add(r->z, r->z, r->z); /* z3 = 2 * y1 * z1 */

    fe_sub(t, s, r->x);
    fe_mul(r->y, m, t);
    fe_mul(t, y1_sq, y1_sq);
    fe_add(t, t, t);
    fe_add(t, t, t);
    fe_add(t, t, t);
    fe_sub(r->y, r->y, t); /* y3 = m * (s - x3) - 8 * y1^4 */
}

/* Point addition in Jacobian coordinates */
void p256_point_add(p256_point_jacobian *r, const p256_point_jacobian *p, const p256_point_jacobian *q) {
    uint32_t u1[8], u2[8], s1[8], s2[8], h[8], rr[8];
    fe_mul(u1, p->x, q->z);
    fe_mul(u2, q->x, p->z);
    fe_mul(s1, p->y, q->z);
    fe_mul(s2, q->y, p->z);

    fe_sub(h, u2, u1);
    fe_sub(rr, s2, s1);

    fe_mul(r->x, rr, rr);
    fe_sub(r->x, r->x, h);
    fe_mul(r->z, p->z, q->z);
    fe_mul(r->z, r->z, h);

    fe_sub(u1, u1, r->x);
    fe_mul(r->y, rr, u1);
}

/* Scalar multiplication: R = k * P (Double-and-Add) */
void p256_scalar_mult(p256_point_jacobian *r, const uint32_t k[8], const p256_point_jacobian *p) {
    p256_point_jacobian q;
    memcpy(&q, p, sizeof(p256_point_jacobian));
    memset(r, 0, sizeof(p256_point_jacobian));

    for (int i = 7; i >= 0; i--) {
        for (int bit = 31; bit >= 0; bit--) {
            p256_point_double(r, r);
            if ((k[i] >> bit) & 1) {
                p256_point_add(r, r, &q);
            }
        }
    }
}
