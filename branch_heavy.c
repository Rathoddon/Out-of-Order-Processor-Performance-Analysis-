// branch_heavy.c
// Recursive quicksort on pseudo-random data - lots of data-dependent
// comparisons and branches, stressing the branch predictor and
// recovery cost (ROB flush) on mispredictions.

#define ARR_SIZE 5000
#define NUM_ROUNDS 20

int arr[ARR_SIZE];

unsigned int seed = 98765;
unsigned int next_rand() {
    seed = seed * 1103515245 + 12345;
    return (seed >> 16) & 0x7FFF;
}

void swap(int *a, int *b) {
    int t = *a; *a = *b; *b = t;
}

int partition(int *a, int low, int high) {
    int pivot = a[high];
    int i = low - 1;
    for (int j = low; j < high; j++) {
        if (a[j] < pivot) {          // data-dependent branch
            i++;
            swap(&a[i], &a[j]);
        }
    }
    swap(&a[i + 1], &a[high]);
    return i + 1;
}

void quicksort(int *a, int low, int high) {
    if (low < high) {                 // recursive branch
        int pi = partition(a, low, high);
        quicksort(a, low, pi - 1);
        quicksort(a, pi + 1, high);
    }
}

int main() {
    long checksum = 0;

    for (int r = 0; r < NUM_ROUNDS; r++) {
        // Refill with pseudo-random data each round
        for (int i = 0; i < ARR_SIZE; i++) {
            arr[i] = next_rand() % 100000;
        }

        quicksort(arr, 0, ARR_SIZE - 1);

        checksum += arr[0] + arr[ARR_SIZE / 2] + arr[ARR_SIZE - 1];
    }

    return (int)(checksum % 256);
}
