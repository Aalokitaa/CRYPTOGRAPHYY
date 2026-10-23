/*
 * XorShift128+ PRNG Generator
 * Hard negative: pseudo-random number generation with bit shifts and additions
 * License: Public Domain
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <stddef.h>


typedef struct {
    uint64_t s[2];
} xorshift128p_state;

void xorshift128p_seed(xorshift128p_state *state, uint64_t seed1, uint64_t seed2) {
    state->s[0] = (seed1 != 0) ? seed1 : 0x853c49e6748fea9bULL;
    state->s[1] = (seed2 != 0) ? seed2 : 0xda3e39cb94b95bdbULL;
}

uint64_t xorshift128p_next(xorshift128p_state *state) {
    uint64_t s1 = state->s[0];
    const uint64_t s0 = state->s[1];
    state->s[0] = s0;
    s1 ^= s1 << 23;
    state->s[1] = s1 ^ s0 ^ (s1 >> 17) ^ (s0 >> 26);
    return state->s[1] + s0;
}

void xorshift128p_fill(xorshift128p_state *state, uint8_t *buffer, size_t length) {
    size_t i = 0;
    while (i < length) {
        uint64_t r = xorshift128p_next(state);
        size_t chunk = (length - i < 8) ? (length - i) : 8;
        for (size_t b = 0; b < chunk; b++) {
            buffer[i + b] = (uint8_t)((r >> (b * 8)) & 0xFF);
        }
        i += chunk;
    }
}
