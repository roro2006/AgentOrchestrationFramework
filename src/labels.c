#include "labels.h"
#include "csv.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <ctype.h>

static int field_nonzero(const char *value) {
    if (!value) return 0;
    while (*value && isspace((unsigned char)*value)) value++;
    if (*value == '\0') return 0;
    char *end = NULL;
    long v = strtol(value, &end, 10);
    if (end && end != value) return v > 0;
    return (value[0] == 't' || value[0] == 'T' || value[0] == 'y' || value[0] == 'Y');
}

int labels_init(LabelContext *ctx, CardDb *carddb) {
    if (!ctx) return -1;

    ctx->total_games = 0;
    ctx->total_wins = 0;
    ctx->carddb = carddb;

    if (hashmap_init(&ctx->card_stats, 4096) != 0) {
        return -1;
    }

    if (hashmap_init(&ctx->pair_stats, 65536) != 0) {
        hashmap_free(&ctx->card_stats);
        return -1;
    }

    return 0;
}

void labels_free(LabelContext *ctx) {
    if (ctx) {
        hashmap_free(&ctx->card_stats);
        hashmap_free(&ctx->pair_stats);
    }
}

void labels_process_game(LabelContext *ctx, uint64_t *present_cards, int count, int win) {
    if (!ctx) return;

    /* Update global counts */
    ctx->total_games++;
    if (win) ctx->total_wins++;

    if (!present_cards || count <= 0) return;

    /* Remove duplicates and sort for consistent pair iteration */
    uint64_t unique[MAX_GAME_CARDS];
    int unique_count = 0;

    for (int i = 0; i < count && unique_count < MAX_GAME_CARDS; i++) {
        int found = 0;
        for (int j = 0; j < unique_count; j++) {
            if (unique[j] == present_cards[i]) {
                found = 1;
                break;
            }
        }
        if (!found) {
            unique[unique_count++] = present_cards[i];
        }
    }

    /* Update per-card statistics */
    for (int i = 0; i < unique_count; i++) {
        hashmap_increment(&ctx->card_stats, unique[i], win);
    }

    /* Update pair statistics for all unordered pairs */
    for (int i = 0; i < unique_count; i++) {
        for (int j = i + 1; j < unique_count; j++) {
            uint64_t pk = pair_key(unique[i], unique[j]);
            hashmap_increment(&ctx->pair_stats, pk, win);
        }
    }
}

