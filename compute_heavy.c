// compute_heavy.c
// Matrix multiplication - high arithmetic intensity, data fits in cache,
// mostly independent multiply-add operations (good ILP for OoO to exploit).

#define N 60

int A[N][N];
int B[N][N];
int C[N][N];

int main() {
    // Initialize with simple values (deterministic, no I/O needed)
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (i + j) % 7;
            B[i][j] = (i - j) % 5;
            C[i][j] = 0;
        }
    }

    // Matrix multiply - the compute-heavy core
    for (int i = 0; i < N; i++) {
        for (int j = 0; j < N; j++) {
            int sum = 0;
            for (int k = 0; k < N; k++) {
                sum += A[i][k] * B[k][j];
            }
            C[i][j] = sum;
        }
    }

    return C[N-1][N-1] % 256;
}
