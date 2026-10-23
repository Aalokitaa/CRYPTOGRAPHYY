/*
 * Base64 Encoding & Decoding
 * Hard negative: involves 64-char table lookup, 6-bit and 8-bit shifts, masking
 * License: Public Domain / MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <stddef.h>

static const char b64_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

int base64_encode(const uint8_t *src, size_t len, char *out) {
    size_t i = 0, j = 0;
    while (i < len) {
        uint32_t octet_a = i < len ? src[i++] : 0;
        uint32_t octet_b = i < len ? src[i++] : 0;
        uint32_t octet_c = i < len ? src[i++] : 0;

        uint32_t triple = (octet_a << 16) + (octet_b << 8) + octet_c;

        out[j++] = b64_table[(triple >> 18) & 0x3F];
        out[j++] = b64_table[(triple >> 12) & 0x3F];
        out[j++] = (i > len + 1) ? '=' : b64_table[(triple >> 6) & 0x3F];
        out[j++] = (i > len) ? '=' : b64_table[triple & 0x3F];
    }
    out[j] = '\0';
    return (int)j;
}

int base64_decode_char(char c) {
    if (c >= 'A' && c <= 'Z') return c - 'A';
    if (c >= 'a' && c <= 'z') return c - 'a' + 26;
    if (c >= '0' && c <= '9') return c - '0' + 52;
    if (c == '+') return 62;
    if (c == '/') return 63;
    return -1;
}

int base64_decode(const char *src, size_t len, uint8_t *out) {
    size_t i = 0, j = 0;
    while (i < len) {
        int d0 = base64_decode_char(src[i++]);
        int d1 = base64_decode_char(src[i++]);
        int d2 = (i < len && src[i] != '=') ? base64_decode_char(src[i++]) : 0;
        int d3 = (i < len && src[i] != '=') ? base64_decode_char(src[i++]) : 0;

        if (d0 < 0 || d1 < 0) break;
        uint32_t triple = (d0 << 18) | (d1 << 12) | (d2 << 6) | d3;

        out[j++] = (triple >> 16) & 0xFF;
        if (d2 >= 0) out[j++] = (triple >> 8) & 0xFF;
        if (d3 >= 0) out[j++] = triple & 0xFF;
    }
    return (int)j;
}
