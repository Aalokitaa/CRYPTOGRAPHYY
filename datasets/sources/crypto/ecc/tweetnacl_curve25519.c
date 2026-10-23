/*
 * TweetNaCl-derived Curve25519 Scalarmult Implementation
 * License: Public Domain
 * Authors: Daniel J. Bernstein, Bernard van Gastel, Wesley Janssen, 
 *          Tanja Lange, Peter Schwabe, Sjaak Smetsers
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

typedef int64_t gf[16];

static const uint8_t _9[32] = {9};
static const gf _121665 = {0xDB41, 1};

static void car25519(gf o) {
    int i;
    int64_t c;
    for (i = 0; i < 16; ++i) {
        o[i] += (1LL << 16);
        c = o[i] >> 16;
        o[(i + 1) * (i < 15)] += c - 1 + 37 * (c - 1) * (i == 15);
        o[i] -= c << 16;
    }
}

static void sel25519(gf p, gf q, int b) {
    int64_t t, c = ~(b - 1);
    for (int i = 0; i < 16; ++i) {
        t = c & (p[i] ^ q[i]);
        p[i] ^= t;
        q[i] ^= t;
    }
}

static void A(gf o, const gf a, const gf b) {
    for (int i = 0; i < 16; ++i) o[i] = a[i] + b[i];
}

static void Z(gf o, const gf a, const gf b) {
    for (int i = 0; i < 16; ++i) o[i] = a[i] - b[i];
}

static void M(gf o, const gf a, const gf b) {
    int64_t t[31] = {0};
    for (int i = 0; i < 16; ++i) {
        for (int j = 0; j < 16; ++j) {
            t[i + j] += a[i] * b[j];
        }
    }
    for (int i = 0; i < 15; ++i) {
        t[i] += 38 * t[i + 16];
    }
    for (int i = 0; i < 16; ++i) o[i] = t[i];
    car25519(o);
    car25519(o);
}

static void S(gf o, const gf a) {
    M(o, a, a);
}

static void inv25519(gf o, const gf i) {
    gf c;
    int a;
    for (a = 0; a < 16; ++a) c[a] = i[a];
    for (a = 253; a >= 0; --a) {
        S(c, c);
        if (a != 2 && a != 4) M(c, c, i);
    }
    for (a = 0; a < 16; ++a) o[a] = c[a];
}

/* Curve25519 Montgomery ladder */
int crypto_scalarmult_curve25519(uint8_t *q, const uint8_t *n, const uint8_t *p) {
    uint8_t z[32];
    int64_t i;
    gf x, a, b, c, d, e, f;
    for (i = 0; i < 31; ++i) z[i] = n[i];
    z[31] = (n[31] & 127) | 64;
    z[0] &= 248;

    for (i = 0; i < 16; ++i) {
        x[i] = p[2 * i] + ((int64_t)p[2 * i + 1] << 8);
        a[i] = b[i] = c[i] = d[i] = 0;
    }
    b[0] = 1;
    d[0] = 1;
    for (i = 0; i < 16; ++i) a[i] = x[i];

    for (i = 254; i >= 0; --i) {
        int r = (z[i >> 3] >> (i & 7)) & 1;
        sel25519(a, b, r);
        sel25519(c, d, r);
        A(e, a, c);
        Z(a, a, c);
        A(c, b, d);
        Z(b, b, d);
        S(d, e);
        S(f, a);
        M(a, c, a);
        M(c, b, e);
        A(e, a, c);
        Z(a, a, c);
        S(b, a);
        Z(c, d, f);
        M(a, c, _121665);
        A(a, a, d);
        M(c, c, a);
        M(a, d, f);
        M(d, b, x);
        S(b, e);
        sel25519(a, b, r);
        sel25519(c, d, r);
    }

    inv25519(c, c);
    M(a, a, c);
    for (i = 0; i < 16; ++i) {
        q[2 * i] = a[i] & 0xFF;
        q[2 * i + 1] = (a[i] >> 8) & 0xFF;
    }
    return 0;
}