int labels_process_file(LabelContext *ctx, const char *game_csv_path) {
    if (!ctx || !game_csv_path) return -1;

    CsvReader reader;
    if (csv_open(&reader, game_csv_path) != 0) {
        fprintf(stderr, "Error: Cannot open game file: %s\n", game_csv_path);
        return -1;
    }

    /* Read header */
    if (csv_next_row(&reader) != 1) {
        csv_close(&reader);
        return -1;
    }

    /* Find relevant columns */
    int won_col = csv_find_column(&reader, "won");
    int opening_hand_col = -1;
    int drawn_col = -1;

    /* Try alternative column names */
    if (won_col < 0) won_col = csv_find_column(&reader, "user_win");
    if (opening_hand_col < 0) opening_hand_col = csv_find_column(&reader, "opening_hand");
    if (opening_hand_col < 0) opening_hand_col = csv_find_column(&reader, "opening_hand_card_ids");
    if (drawn_col < 0) drawn_col = csv_find_column(&reader, "drawn");
    if (drawn_col < 0) drawn_col = csv_find_column(&reader, "drawn_card_ids");

    if (won_col < 0) {
        fprintf(stderr, "Error: Cannot find 'won' column in game data\n");
        csv_close(&reader);
        return -1;
    }

    int num_fields = reader.num_fields;
    int per_card_mode = 0;
    int *opening_hand_cols = NULL;
    int *drawn_cols = NULL;
    uint64_t *card_ids = NULL;
    int card_col_count = 0;

    if (opening_hand_col < 0 || drawn_col < 0) {
        opening_hand_cols = malloc(sizeof(int) * num_fields);
        drawn_cols = malloc(sizeof(int) * num_fields);
        card_ids = malloc(sizeof(uint64_t) * num_fields);
        if (!opening_hand_cols || !drawn_cols || !card_ids) {
            free(opening_hand_cols);
            free(drawn_cols);
            free(card_ids);
            csv_close(&reader);
            return -1;
        }

        for (int i = 0; i < num_fields; i++) {
            const char *name = csv_get_field(&reader, i);
            if (!name) continue;
            if (strncmp(name, "opening_hand_", 13) == 0) {
                const char *card_name = name + 13;
                uint64_t card_id = carddb_get_id(ctx->carddb, card_name);
                if (card_id == 0) continue;
                opening_hand_cols[card_col_count] = i;
                drawn_cols[card_col_count] = -1;
                card_ids[card_col_count] = card_id;
                card_col_count++;
            }
        }

        for (int i = 0; i < num_fields; i++) {
            const char *name = csv_get_field(&reader, i);
            if (!name) continue;
            if (strncmp(name, "drawn_", 6) == 0) {
                const char *card_name = name + 6;
                uint64_t card_id = carddb_get_id(ctx->carddb, card_name);
                if (card_id == 0) continue;
                for (int j = 0; j < card_col_count; j++) {
                    if (card_ids[j] == card_id) {
                        drawn_cols[j] = i;
                        break;
                    }
                }
            }
        }

        if (card_col_count > 0) {
            per_card_mode = 1;
        }
    }

    int games_processed = 0;
    uint64_t present_cards[MAX_GAME_CARDS * 2];

    while (csv_next_row(&reader) == 1) {
        const char *won_str = csv_get_field(&reader, won_col);
        if (!won_str) continue;

        int win = (won_str[0] == '1' || won_str[0] == 't' || won_str[0] == 'T');

        int card_count = 0;

        if (per_card_mode) {
            for (int i = 0; i < card_col_count && card_count < MAX_GAME_CARDS * 2; i++) {
                int present = 0;
                if (opening_hand_cols[i] >= 0) {
                    const char *hand_val = csv_get_field(&reader, opening_hand_cols[i]);
                    if (field_nonzero(hand_val)) present = 1;
                }
                if (!present && drawn_cols[i] >= 0) {
                    const char *drawn_val = csv_get_field(&reader, drawn_cols[i]);
                    if (field_nonzero(drawn_val)) present = 1;
                }
                if (present) {
                    present_cards[card_count++] = card_ids[i];
                }
            }
        } else {
            /* Parse opening hand */
            if (opening_hand_col >= 0) {
                const char *hand = csv_get_field(&reader, opening_hand_col);
                if (hand) {
                    card_count += csv_parse_list(hand, present_cards + card_count, MAX_GAME_CARDS);
                }
            }

            /* Parse drawn cards */
            if (drawn_col >= 0) {
                const char *drawn = csv_get_field(&reader, drawn_col);
                if (drawn) {
                    card_count += csv_parse_list(drawn, present_cards + card_count, MAX_GAME_CARDS);
                }
            }
        }

        labels_process_game(ctx, present_cards, card_count, win);
        games_processed++;

        /* Progress indicator every 100k games */
        if (games_processed % 100000 == 0) {
            fprintf(stderr, "Processed %d games...\n", games_processed);
        }
    }

    free(opening_hand_cols);
    free(drawn_cols);
    free(card_ids);
    csv_close(&reader);
    return games_processed;
}

double labels_smooth_prob(uint64_t wins, uint64_t games) {
    return (double)(wins + BETA_ALPHA) / (double)(games + BETA_ALPHA + BETA_BETA);
}

