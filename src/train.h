#ifndef TRAIN_H
#define TRAIN_H

#include <stdint.h>
#include <stddef.h>

/* Model parameters */
#define EMBED_DIM 16
#define DEFAULT_LEARNING_RATE 0.01
#define DEFAULT_L2_REG 0.001
#define DEFAULT_EPOCHS 50
#define MAX_WEIGHT 1000.0

/* Model binary format */
#define MODEL_MAGIC 0x53594E31  /* "SYN1" */
#define MODEL_VERSION 1

/* Card embedding and bias */
typedef struct {
    uint64_t card_id;
    float bias;
    float embedding[EMBED_DIM];
} CardModel;

/* Full model */
typedef struct {
    CardModel *cards;
    size_t num_cards;
    size_t capacity;
    float global_bias;
    int embed_dim;
} SynergyModel;

/* Training sample (loaded from labels CSV) */
typedef struct {
    uint64_t card_a;
    uint64_t card_b;
    double syn_delta;
    double weight;
} TrainSample;

/* Training data */
typedef struct {
    TrainSample *samples;
    size_t count;
    size_t capacity;
} TrainData;

/* Initialize model. Returns 0 on success. */
int model_init(SynergyModel *model);

/* Free model memory. */
void model_free(SynergyModel *model);

/* Get or create card model entry. Returns pointer or NULL on error. */
CardModel *model_get_card(SynergyModel *model, uint64_t card_id);

/* Predict synergy between two cards. */
float model_predict(SynergyModel *model, uint64_t card_a, uint64_t card_b);

/* Save model to binary file. Returns 0 on success. */
int model_save(SynergyModel *model, const char *path);

/* Load model from binary file. Returns 0 on success. */
int model_load(SynergyModel *model, const char *path);

/* Initialize training data. Returns 0 on success. */
int traindata_init(TrainData *data);

/* Free training data. */
void traindata_free(TrainData *data);

/* Load training data from labels CSV. Returns number of samples, -1 on error. */
int traindata_load(TrainData *data, const char *labels_csv_path);

/* Add a training sample. */
int traindata_add(TrainData *data, uint64_t card_a, uint64_t card_b,
                  double syn_delta, double weight);

/* Train model on data. Returns final MSE. */
double train_model(SynergyModel *model, TrainData *data,
                   double learning_rate, double l2_reg, int epochs);

/* Shuffle training data. */
void traindata_shuffle(TrainData *data);

#endif /* TRAIN_H */
