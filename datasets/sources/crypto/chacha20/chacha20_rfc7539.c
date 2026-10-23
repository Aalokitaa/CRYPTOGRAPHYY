/*
 * ChaCha20 Stream Cipher (RFC 7539)
 * License: Public Domain / MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

#define ROTL32(v, n) (((v) << (n)) | ((v) >> (32 - (n))))

#define CHACHA20_QUARTERROUND(a, b, c, d) \
    a += b; d ^= a; d = ROTL32(d, 16); \
    c += d; b ^= c; b = ROTL32(b, 12); \
    a += b; d ^= a; d = ROTL32(d, 8);  \
    c += d; b ^= c; b = ROTL32(b, 7);

void chacha20_block(const uint32_t key[8], const uint32_t nonce[3], uint32_t counter, uint8_t output[64]) {
    uint32_t state[16];
    uint32_t working_state[16];
    int i;

    /* Constant string "expand 32-byte k" */
    state[0] = 0x61707865;
    state[1] = 0x3320646e;
    state[2] = 0x79622d32;
    state[3] = 0x6b206574;

    for (i = 0; i < 8; i++) {
        state[4 + i] = key[i];
    }
    state[12] = counter;
    state[13] = nonce[0];
    state[14] = nonce[1];
    state[15] = nonce[2];

    memcpy(working_state, state, sizeof(state));

    for (i = 0; i < 10; i++) {
        /* Column round */
        CHACHA20_QUARTERROUND(working_state[0], working_state[4], working_state[8],  working_state[12]);
        CHACHA20_QUARTERROUND(working_state[1], working_state[5], working_state[9],  working_state[13]);
        CHACHA20_QUARTERROUND(working_state[2], working_state[6], working_state[10], working_state[14]);
        CHACHA20_QUARTERROUND(working_state[3], working_state[7], working_state[11], working_state[15]);

        /* Diagonal round */
        CHACHA20_QUARTERROUND(working_state[0], working_state[5], working_state[10], working_state[15]);
        CHACHA20_QUARTERROUND(working_state[1], working_state[6], working_state[11], working_state[12]);
        CHACHA20_QUARTERROUND(working_state[2], working_state[7], working_state[8],  working_state[13]);
        CHACHA20_QUARTERROUND(working_state[3], working_state[4], working_state[9],  working_state[14]);
    }

    for (i = 0; i < 16; i++) {
        working_state[i] += state[i];
        output[i * 4 + 0] = (uint8_t)(working_state[i] & 0xFF);
        output[i * 4 + 1] = (uint8_t)((working_state[i] >> 8) & 0xFF);
        output[i * 4 + 2] = (uint8_t)((working_state[i] >> 16) & 0xFF);
        output[i * 4 + 3] = (uint8_t)((working_state[i] >> 24) & 0xFF);
    }
}

void chacha20_crypt(const uint32_t key[8], const uint32_t nonce[3], uint32_t counter,
                    const uint8_t *in, uint8_t *out, size_t len) {
    uint8_t key_stream[64];
    size_t i, j;

    for (i = 0; i < len; i += 64) {
        chacha20_block(key, nonce, counter++, key_stream);
        size_t chunk = (len - i < 64) ? (len - i) : 64;
        for (j = 0; j < chunk; j++) {
            out[i + j] = in[i + j] ^ key_stream[j];
        }
    }
}
