import numpy as np
import tensorflow as tf

N=8
inner_frac = 0.5
threshold = 0.2
min_ink = 0.25

def grid_center_extract_batch(
    images,  # shape (n, height, width)
    inner_frac=0.5,
    threshold=0.2,
    min_ink_fraction=0.01
):
    n, height, width = images.shape

    cell_width = width // N
    cell_height = height // N

    output = np.zeros((n, N, N), dtype=bool)

    for r in range(N):
        for c in range(N):
            cell_y_0 = r * cell_height
            cell_x_0 = c * cell_width

            cell = images[:, cell_y_0:cell_y_0 + cell_height, cell_x_0:cell_x_0 + cell_width]

            # Inner window (basically the sensor's area of sensoring)
            window_width = max(1, int(cell_width * inner_frac))
            window_height = max(1, int(cell_height * inner_frac))

            window_x_0 = (cell_width - window_width) // 2
            window_y_0 = (cell_height - window_height) // 2

            window = cell[:, window_y_0:window_y_0 + window_height, window_x_0:window_x_0 + window_width]

            ink = window > threshold
            frac = ink.mean(axis=(1, 2))

            output[:, r, c] = frac >= min_ink_fraction

    return output


model = tf.keras.models.load_model("mnist_grid_model.keras")

'One test'
(_, _), (x_test, y_test) = tf.keras.datasets.mnist.load_data()
x_test = x_test.astype(np.float32) / 255.0

sample = x_test[0:1]
label = y_test[0]

sample_bool = grid_center_extract_batch(
    sample,
    inner_frac=inner_frac,
    threshold=threshold,
    min_ink_fraction=min_ink
)

sample_feat = sample_bool.reshape(-1, N * N).astype(np.float32)

prediction = model.predict(sample_feat)
predicted_digit = np.argmax(prediction, axis=1)[0]

print("True label:", label)
print("Predicted:", predicted_digit)