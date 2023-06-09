"""
Main

Contains the pipeline to train and evaluate the model.

Date: 09.07.2023
"""

import random
import pickle
from Perceptron import Perceptron
from Corpus import Corpus
from Evaluator import Evaluator
from tqdm import tqdm
from typing import Any


def save_model(model: Any, filepath: str):
    """
    Wrapper to save the model in a pickle
    :param model: Model as an object
    :param filepath: Path to the file it should be saved in
    """
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)


def load_model(filepath: str) -> Any:
    """
    Wrapper to load a model from a pickle
    :param filepath: Path to the file
    :return: The model stored in the pickle, as its corresponding object type
    """
    with open(filepath, 'rb') as f:
        return pickle.load(f)


if __name__ == "__main__":
    EPOCHS = 3  # Define the number of training iterations

    # Load corpus
    data = Corpus.read_file("data/menu_train.txt")  # comment out this line if loading from json
    dev = Corpus.read_file("data/menu_dev.txt")

    # create corpus from training data
    # choose which features to exclude: ['name', 'type', 'loc', 'menu']
    # chose feature extraction method: 'bow' for bag of words or 'emb' for embeddings
    corpus = Corpus(train_data=data, test_data=dev, exclude_feats=None, method='bow')

    # load corpus from json
    # corpus = Corpus(test_data=dev, load_mapping="models/feature_mapping.json", method='bow')

    # initialize a perceptron for each price category
    perceptrons = [Perceptron(corpus.num_feats, i) for i in range(1, 5)]  # Assuming 4 price categories
    # collect training data as a list of tuple (feature_vector, gold_label)
    train_data = [(corpus.get_dense_features(restaurant), restaurant.gold_label) for restaurant in corpus.train_data]

    print("\nTraining the model...")
    for perceptron in tqdm(perceptrons):
        perceptron.train(train_data, EPOCHS)

    # load existing models
    # perceptrons = [load_model("models/all_feats_3_ep_perc1"),
    #                load_model("models/all_feats_3_ep_perc2"),
    #                load_model("models/all_feats_3_ep_perc3"),
    #                load_model("models/all_feats_3_ep_perc4")]

    # Make predictions
    for restaurant in corpus.test_data:
        dense_features = corpus.get_dense_features(restaurant)
        predictions = [perceptron.predict(dense_features) for perceptron in perceptrons]
        # Get the predicted class (1-indexed)
        predicted_class = predictions.index(max(predictions)) + 1
        # Set the predicted label
        restaurant.set_predicted_label(predicted_class)

    # Cross-validation
    # K = 5  # number of splits for cross-validation
    # fold_size = len(data) // K
    f1_scores = []
    correlations = []
    """
    random.shuffle(data)

    for i in range(K):
        dev = data[i*fold_size: (i+1)*fold_size]
        train = data[:i*fold_size] + data[(i+1)*fold_size:]
        corpus = Corpus(train, exclude_feats=['name'])
        corpus.set_test_data(dev)

        # Get the number of features
        num_features = corpus.num_feats

        # Initialize perceptron for each class
        perceptrons = [Perceptron(num_features, i) for i in range(1, 5)]  # Assuming 4 price categories

        # Train perceptrons
        train_data = [(corpus.get_dense_features(restaurant), restaurant.gold_label) for restaurant in corpus.train_data]
        for perceptron in tqdm(perceptrons):
            perceptron.train(train_data, EPOCHS)

        # Make predictions
        for restaurant in corpus.test_data:
            dense_features = corpus.get_dense_features(restaurant)
            predictions = [perceptron.predict(dense_features) for perceptron in perceptrons]
            # Get the predicted class (1-indexed)
            predicted_class = predictions.index(max(predictions)) + 1
            # Set the predicted label
            restaurant.set_predicted_label(predicted_class)
    """

    # Evaluate perceptrons
    y_true = []
    y_pred = []
    for restaurant in corpus.test_data:
        # Check if gold_label and predicted_label are not None
        if restaurant.gold_label is None:
            print(f"Gold label for restaurant {restaurant.name} is None.")
            continue
        if restaurant.pred_label is None:
            print(f"Predicted label for restaurant {restaurant.name} is None.")
            continue

        y_true.append(restaurant.gold_label)
        y_pred.append(restaurant.pred_label)

    # For testing if the labels are assigned correctly
    # corpus.print_labels()

    # Set up evaluator
    evaluator = Evaluator(corpus)
    
    if len(set(y_true)) == 1 or len(set(y_pred)) == 1:
        print("Insufficient variation in the data to calculate correlation.")
    else:
        correlation = evaluator.evaluate_correlation()
        correlations.append(correlation)

    f1_score = evaluator.evaluate_f1_score()
    f1_scores.append(f1_score)

average_f1_score = sum(f1_scores) / len(f1_scores)
average_correlation = sum(correlations) / len(correlations)

print()
print(f"Average F1 Score across all folds: {average_f1_score:.2f}")
print(f"Average Correlation across all folds: {average_correlation:.2f}")

print()
for p in perceptrons:
    save_model(p, "out/emb_allfeats_3ep_perc" + str(p.tar_label))
    print(f"Perceptron {p.tar_label} saved")
