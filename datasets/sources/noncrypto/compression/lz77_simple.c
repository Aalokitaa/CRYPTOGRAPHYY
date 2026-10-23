/*
 * Simple LZ77 Sliding Window Compression (Non-crypto baseline)
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

#define WINDOW_SIZE 256
#define LOOKAHEAD_SIZE 16

typedef struct {
    uint16_t offset;
    uint8_t length;
    uint8_t next_char;
} lz77_token_t;

int lz77_compress(const uint8_t *in, int in_len, lz77_token_t *out, int max_tokens) {
    int cursor = 0;
    int token_count = 0;

    while (cursor < in_len && token_count < max_tokens) {
        int best_offset = 0;
        int best_len = 0;

        int search_start = (cursor > WINDOW_SIZE) ? (cursor - WINDOW_SIZE) : 0;
        int max_match = (in_len - cursor < LOOKAHEAD_SIZE) ? (in_len - cursor) : LOOKAHEAD_SIZE;

        for (int i = search_start; i < cursor; i++) {
            int match_len = 0;
            while (match_len < max_match && in[i + match_len] == in[cursor + match_len]) {
                match_len++;
            }
            if (match_len > best_len) {
                best_len = match_len;
                best_offset = cursor - i;
            }
        }

        out[token_count].offset = (uint16_t)best_offset;
        out[token_count].length = (uint8_t)best_len;
        out[token_count].next_char = (cursor + best_len < in_len) ? in[cursor + best_len] : 0;
        cursor += best_len + 1;
        token_count++;
    }

    return token_count;
}
