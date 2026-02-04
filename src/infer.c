#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "train.h"
#include "cards.h"

static void print_usage(const char *program) {
    fprintf(stderr, "Usage: %s <model.bin> <cards.csv> \"Card Name A\" \"Card Name B\"\n", program);
    fprintf(stderr, "\n");
    fprintf(stderr, "Arguments:\n");
    fprintf(stderr, "  model.bin    - Binary model file (from train program)\n");
    fprintf(stderr, "  cards.csv    - Card database CSV file\n");
    fprintf(stderr, "  Card Name A  - First card name (in quotes)\n");
    fprintf(stderr, "  Card Name B  - Second card name (in quotes)\n");
    fprintf(stderr, "\n");
    fprintf(stderr, "Example:\n");
    fprintf(stderr, "  %s data/out/model_premier.bin data/raw/cards.csv \"Tinker\" \"Blightsteel Colossus\"\n", program);
}

int main(int argc, char *argv[]) {
    if (argc < 5) {
        print_usage(argv[0]);
        return 1;
    }

    const char *model_path = argv[1];
    const char *cards_path = argv[2];
    const char *card_name_a = argv[3];
    const char *card_name_b = argv[4];

    /* Load card database */
    CardDb carddb;
    if (carddb_init(&carddb) != 0) {
        fprintf(stderr, "Error: Failed to initialize card database\n");
        return 1;
    }

    int cards_loaded = carddb_load(&carddb, cards_path);
    if (cards_loaded < 0) {
        fprintf(stderr, "Error: Failed to load cards from %s\n", cards_path);
        carddb_free(&carddb);
        return 1;
    }
    fprintf(stderr, "Loaded %d cards from database\n", cards_loaded);

    /* Look up card IDs */
    uint64_t card_a = carddb_get_id(&carddb, card_name_a);
    uint64_t card_b = carddb_get_id(&carddb, card_name_b);

    if (card_a == 0) {
        fprintf(stderr, "Error: Card not found: \"%s\"\n", card_name_a);
        carddb_free(&carddb);
        return 1;
    }

    if (card_b == 0) {
        fprintf(stderr, "Error: Card not found: \"%s\"\n", card_name_b);
        carddb_free(&carddb);
        return 1;
    }

    fprintf(stderr, "Card A: \"%s\" (ID: %lu)\n", card_name_a, (unsigned long)card_a);
    fprintf(stderr, "Card B: \"%s\" (ID: %lu)\n", card_name_b, (unsigned long)card_b);

    /* Load model */
    SynergyModel model;
    if (model_load(&model, model_path) != 0) {
        fprintf(stderr, "Error: Failed to load model from %s\n", model_path);
        carddb_free(&carddb);
        return 1;
    }
    fprintf(stderr, "Loaded model with %zu cards, dimension %d\n",
            model.num_cards, model.embed_dim);

    /* Compute prediction */
    float prediction = model_predict(&model, card_a, card_b);

    /* Output result */
    printf("\n=== Synergy Prediction ===\n");
    printf("Card A: %s\n", card_name_a);
    printf("Card B: %s\n", card_name_b);
    printf("Predicted synergy: %.6f\n", prediction);

    /* Interpret the result */
    if (prediction > 0.02) {
        printf("Interpretation: STRONG POSITIVE SYNERGY\n");
    } else if (prediction > 0.005) {
        printf("Interpretation: Moderate positive synergy\n");
    } else if (prediction > -0.005) {
        printf("Interpretation: Neutral (little to no synergy)\n");
    } else if (prediction > -0.02) {
        printf("Interpretation: Moderate negative synergy (anti-synergy)\n");
    } else {
        printf("Interpretation: STRONG NEGATIVE SYNERGY (anti-synergy)\n");
    }

    /* Cleanup */
    model_free(&model);
    carddb_free(&carddb);

    return 0;
}
