import numpy as np
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix

MODEL_PATH = "multi-class_classifier_model.keras"

def main():
    x0 = np.load("0.npy")  # label 0
    x1 = np.load("1.npy")  # label 1
    x2 = np.load("2.npy")  # label 2

    y0 = np.full(x0.shape[0], 0)
    y1 = np.full(x1.shape[0], 1)
    y2 = np.full(x2.shape[0], 2)

    x = np.concatenate([x0, x1, x2], axis=0)
    y = np.concatenate([y0, y1, y2], axis=0)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    x_train = x_train.reshape(x_train.shape[0], -1)
    x_test = x_test.reshape(x_test.shape[0], -1)

    model = tf.keras.Sequential([
        tf.keras.layers.Input(shape=(x_train.shape[1],)),
        tf.keras.layers.Dense(128, activation="relu"),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(3, activation="softmax")  # 3 classes
    ])

    model.compile(
        optimizer="adam",
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"]
    )

    model.fit(
        x_train, y_train,
        validation_data=(x_test, y_test),
        epochs=10,
        batch_size=16
    )
    
    y_pred_probs = model.predict(x_test)
    y_pred = np.argmax(y_pred_probs, axis=1)
    
    cm = confusion_matrix(y_test, y_pred)
    print(cm)
    
    model.save(MODEL_PATH)

main()

