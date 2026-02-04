#include "train.h"
#include "csv.h"
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <math.h>
#include <time.h>

int model_init(SynergyModel *model) {
    if (!model) return -1;

    model->capacity = 1024;
    model->cards = malloc(model->capacity * sizeof(CardModel));
    if (!model->cards) return -1;

    model->num_cards = 0;
    model->global_bias = 0.0f;
    model->embed_dim = EMBED_DIM;

    return 0;
}

void model_free(SynergyModel *model) {
    if (model && model->cards) {
        free(model->cards);
        model->cards = NULL;
        model->num_cards = 0;
    }
}

/* Find card in model */
static CardModel *model_find_card(SynergyModel *model, uint64_t card_id) {
    for (size_t i = 0; i < model->num_cards; i++) {
        if (model->cards[i].card_id == card_id) {
            return &model->cards[i];
        }
    }
    return NULL;
}

CardModel *model_get_card(SynergyModel *model, uint64_t card_id) {
    if (!model) return NULL;

    /* Check if already exists */
    CardModel *existing = model_find_card(model, card_id);
    if (existing) return existing;

    /* Grow if needed */
    if (model->num_cards >= model->capacity) {
        size_t new_cap = model->capacity * 2;
        CardModel *new_cards = realloc(model->cards, new_cap * sizeof(CardModel));
        if (!new_cards) return NULL;
        model->cards = new_cards;
        model->capacity = new_cap;
    }

    /* Initialize new card */
    CardModel *card = &model->cards[model->num_cards++];
    card->card_id = card_id;
    card->bias = 0.0f;

    /* Initialize embedding with small random values */
    for (int i = 0; i < EMBED_DIM; i++) {
        card->embedding[i] = ((float)rand() / RAND_MAX - 0.5f) * 0.1f;
    }

    return card;
}

float model_predict(SynergyModel *model, uint64_t card_a, uint64_t card_b) {
    if (!model) return 0.0f;

    CardModel *ma = model_find_card(model, card_a);
    CardModel *mb = model_find_card(model, card_b);

    if (!ma || !mb) return model->global_bias;

    /* Compute dot product */
    float dot = 0.0f;
    for (int i = 0; i < model->embed_dim; i++) {
        dot += ma->embedding[i] * mb->embedding[i];
    }

    return dot + ma->bias + mb->bias + model->global_bias;
}

int model_save(SynergyModel *model, const char *path) {
    if (!model || !path) return -1;

    FILE *fp = fopen(path, "wb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot create model file: %s\n", path);
        return -1;
    }

    /* Write header */
    uint32_t magic = MODEL_MAGIC;
    uint32_t version = MODEL_VERSION;
    uint32_t dim = (uint32_t)model->embed_dim;
    uint32_t num_cards = (uint32_t)model->num_cards;

    fwrite(&magic, sizeof(magic), 1, fp);
    fwrite(&version, sizeof(version), 1, fp);
    fwrite(&dim, sizeof(dim), 1, fp);
    fwrite(&num_cards, sizeof(num_cards), 1, fp);

    /* Write cards */
    for (size_t i = 0; i < model->num_cards; i++) {
        CardModel *card = &model->cards[i];
        fwrite(&card->card_id, sizeof(card->card_id), 1, fp);
        fwrite(&card->bias, sizeof(card->bias), 1, fp);
        fwrite(card->embedding, sizeof(float), dim, fp);
    }

    /* Write global bias */
    fwrite(&model->global_bias, sizeof(model->global_bias), 1, fp);

    fclose(fp);
    return 0;
}

