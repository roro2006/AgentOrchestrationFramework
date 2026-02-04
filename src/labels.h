#ifndef LABELS_H
#define LABELS_H

#include "hash.h"
#include "cards.h"
#include <stdint.h>

/* Minimum number of games with both cards present to emit a label */
#define MIN_BOTH_PRESENT 500

/* Beta smoothing parameters */
#define BETA_ALPHA 1.0
#define BETA_BETA 1.0

/* Maximum cards in a single game's GIH set */
#define MAX_GAME_CARDS 100

/* Label computation context */
typedef struct {
    /* Global statistics */
    uint64_t total_games;
    uint64_t total_wins;

    /* Per-card statistics: key = card_id, value = {n, w} */
    HashMap card_stats;

    /* Pair statistics: key = pair_key(a, b), value = {n, w} */
    HashMap pair_stats;

    /* Card database for name lookups */
    CardDb *carddb;
} LabelContext;

/* Label output record */
typedef struct {
    uint64_t card_a;
    uint64_t card_b;
    uint64_t n11, w11;
    uint64_t n10, w10;
    uint64_t n01, w01;
    uint64_t n00, w00;
    double p11, p10, p01, p00;
    double syn_delta;
} LabelRecord;

/* Initialize label computation context. Returns 0 on success. */
int labels_init(LabelContext *ctx, CardDb *carddb);

/* Free label computation context. */
void labels_free(LabelContext *ctx);

/* Process a single game. present_cards is array of card IDs, count is length.
   win is 1 if player won, 0 otherwise. */
void labels_process_game(LabelContext *ctx, uint64_t *present_cards, int count, int win);

/* Process a CSV file of games. Returns number of games processed, -1 on error. */
int labels_process_file(LabelContext *ctx, const char *game_csv_path);

/* Compute smoothed probability with beta prior */
double labels_smooth_prob(uint64_t wins, uint64_t games);

/* Compute synergy label for a pair. Returns 0 on success, fills record. */
int labels_compute_pair(LabelContext *ctx, uint64_t card_a, uint64_t card_b, LabelRecord *record);

/* Write all labels to output CSV. Returns number of labels written, -1 on error. */
int labels_write_csv(LabelContext *ctx, const char *output_path);

/* Callback type for iterating over valid pairs */
typedef void (*LabelCallback)(const LabelRecord *record, void *user_data);

/* Iterate over all pairs meeting threshold, calling callback for each. */
void labels_iterate(LabelContext *ctx, LabelCallback callback, void *user_data);

#endif /* LABELS_H */
