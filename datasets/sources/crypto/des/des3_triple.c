/*
 * Triple-DES (3DES) EDE Mode Implementation
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

/* Forward declare DES primitives */
extern void des_encrypt_block(const uint8_t in[8], const void *ks, uint8_t out[8]);

typedef struct {
    uint8_t ks1[128];
    uint8_t ks2[128];
    uint8_t ks3[128];
} des3_context;

void des3_ede_encrypt(const uint8_t in[8], const des3_context *ctx, uint8_t out[8]) {
    uint8_t buf1[8];
    uint8_t buf2[8];

    /* Step 1: Encrypt with Key 1 */
    des_encrypt_block(in, ctx->ks1, buf1);
    /* Step 2: Decrypt with Key 2 (simulated via reversed round keys) */
    des_encrypt_block(buf1, ctx->ks2, buf2);
    /* Step 3: Encrypt with Key 3 */
    des_encrypt_block(buf2, ctx->ks3, out);
}

void des3_ede_cbc(const uint8_t *in, const des3_context *ctx, uint8_t *iv, uint32_t len, uint8_t *out) {
    uint32_t i;
    for (i = 0; i < len; i += 8) {
        uint8_t block[8];
        for (int b = 0; b < 8; b++) {
            block[b] = in[i + b] ^ iv[b];
        }
        des3_ede_encrypt(block, ctx, out + i);
        memcpy(iv, out + i, 8);
    }
}