int model_load(SynergyModel *model, const char *path) {
    if (!model || !path) return -1;

    FILE *fp = fopen(path, "rb");
    if (!fp) {
        fprintf(stderr, "Error: Cannot open model file: %s\n", path);
        return -1;
    }

    /* Read header */
    uint32_t magic, version, dim, num_cards;

    if (fread(&magic, sizeof(magic), 1, fp) != 1 ||
        fread(&version, sizeof(version), 1, fp) != 1 ||
        fread(&dim, sizeof(dim), 1, fp) != 1 ||
        fread(&num_cards, sizeof(num_cards), 1, fp) != 1) {
        fclose(fp);
        return -1;
    }

    if (magic != MODEL_MAGIC || version != MODEL_VERSION) {
        fprintf(stderr, "Error: Invalid model file format\n");
        fclose(fp);
        return -1;
    }

    if (dim > EMBED_DIM) {
        fprintf(stderr, "Error: Model has larger embedding dimension than supported\n");
        fclose(fp);
        return -1;
    }

    /* Initialize model */
    model->embed_dim = (int)dim;
    model->capacity = num_cards > 1024 ? num_cards : 1024;
    model->cards = malloc(model->capacity * sizeof(CardModel));
    if (!model->cards) {
        fclose(fp);
        return -1;
    }
    model->num_cards = num_cards;

    /* Read cards */
    for (uint32_t i = 0; i < num_cards; i++) {
        CardModel *card = &model->cards[i];
        if (fread(&card->card_id, sizeof(card->card_id), 1, fp) != 1 ||
            fread(&card->bias, sizeof(card->bias), 1, fp) != 1 ||
            fread(card->embedding, sizeof(float), dim, fp) != dim) {
            free(model->cards);
            fclose(fp);
            return -1;
        }
        /* Zero out unused dimensions */
        for (int j = (int)dim; j < EMBED_DIM; j++) {
            card->embedding[j] = 0.0f;
        }
    }

    /* Read global bias */
    if (fread(&model->global_bias, sizeof(model->global_bias), 1, fp) != 1) {
        free(model->cards);
        fclose(fp);
        return -1;
    }

    fclose(fp);
    return 0;
}

int traindata_init(TrainData *data) {
    if (!data) return -1;

    data->capacity = 65536;
    data->samples = malloc(data->capacity * sizeof(TrainSample));
    if (!data->samples) return -1;

    data->count = 0;
    return 0;
}

void traindata_free(TrainData *data) {
    if (data && data->samples) {
        free(data->samples);
        data->samples = NULL;
        data->count = 0;
    }
}

int traindata_add(TrainData *data, uint64_t card_a, uint64_t card_b,
                  double syn_delta, double weight) {
    if (!data) return -1;

    if (data->count >= data->capacity) {
        size_t new_cap = data->capacity * 2;
        TrainSample *new_samples = realloc(data->samples, new_cap * sizeof(TrainSample));
        if (!new_samples) return -1;
        data->samples = new_samples;
        data->capacity = new_cap;
    }

    TrainSample *s = &data->samples[data->count++];
    s->card_a = card_a;
    s->card_b = card_b;
    s->syn_delta = syn_delta;
    s->weight = weight;

    return 0;
}

