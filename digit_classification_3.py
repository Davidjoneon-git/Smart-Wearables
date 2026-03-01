import tensorflow as tf
import numpy as np

is_ghosting = True

def add_ghosting(X):
    Y = X.copy()

    a = X[:, :-1, :-1]   # top-left
    b = X[:, :-1,  1:]   # top-right
    c = X[:,  1:, :-1]   # bottom-left
    d = X[:,  1:,  1:]   # bottom-right

    Y[:, :-1, :-1] |= (b & c & d)
    Y[:, :-1,  1:] |= (a & c & d)
    Y[:,  1:, :-1] |= (a & b & d)
    Y[:,  1:,  1:] |= (a & b & c)

    return Y

def grid_center_extract_batch(
    images,  # shape (n, height, width)
    grid_width,
    grid_height,
    inner_frac=0.5,
    threshold=0.2,
    min_ink_fraction=0.01
):
    n, height, width = images.shape

    cell_width = width // grid_width
    cell_height = height // grid_height

    output = np.zeros((n, grid_height, grid_width), dtype=bool)

    for r in range(grid_height):
        for c in range(grid_width):
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

    if (is_ghosting):
        return add_ghosting(output)
    
    return output

# Loading dataset from TensorFlow
(x_train, y_train), (x_test, y_test) = tf.keras.datasets.mnist.load_data()

# Normalize
x_train = x_train.astype(np.float32) / 255.0
x_test  = x_test.astype(np.float32) / 255.0


#min % that needs to be "sensed" to be "pressed"
mins = 0.5
ns = [8,9,10,11,12,13,14,15,16]
accuracies = []
losses = []
tests = []

for n in ns:    
    x_train_bool = grid_center_extract_batch(
        x_train,
        grid_width=n,
        grid_height=n,
        inner_frac=0.5,
        threshold=0.2,
        min_ink_fraction=mins
    )
    x_test_bool = grid_center_extract_batch(
        x_test,
        grid_width=n,
        grid_height=n,
        inner_frac=0.5,
        threshold=0.2,
        min_ink_fraction=mins
    )
    # Flatten grid
    # Feature vector of length n*n
    x_train_feat = x_train_bool.reshape(-1, n * n).astype(np.float32)
    x_test_feat  = x_test_bool.reshape(-1, n * n).astype(np.float32)
    # Build model
    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(n * n,)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(10, activation='softmax')
    ])
    # Compiling
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )
    # Training
    model.fit(
        x_train_feat,
        y_train,
        epochs=5,
        batch_size=128,
        validation_split=0.1
    )
    # Evaluation
    test_loss, test_acc = model.evaluate(x_test_feat, y_test)
    accuracies.append(test_acc)
    print("Done", n)    

for i in range(len(ns)):
    print(f"---------------------------------------------\n{ns[i]} x {ns[i]} with Ghosting\nAccuracy: {accuracies[i]}")