/*
 * JSON Tokenizer & KMP String Search (Non-crypto baseline)
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

typedef enum {
    TOKEN_START_OBJ, TOKEN_END_OBJ,
    TOKEN_START_ARR, TOKEN_END_ARR,
    TOKEN_STRING,    TOKEN_NUMBER,
    TOKEN_COLON,     TOKEN_COMMA,
    TOKEN_EOF,       TOKEN_ERROR
} json_token_type_t;

json_token_type_t json_next_token(const char *src, int *pos) {
    while (src[*pos] != '\0') {
        char c = src[*pos];
        if (c == ' ' || c == '\t' || c == '\r' || c == '\n') {
            (*pos)++;
            continue;
        }
        (*pos)++;
        switch (c) {
            case '{': return TOKEN_START_OBJ;
            case '}': return TOKEN_END_OBJ;
            case '[': return TOKEN_START_ARR;
            case ']': return TOKEN_END_ARR;
            case ':': return TOKEN_COLON;
            case ',': return TOKEN_COMMA;
            case '"':
                while (src[*pos] != '\0' && src[*pos] != '"') {
                    if (src[*pos] == '\\' && src[*pos+1] != '\0') (*pos)++;
                    (*pos)++;
                }
                if (src[*pos] == '"') (*pos)++;
                return TOKEN_STRING;
            default:
                if ((c >= '0' && c <= '9') || c == '-') {
                    while (src[*pos] >= '0' && src[*pos] <= '9') (*pos)++;
                    return TOKEN_NUMBER;
                }
                return TOKEN_ERROR;
        }
    }
    return TOKEN_EOF;
}

/* Knuth-Morris-Pratt pattern search */
int kmp_search(const char *text, int n, const char *pattern, int m) {
    int lps[64] = {0};
    int len = 0;
    int i = 1;
    while (i < m && i < 64) {
        if (pattern[i] == pattern[len]) {
            len++;
            lps[i] = len;
            i++;
        } else {
            if (len != 0) {
                len = lps[len - 1];
            } else {
                lps[i] = 0;
                i++;
            }
        }
    }

    i = 0;
    int j = 0;
    while (i < n) {
        if (pattern[j] == text[i]) {
            j++;
            i++;
        }
        if (j == m) {
            return i - j; /* Found */
        } else if (i < n && pattern[j] != text[i]) {
            if (j != 0) j = lps[j - 1];
            else i++;
        }
    }
    return -1;
}
