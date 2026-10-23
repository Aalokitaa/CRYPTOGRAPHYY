/*
 * HMAC-SHA-256 Implementation (RFC 2104)
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

#define SHA256_BLOCK_SIZE 64
#define SHA256_DIGEST_SIZE 32

/* Forward declarations for SHA-256 */
typedef struct {
    uint8_t data[64];
    uint32_t datalen;
    unsigned long long bitlen;
    uint32_t state[8];
} SHA256_CTX;

extern void sha256_init(SHA256_CTX *ctx);
extern void sha256_update(SHA256_CTX *ctx, const uint8_t data[], size_t len);
extern void sha256_final(SHA256_CTX *ctx, uint8_t hash[]);

void hmac_sha256(const uint8_t *key, size_t key_len, 
                 const uint8_t *msg, size_t msg_len, 
                 uint8_t out[SHA256_DIGEST_SIZE]) {
    SHA256_CTX ctx;
    uint8_t k_pad[SHA256_BLOCK_SIZE];
    uint8_t tk[SHA256_DIGEST_SIZE];

    /* If key is longer than 64 bytes reset it to key=SHA256(key) */
    if (key_len > SHA256_BLOCK_SIZE) {
        sha256_init(&ctx);
        sha256_update(&ctx, key, key_len);
        sha256_final(&ctx, tk);
        key = tk;
        key_len = SHA256_DIGEST_SIZE;
    }

    /* Start inner hash: SHA256(K XOR 0x36 || msg) */
    memset(k_pad, 0, sizeof(k_pad));
    memcpy(k_pad, key, key_len);
    for (int i = 0; i < SHA256_BLOCK_SIZE; i++) {
        k_pad[i] ^= 0x36;
    }

    sha256_init(&ctx);
    sha256_update(&ctx, k_pad, SHA256_BLOCK_SIZE);
    sha256_update(&ctx, msg, msg_len);
    sha256_final(&ctx, out);

    /* Start outer hash: SHA256(K XOR 0x5C || inner_hash) */
    memset(k_pad, 0, sizeof(k_pad));
    memcpy(k_pad, key, key_len);
    for (int i = 0; i < SHA256_BLOCK_SIZE; i++) {
        k_pad[i] ^= 0x5C;
    }

    sha256_init(&ctx);
    sha256_update(&ctx, k_pad, SHA256_BLOCK_SIZE);
    sha256_update(&ctx, out, SHA256_DIGEST_SIZE);
    sha256_final(&ctx, out);
}
