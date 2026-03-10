import numpy as np
import tensorflow as tf
import time as tm

N=8

#should be adjusted based on readings
threshold_ADC = 1000

#The inputs should be taken in intervals take the full picture (? sec = 1 image or ? reading = 1 image) (30 reading / sec)
#Maybe starting from a point of first pressed grid point
#this will have to be replaced with a func that turns ADC (0-4065) into bool (true or false)
def basic_bool(readings):
    output = np.zeros((1, N, N), dtype=bool)
    
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[:, r, c] > threshold_ADC
    
    return output

# new ML model should be built !!!
model = tf.keras.models.load_model("ml_model.keras")

'One small test'
sample = matrix = [
    [       0,      0,      0,      0,      0,      0,      0,      0],
    [       0,      0,   2000,   2000,   2000,   2000,      0,      0],
    [       0,      0,   2000,      0,      0,      0,      0,      0],
    [       0,      0,   2000,      0,      0,      0,      0,      0],
    [       0,      0,   2000,   2000,   2000,   2000,      0,      0],
    [       0,      0,   2000,      0,      0,   2000,      0,      0],
    [       0,      0,   2000,   2000,   2000,   2000,      0,      0],
    [       0,      0,      0,      0,      0,      0,      0,      0],
]

retained = np.zeros((1, N, N), dtype=int)
def update_matrix(readings):
    for r in range(N):
        for c in range(N):
            retained[:, r, c] = max(readings[r][c], retained[:, r, c])

max_times = 60 # about 3 sec
times = 0

while True:
    new = sample #this will be the readings input
    update_matrix(new)
    times += 1
    if times == max_times:
        sample_bool = basic_bool(retained)
        sample_feat = sample_bool.reshape(-1, N * N).astype(np.float32)
        prediction = model.predict(sample_feat)
        predicted_digit = np.argmax(prediction, axis=1)[0]
        print(f"Predicted Digit: {predicted_digit}")
        retained = np.zeros((1, N, N), dtype=int)
        times = 0
    tm.sleep(0.1)