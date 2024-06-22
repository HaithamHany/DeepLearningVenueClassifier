import joblib
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import RandomizedSearchCV
import tensorflow as tf
from . import Utils
from Config import config


class SupervisedImageClassifier:
    def __init__(self, preprocessing, label_encoder):
        """
        Initialize the SupervisedImageClassifier class.
        """
        self.preprocessing = preprocessing
        self.label_encoder = label_encoder
        self.trained_model = None

    def load_model(self, model_filename):
       self.trained_model = Utils.load_model(model_filename, config)

    def train_classifier(self, X_train, y_train):
        """
        Train a Decision Tree Classifier with specified hyperparameters.
        Perform a randomized search over the provided hyperparameters.
        """
        X_train_tensor = tf.convert_to_tensor(X_train, dtype=tf.float32)
        y_train_tensor = tf.convert_to_tensor(y_train, dtype=tf.int64)
        augmented_dataset = self.preprocessing.augment_dataset(X_train_tensor, y_train_tensor)

        X_train_augmented = []
        y_train_augmented = []
        for batch in augmented_dataset:
            augmented_images, augmented_labels = batch
            X_train_augmented.append(augmented_images.numpy())
            y_train_augmented.append(augmented_labels.numpy())

        X_train_augmented = np.concatenate(X_train_augmented)
        y_train_augmented = np.concatenate(y_train_augmented)

        # Flatten images
        X_train_augmented_flat = self.preprocessing.flatten_images(X_train_augmented)

        # Train the classifier
        param_distributions = {
            'max_depth': config.get("max_depth"),
            'min_samples_split': config.get("min_samples_split"),
            'min_samples_leaf': config.get("min_samples_leaf"),
        }

        clf = DecisionTreeClassifier(random_state=config.get("random_state"))

        randomized_search = RandomizedSearchCV(
            estimator=clf,
            param_distributions=param_distributions,
            n_iter=config.get("n_iter", 5),
            scoring='accuracy',
            n_jobs=config.get("n_jobs", -1),
            cv=config.get("cv", 3),
            verbose=1,
            random_state=config.get("random_state")
        )

        randomized_search.fit(X_train_augmented_flat, y_train_augmented)

        # Save the best trained model
        self.trained_model = randomized_search.best_estimator_
        joblib.dump(self.trained_model, 'supervised_model.pkl')

        best_params = randomized_search.best_params_
        best_score = randomized_search.best_score_

        print(f"Best Hyperparameters: {best_params}")
        print(f"Best Cross-Validation Accuracy: {best_score}")

    def evaluate_classifier(self, X_test, y_test):
        """
        Evaluate the trained classifier on the test set.
        """
        Utils.evaluate_classifier(self.trained_model, X_test, y_test, self.preprocessing, self.label_encoder)
