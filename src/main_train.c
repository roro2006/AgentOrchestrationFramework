#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "train.h"

static void print_usage(const char *program) {
    fprintf(stderr, "Usage: %s <labels.csv> <output_model.bin> [options]\n", program);
    fprintf(stderr, "\n");
    fprintf(stderr, "Arguments:\n");
    fprintf(stderr, "  labels.csv       - Synergy labels CSV file (from labels program)\n");
    fprintf(stderr, "  output_model.bin - Output binary model file\n");
    fprintf(stderr, "\n");
    fprintf(stderr, "Options:\n");
    fprintf(stderr, "  -lr <rate>       - Learning rate (default: %.4f)\n", DEFAULT_LEARNING_RATE);
    fprintf(stderr, "  -reg <lambda>    - L2 regularization (default: %.4f)\n", DEFAULT_L2_REG);
    fprintf(stderr, "  -epochs <n>      - Number of epochs (default: %d)\n", DEFAULT_EPOCHS);
    fprintf(stderr, "\n");
    fprintf(stderr, "Example:\n");
    fprintf(stderr, "  %s data/out/labels_premier.csv data/out/model_premier.bin\n", program);
    fprintf(stderr, "  %s data/out/labels_premier.csv data/out/model_premier.bin -epochs 100 -lr 0.005\n", program);
}

int main(int argc, char *argv[]) {
    if (argc < 3) {
        print_usage(argv[0]);
        return 1;
    }

    const char *labels_path = argv[1];
    const char *output_path = argv[2];

    /* Parse optional arguments */
    double learning_rate = DEFAULT_LEARNING_RATE;
    double l2_reg = DEFAULT_L2_REG;
    int epochs = DEFAULT_EPOCHS;

    for (int i = 3; i < argc - 1; i++) {
        if (strcmp(argv[i], "-lr") == 0) {
            learning_rate = strtod(argv[i + 1], NULL);
            i++;
        } else if (strcmp(argv[i], "-reg") == 0) {
            l2_reg = strtod(argv[i + 1], NULL);
            i++;
        } else if (strcmp(argv[i], "-epochs") == 0) {
            epochs = atoi(argv[i + 1]);
            i++;
        }
    }

    fprintf(stderr, "=== Model Training ===\n");
    fprintf(stderr, "Labels file: %s\n", labels_path);
    fprintf(stderr, "Output:      %s\n", output_path);
    fprintf(stderr, "Learning rate: %.6f\n", learning_rate);
    fprintf(stderr, "L2 regularization: %.6f\n", l2_reg);
    fprintf(stderr, "Epochs: %d\n", epochs);
    fprintf(stderr, "Embedding dimension: %d\n", EMBED_DIM);
    fprintf(stderr, "\n");

    /* Load training data */
    TrainData data;
    if (traindata_init(&data) != 0) {
        fprintf(stderr, "Error: Failed to initialize training data\n");
        return 1;
    }

    fprintf(stderr, "Loading labels from %s...\n", labels_path);
    int samples_loaded = traindata_load(&data, labels_path);
    if (samples_loaded < 0) {
        fprintf(stderr, "Error: Failed to load training data\n");
        traindata_free(&data);
        return 1;
    }
    fprintf(stderr, "Loaded %d training samples\n\n", samples_loaded);

    if (samples_loaded == 0) {
        fprintf(stderr, "Error: No training samples loaded\n");
        traindata_free(&data);
        return 1;
    }

    /* Initialize model */
    SynergyModel model;
    if (model_init(&model) != 0) {
        fprintf(stderr, "Error: Failed to initialize model\n");
        traindata_free(&data);
        return 1;
    }

    /* Train model */
    fprintf(stderr, "Training model...\n");
    double final_mse = train_model(&model, &data, learning_rate, l2_reg, epochs);

    fprintf(stderr, "\nTraining complete:\n");
    fprintf(stderr, "  Final MSE: %.6f\n", final_mse);
    fprintf(stderr, "  Model cards: %zu\n", model.num_cards);
    fprintf(stderr, "  Global bias: %.6f\n", model.global_bias);
    fprintf(stderr, "\n");

    /* Save model */
    fprintf(stderr, "Saving model to %s...\n", output_path);
    if (model_save(&model, output_path) != 0) {
        fprintf(stderr, "Error: Failed to save model\n");
        model_free(&model);
        traindata_free(&data);
        return 1;
    }

    /* Cleanup */
    model_free(&model);
    traindata_free(&data);

    fprintf(stderr, "Done!\n");
    return 0;
}
