import numpy as np
import tensorflow as tf


# Config
GRID_SIZE = 8
INNER_FRAC = 0.5
PIXEL_THRESHOLD = 0.2
MIN_INK_FRACTION = 0.25

EPOCHS = 5
BATCH_SIZE = 128
MODEL_PATH = "ml_model.keras"


# Preprocessing
def grid_center_extract_batch(
    images: np.ndarray,
    grid_width: int,
    grid_height: int,
    inner_frac: float = 0.5,
    threshold: float = 0.2,
    min_ink_fraction: float = 0.01,
) -> np.ndarray:
    """
    Converting grayscale images (n, height, width)
    Into bool grid (n, GRID_SIZE, GRID_SIZE)

    Each output cell becomes True if enough pixels in the inner area
    of the corresponding image cell exceed the threshold.
    """
    n, height, width = images.shape

    cell_width = width // grid_width
    cell_height = height // grid_height

    output = np.zeros((n, grid_height, grid_width), dtype=bool)

    for r in range(grid_height):
        for c in range(grid_width):
            y0 = r * cell_height
            x0 = c * cell_width

            cell = images[:, y0:y0 + cell_height, x0:x0 + cell_width]

            window_width = max(1, int(cell_width * inner_frac))
            window_height = max(1, int(cell_height * inner_frac))

            wx0 = (cell_width - window_width) // 2
            wy0 = (cell_height - window_height) // 2

            window = cell[:, wy0:wy0 + window_height, wx0:wx0 + window_width]

            ink_mask = window > threshold
            ink_fraction = ink_mask.mean(axis=(1, 2))

            output[:, r, c] = ink_fraction >= min_ink_fraction

    return output


def preprocess_images(
    x: np.ndarray,
    grid_size: int,
    inner_frac: float,
    pixel_threshold: float,
    min_ink_fraction: float,
) -> np.ndarray:
    """
    Normalizing images, then
    Flattening them into N x N feature vectors.
    """
    x = x.astype(np.float32) / 255.0

    x_bool = grid_center_extract_batch(
        x,
        grid_width=grid_size,
        grid_height=grid_size,
        inner_frac=inner_frac,
        threshold=pixel_threshold,
        min_ink_fraction=min_ink_fraction,
    )

    x_feat = x_bool.reshape(-1, grid_size * grid_size).astype(np.float32)
    return x_feat


# Model
def build_model(input_size: int, num_classes: int = 10) -> tf.keras.Model:
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(input_size,)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(num_classes, activation="softmax"),
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )

    return model


# Evaluation
def print_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> None:
    cm = tf.math.confusion_matrix(y_true, y_pred)
    print("Confusion matrix:")
    print(cm.numpy())


def main():
    # loading dataset
    (x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()

    # Preprocess into GRID_SIZE x GRID_SIZE
    x_train_feat = preprocess_images(
        x_train,
        grid_size=GRID_SIZE,
        inner_frac=INNER_FRAC,
        pixel_threshold=PIXEL_THRESHOLD,
        min_ink_fraction=MIN_INK_FRACTION,
    )

    x_test_feat = preprocess_images(
        x_test,
        grid_size=GRID_SIZE,
        inner_frac=INNER_FRAC,
        pixel_threshold=PIXEL_THRESHOLD,
        min_ink_fraction=MIN_INK_FRACTION,
    )

    # Building and training model
    model = build_model(input_size=GRID_SIZE * GRID_SIZE)

    model.fit(
        x_train_feat,
        y_train,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        validation_split=0.1,
        verbose=1,
    )

    # Evaluate
    loss, accuracy = model.evaluate(x_test_feat, y_test, verbose=0)

    # Save
    model.save(MODEL_PATH)

    # Prediction and confusion matrix
    predictions = model.predict(x_test_feat, verbose=0)
    y_pred = np.argmax(predictions, axis=1)

    print(f"Grid size: {GRID_SIZE}x{GRID_SIZE}")
    print(f"Test loss: {loss}")
    print(f"Test accuracy: {accuracy}")
    print_confusion_matrix(y_test, y_pred)
    print(f"Model saved to: {MODEL_PATH}")


main()