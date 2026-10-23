/*
 * XOR and Rotate Obfuscation Routine
 * Hard negative: demonstrates XOR and bitwise rotate loops without standard crypto structure
 * License: Public Domain
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <stddef.h>

#define ROTL8(x, r) (((x) << (r)) | ((x) >> (8 - (r))))
#define ROTR8(x, r) (((x) >> (r)) | ((x) << (8 - (r))))

void xor_rotate_obfuscate(const uint8_t *in, uint8_t *out, size_t len, const uint8_t *key, size_t keylen) {
    uint8_t rolling_accumulator = 0x5A;
    for (size_t i = 0; i < len; i++) {
        uint8_t k = key[i % keylen];
        uint8_t b = in[i] ^ k ^ rolling_accumulator;
        /* Circular 3-bit left rotate */
        out[i] = ROTL8(b, 3);
        rolling_accumulator = (rolling_accumulator + out[i]) ^ 0xA5;
    }
}

void xor_rotate_deobfuscate(const uint8_t *in, uint8_t *out, size_t len, const uint8_t *key, size_t keylen) {
    uint8_t rolling_accumulator = 0x5A;
    for (size_t i = 0; i < len; i++) {
        uint8_t k = key[i % keylen];
        uint8_t b = ROTR8(in[i], 3);
        out[i] = b ^ k ^ rolling_accumulator;
        rolling_accumulator = (rolling_accumulator + in[i]) ^ 0xA5;
    }
}
