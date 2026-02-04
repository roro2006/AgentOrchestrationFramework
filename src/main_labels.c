#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "labels.h"
#include "cards.h"

static void print_usage(const char *program) {
    fprintf(stderr, "Usage: %s <game_data.csv> <cards.csv> <output_labels.csv>\n", program);
    fprintf(stderr, "\n");
    fprintf(stderr, "Arguments:\n");
    fprintf(stderr, "  game_data.csv    - Game data CSV file (e.g., powered_premier_games.csv)\n");
    fprintf(stderr, "  cards.csv        - Card database CSV file\n");
    fprintf(stderr, "  output_labels.csv - Output file for synergy labels\n");
    fprintf(stderr, "\n");
    fprintf(stderr, "Example:\n");
    fprintf(stderr, "  %s data/tmp/powered_premier_games.csv data/raw/cards.csv data/out/labels_premier.csv\n", program);
}

int main(int argc, char *argv[]) {
    if (argc < 4) {
        print_usage(argv[0]);
        return 1;
    }

    const char *game_path = argv[1];
    const char *cards_path = argv[2];
    const char *output_path = argv[3];

    fprintf(stderr, "=== Label Generation ===\n");
    fprintf(stderr, "Game data: %s\n", game_path);
    fprintf(stderr, "Cards DB:  %s\n", cards_path);
    fprintf(stderr, "Output:    %s\n", output_path);
    fprintf(stderr, "\n");

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

    /* Initialize label context */
    LabelContext ctx;
    if (labels_init(&ctx, &carddb) != 0) {
        fprintf(stderr, "Error: Failed to initialize label context\n");
        carddb_free(&carddb);
        return 1;
    }

    /* Process game data */
    fprintf(stderr, "Processing game data...\n");
    int games_processed = labels_process_file(&ctx, game_path);
    if (games_processed < 0) {
        fprintf(stderr, "Error: Failed to process game data\n");
        labels_free(&ctx);
        carddb_free(&carddb);
        return 1;
    }

    fprintf(stderr, "\nProcessing complete:\n");
    fprintf(stderr, "  Total games: %lu\n", (unsigned long)ctx.total_games);
    fprintf(stderr, "  Total wins:  %lu\n", (unsigned long)ctx.total_wins);
    fprintf(stderr, "  Win rate:    %.4f\n",
            ctx.total_games > 0 ? (double)ctx.total_wins / ctx.total_games : 0.0);
    fprintf(stderr, "  Unique cards tracked: %zu\n", hashmap_size(&ctx.card_stats));
    fprintf(stderr, "  Card pairs tracked:   %zu\n", hashmap_size(&ctx.pair_stats));
    fprintf(stderr, "\n");

    /* Write output */
    fprintf(stderr, "Writing labels to %s...\n", output_path);
    int labels_written = labels_write_csv(&ctx, output_path);
    if (labels_written < 0) {
        fprintf(stderr, "Error: Failed to write labels\n");
        labels_free(&ctx);
        carddb_free(&carddb);
        return 1;
    }

    fprintf(stderr, "Wrote %d labels (pairs meeting threshold >= %d)\n",
            labels_written, MIN_BOTH_PRESENT);

    /* Cleanup */
    labels_free(&ctx);
    carddb_free(&carddb);

    fprintf(stderr, "\nDone!\n");
    return 0;
}
