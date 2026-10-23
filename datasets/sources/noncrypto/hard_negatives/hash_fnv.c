/*
 * Fowler-Noll-Vo (FNV-1a) Non-Cryptographic Hash
 * Hard negative: hash loops, prime multiplications, and XOR steps
 * License: Public Domain
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <stddef.h>

#define FNV_OFFSET_BASIS_32 0x811c9dc5U
#define FNV_PRIME_32        0x01000193U

#define FNV_OFFSET_BASIS_64 0xcbf29ce484222325ULL
#define FNV_PRIME_64        0x100000001b3ULL

uint32_t fnv1a_32(const void *data, size_t len) {
    const uint8_t *bytes = (const uint8_t *)data;
    uint32_t hash = FNV_OFFSET_BASIS_32;

    for (size_t i = 0; i < len; ++i) {
        hash ^= bytes[i];
        hash *= FNV_PRIME_32;
    }
    return hash;
}

uint64_t fnv1a_64(const void *data, size_t len) {
    const uint8_t *bytes = (const uint8_t *)data;
    uint64_t hash = FNV_OFFSET_BASIS_64;

    for (size_t i = 0; i < len; ++i) {
        hash ^= bytes[i];
        hash *= FNV_PRIME_64;
    }
    return hash;
}
