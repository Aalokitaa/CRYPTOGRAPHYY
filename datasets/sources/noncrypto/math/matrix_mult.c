/*
 * Matrix Multiplication & Numerical Routines (Non-crypto baseline)
 * License: MIT
 * CryptoScope benchmark implementation
 */

#include <stdint.h>
#include <string.h>

#define MAT_N 16

void matrix_multiply(const float A[MAT_N][MAT_N], const float B[MAT_N][MAT_N], float C[MAT_N][MAT_N]) {
    for (int i = 0; i < MAT_N; ++i) {
        for (int j = 0; j < MAT_N; ++j) {
            float sum = 0.0f;
            for (int k = 0; k < MAT_N; ++k) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }
}

/* Sieve of Eratosthenes prime generation */
int prime_sieve(uint8_t *is_prime, int max_n) {
    memset(is_prime, 1, max_n);
    is_prime[0] = 0;
    is_prime[1] = 0;
    int count = 0;

    for (int p = 2; p * p <= max_n; p++) {
        if (is_prime[p]) {
            for (int i = p * p; i < max_n; i += p) {
                is_prime[i] = 0;
            }
        }
    }

    for (int p = 2; p < max_n; p++) {
        if (is_prime[p]) count++;
    }
    return count;
}
