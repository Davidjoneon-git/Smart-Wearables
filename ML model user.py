import numpy as np
import tensorflow as tf

N=8

#should be adjusted based on readings
threshold_ADC = 1000

#The inputs should be taken in intervals take the full picture (? sec = 1 image)
#Maybe starting from a point of first pressed grid point
#this will have to be replaced with a func that turns ADC (0-4065) into bool (true or false)
def basic_bool(readings):
    output = np.zeros((1, N, N), dtype=bool)
    
    for r in range(N):
        for c in range(N):
            output[:, r, c] = readings[r][c] > threshold_ADC
    
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

label = 6

sample_bool = basic_bool(sample)

sample_feat = sample_bool.reshape(-1, N * N).astype(np.float32)

prediction = model.predict(sample_feat)
predicted_digit = np.argmax(prediction, axis=1)[0]

print("True label:", label)
print("Predicted:", predicted_digit)