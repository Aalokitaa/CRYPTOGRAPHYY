/*
 * RSA PKCS#1 v1.5 Encryption & Signature Verification
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

extern void rsa_mod_exp(void *res, const void *base, const void *exp, const void *modulus);

int rsa_pkcs1_pad_encrypt(const uint8_t *in, int in_len, uint8_t *out, int mod_len) {
    if (in_len > mod_len - 11) return -1;
    out[0] = 0x00;
    out[1] = 0x02; /* Block type 2 for encryption */
    int pad_len = mod_len - in_len - 3;
    for (int i = 0; i < pad_len; i++) {
        out[2 + i] = (uint8_t)(0x12 + (i % 200)); /* Pseudo-random non-zero */
    }
    out[2 + pad_len] = 0x00;
    memcpy(out + 3 + pad_len, in, in_len);
    return 0;
}

int rsa_pkcs1_verify_signature(const uint8_t *decrypted_block, int mod_len, const uint8_t *expected_hash, int hash_len) {
    if (decrypted_block[0] != 0x00 || decrypted_block[1] != 0x01) {
        return -1; /* Invalid PKCS#1 v1.5 signature block */
    }
    int idx = 2;
    while (idx < mod_len && decrypted_block[idx] == 0xFF) {
        idx++;
    }
    if (idx >= mod_len || decrypted_block[idx] != 0x00) {
        return -1;
    }
    idx++; /* Step over 0x00 separator */
    int remaining = mod_len - idx;
    if (remaining < hash_len) return -1;
    if (memcmp(decrypted_block + mod_len - hash_len, expected_hash, hash_len) != 0) {
        return -2; /* Hash mismatch */
    }
    return 0; /* Signature verified */
}