int labels_compute_pair(LabelContext *ctx, uint64_t card_a, uint64_t card_b, LabelRecord *record) {
    if (!ctx || !record) return -1;

    /* Get card A stats */
    HashEntry *entry_a = hashmap_get(&ctx->card_stats, card_a);
    if (!entry_a) return -1;
    uint64_t n_a = entry_a->n;
    uint64_t w_a = entry_a->w;

    /* Get card B stats */
    HashEntry *entry_b = hashmap_get(&ctx->card_stats, card_b);
    if (!entry_b) return -1;
    uint64_t n_b = entry_b->n;
    uint64_t w_b = entry_b->w;

    /* Get pair stats */
    uint64_t pk = pair_key(card_a, card_b);
    HashEntry *entry_ab = hashmap_get(&ctx->pair_stats, pk);
    if (!entry_ab) return -1;
    uint64_t n_ab = entry_ab->n;
    uint64_t w_ab = entry_ab->w;

    /* Check threshold */
    if (n_ab < MIN_BOTH_PRESENT) return -1;

    uint64_t N = ctx->total_games;
    uint64_t W = ctx->total_wins;

    if (W > N || w_a > n_a || w_b > n_b || w_ab > n_ab) {
        fprintf(stderr, "Error: Invalid win counts for pair %lu,%lu\n",
                (unsigned long)card_a, (unsigned long)card_b);
        return -1;
    }

    int64_t n10 = (int64_t)n_a - (int64_t)n_ab;
    int64_t n01 = (int64_t)n_b - (int64_t)n_ab;
    int64_t n00 = (int64_t)N - (int64_t)n_a - (int64_t)n_b + (int64_t)n_ab;
    int64_t w10 = (int64_t)w_a - (int64_t)w_ab;
    int64_t w01 = (int64_t)w_b - (int64_t)w_ab;
    int64_t w00 = (int64_t)W - (int64_t)w_a - (int64_t)w_b + (int64_t)w_ab;

    if (n10 < 0 || n01 < 0 || n00 < 0 || w10 < 0 || w01 < 0 || w00 < 0) {
        fprintf(stderr, "Error: Negative bucket counts for pair %lu,%lu\n",
                (unsigned long)card_a, (unsigned long)card_b);
        return -1;
    }

    /* Compute the four buckets algebraically */
    record->card_a = card_a;
    record->card_b = card_b;

    /* n11, w11: both present */
    record->n11 = n_ab;
    record->w11 = w_ab;

    /* n10, w10: A present, B not present */
    record->n10 = (uint64_t)n10;
    record->w10 = (uint64_t)w10;

    /* n01, w01: A not present, B present */
    record->n01 = (uint64_t)n01;
    record->w01 = (uint64_t)w01;

    /* n00, w00: neither present */
    record->n00 = (uint64_t)n00;
    record->w00 = (uint64_t)w00;

    if (record->n11 + record->n10 + record->n01 + record->n00 != N ||
        record->w11 + record->w10 + record->w01 + record->w00 != W) {
        fprintf(stderr, "Error: Bucket totals mismatch for pair %lu,%lu\n",
                (unsigned long)card_a, (unsigned long)card_b);
        return -1;
    }

    /* Compute smoothed probabilities */
    record->p11 = labels_smooth_prob(record->w11, record->n11);
    record->p10 = labels_smooth_prob(record->w10, record->n10);
    record->p01 = labels_smooth_prob(record->w01, record->n01);
    record->p00 = labels_smooth_prob(record->w00, record->n00);

    /* Compute synergy delta */
    record->syn_delta = record->p11 - record->p10 - record->p01 + record->p00;

    return 0;
}

/* Iterator context for writing labels */
typedef struct {
    FILE *fp;
    LabelContext *ctx;
    int count;
} WriteContext;

static void write_pair_callback(uint64_t pk, uint64_t n, uint64_t w, void *user_data) {
    (void)n; (void)w;  /* Unused */

    WriteContext *wctx = (WriteContext *)user_data;
    if (!wctx || !wctx->fp || !wctx->ctx) return;

    uint64_t card_a, card_b;
    pair_decode(pk, &card_a, &card_b);

    LabelRecord record;
    if (labels_compute_pair(wctx->ctx, card_a, card_b, &record) == 0) {
        fprintf(wctx->fp, "%lu,%lu,%lu,%lu,%.6f,%lu,%lu,%.6f,%lu,%lu,%.6f,%lu,%lu,%.6f,%.6f\n",
                (unsigned long)record.card_a, (unsigned long)record.card_b,
                (unsigned long)record.n11, (unsigned long)record.w11, record.p11,
                (unsigned long)record.n10, (unsigned long)record.w10, record.p10,
                (unsigned long)record.n01, (unsigned long)record.w01, record.p01,
                (unsigned long)record.n00, (unsigned long)record.w00, record.p00,
                record.syn_delta);
        wctx->count++;
    }
}

int labels_write_csv(LabelContext *ctx, const char *output_path) {
    if (!ctx || !output_path) return -1;

    FILE *fp = fopen(output_path, "w");
    if (!fp) {
        fprintf(stderr, "Error: Cannot create output file: %s\n", output_path);
        return -1;
    }

    /* Write header */
    fprintf(fp, "card_a,card_b,n11,w11,p11,n10,w10,p10,n01,w01,p01,n00,w00,p00,syn_delta\n");

    WriteContext wctx = { fp, ctx, 0 };
    hashmap_iterate(&ctx->pair_stats, write_pair_callback, &wctx);

    fclose(fp);
    return wctx.count;
}

static void iterate_pair_callback(uint64_t pk, uint64_t n, uint64_t w, void *user_data) {
    (void)n; (void)w;

    void **args = (void **)user_data;
    LabelContext *ctx = (LabelContext *)args[0];
    LabelCallback callback = (LabelCallback)args[1];
    void *cb_data = args[2];

    uint64_t card_a, card_b;
    pair_decode(pk, &card_a, &card_b);

    LabelRecord record;
    if (labels_compute_pair(ctx, card_a, card_b, &record) == 0) {
        callback(&record, cb_data);
    }
}

void labels_iterate(LabelContext *ctx, LabelCallback callback, void *user_data) {
    if (!ctx || !callback) return;

    void *args[3] = { ctx, (void *)callback, user_data };
    hashmap_iterate(&ctx->pair_stats, iterate_pair_callback, args);
}