int traindata_load(TrainData *data, const char *labels_csv_path) {
    if (!data || !labels_csv_path) return -1;

    CsvReader reader;
    if (csv_open(&reader, labels_csv_path) != 0) {
        fprintf(stderr, "Error: Cannot open labels file: %s\n", labels_csv_path);
        return -1;
    }

    /* Read header */
    if (csv_next_row(&reader) != 1) {
        csv_close(&reader);
        return -1;
    }

    int card_a_col = csv_find_column(&reader, "card_a");
    int card_b_col = csv_find_column(&reader, "card_b");
    int syn_delta_col = csv_find_column(&reader, "syn_delta");
    int n11_col = csv_find_column(&reader, "n11");

    if (card_a_col < 0 || card_b_col < 0 || syn_delta_col < 0) {
        fprintf(stderr, "Error: Missing required columns in labels file\n");
        csv_close(&reader);
        return -1;
    }

    int count = 0;
    while (csv_next_row(&reader) == 1) {
        const char *a_str = csv_get_field(&reader, card_a_col);
        const char *b_str = csv_get_field(&reader, card_b_col);
        const char *syn_str = csv_get_field(&reader, syn_delta_col);

        if (!a_str || !b_str || !syn_str) continue;

        uint64_t card_a = strtoull(a_str, NULL, 10);
        uint64_t card_b = strtoull(b_str, NULL, 10);
        double syn_delta = strtod(syn_str, NULL);

        /* Weight by n11 (number of co-occurrences) */
        double weight = 1.0;
        if (n11_col >= 0) {
            const char *n11_str = csv_get_field(&reader, n11_col);
            if (n11_str) {
                weight = strtod(n11_str, NULL);
                if (weight > MAX_WEIGHT) weight = MAX_WEIGHT;
                if (weight < 1.0) weight = 1.0;
            }
        }

        if (card_a > 0 && card_b > 0) {
            traindata_add(data, card_a, card_b, syn_delta, weight);
            count++;
        }
    }

    csv_close(&reader);
    return count;
}

void traindata_shuffle(TrainData *data) {
    if (!data || data->count < 2) return;

    for (size_t i = data->count - 1; i > 0; i--) {
        size_t j = (size_t)(rand() % (int)(i + 1));
        TrainSample tmp = data->samples[i];
        data->samples[i] = data->samples[j];
        data->samples[j] = tmp;
    }
}

double train_model(SynergyModel *model, TrainData *data,
                   double learning_rate, double l2_reg, int epochs) {
    if (!model || !data || data->count == 0) return -1.0;

    srand((unsigned int)time(NULL));

    /* Ensure all cards have model entries */
    for (size_t i = 0; i < data->count; i++) {
        model_get_card(model, data->samples[i].card_a);
        model_get_card(model, data->samples[i].card_b);
    }

    double total_weight = 0.0;
    for (size_t i = 0; i < data->count; i++) {
        total_weight += data->samples[i].weight;
    }

    double mse = 0.0;
    float lr = (float)learning_rate;
    float reg = (float)l2_reg;

    for (int epoch = 0; epoch < epochs; epoch++) {
        traindata_shuffle(data);
        double epoch_loss = 0.0;
        double epoch_weight = 0.0;

        for (size_t i = 0; i < data->count; i++) {
            TrainSample *s = &data->samples[i];

            CardModel *ma = model_find_card(model, s->card_a);
            CardModel *mb = model_find_card(model, s->card_b);

            if (!ma || !mb) continue;

            /* Forward pass */
            float dot = 0.0f;
            for (int j = 0; j < model->embed_dim; j++) {
                dot += ma->embedding[j] * mb->embedding[j];
            }
            float pred = dot + ma->bias + mb->bias + model->global_bias;

            /* Compute error */
            float target = (float)s->syn_delta;
            float error = pred - target;
            float w = (float)s->weight;

            epoch_loss += (double)(error * error * w);
            epoch_weight += s->weight;

            /* Backward pass (SGD with L2 regularization) */
            float grad = 2.0f * error * w / (float)total_weight;

            /* Update biases */
            ma->bias -= lr * (grad + reg * ma->bias);
            mb->bias -= lr * (grad + reg * mb->bias);
            model->global_bias -= lr * grad;

            /* Update embeddings */
            for (int j = 0; j < model->embed_dim; j++) {
                float ga = grad * mb->embedding[j] + reg * ma->embedding[j];
                float gb = grad * ma->embedding[j] + reg * mb->embedding[j];
                ma->embedding[j] -= lr * ga;
                mb->embedding[j] -= lr * gb;
            }
        }

        mse = epoch_loss / epoch_weight;

        if ((epoch + 1) % 10 == 0) {
            fprintf(stderr, "Epoch %d/%d, MSE: %.6f\n", epoch + 1, epochs, mse);
        }
    }

    return mse;
}
