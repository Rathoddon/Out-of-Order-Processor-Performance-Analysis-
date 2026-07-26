// memory_heavy.c
// Pointer-chasing linked list traversal - shuffled node order defeats
// cache prefetching and spatial locality, creating frequent cache misses.
// This is where OoO / bigger ROB should show its biggest advantage,
// since the CPU can do other work while a load is outstanding.

#define NUM_NODES 20000
#define TRAVERSALS 50

typedef struct Node {
    struct Node *next;
    int value;
    int pad[6]; // pad node size so nodes spread across more cache lines
} Node;

static Node nodes[NUM_NODES];

// Simple deterministic pseudo-random shuffle (no library rand() needed)
unsigned int seed = 12345;
unsigned int next_rand() {
    seed = seed * 1103515245 + 12345;
    return (seed >> 16) & 0x7FFF;
}

int main() {
    // Build nodes
    for (int i = 0; i < NUM_NODES; i++) {
        nodes[i].value = i;
        nodes[i].next = 0;
    }

    // Shuffle the link order using Fisher-Yates on an index array
    int indices[NUM_NODES];
    for (int i = 0; i < NUM_NODES; i++) indices[i] = i;

    for (int i = NUM_NODES - 1; i > 0; i--) {
        int j = next_rand() % (i + 1);
        int tmp = indices[i];
        indices[i] = indices[j];
        indices[j] = tmp;
    }

    // Link nodes in shuffled order -> pointer chasing pattern
    for (int i = 0; i < NUM_NODES - 1; i++) {
        nodes[indices[i]].next = &nodes[indices[i + 1]];
    }
    nodes[indices[NUM_NODES - 1]].next = &nodes[indices[0]]; // circular

    // Traverse repeatedly - each ->next dereference is likely a cache miss
    Node *cur = &nodes[indices[0]];
    long sum = 0;
    for (int t = 0; t < TRAVERSALS; t++) {
        for (int i = 0; i < NUM_NODES; i++) {
            sum += cur->value;
            cur = cur->next;
        }
    }

    return (int)(sum % 256);
}
