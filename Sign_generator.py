import numpy as np
import tensorflow as tf

GRID_SIZE = 8
INNER_FRAC = 0.5
PIXEL_THRESHOLD = 0.2
MIN_INK_FRACTION = 0.25

EPOCHS = 5
BATCH_SIZE = 128

DIGIT_CLASSES = 10
LABEL_PLUS = 10
LABEL_MINUS = 11
LABEL_EQUALS = 12
NUM_CLASSES = 13

def blank_grid() -> np.ndarray:
    return np.zeros((GRID_SIZE, GRID_SIZE), dtype=np.float32)


def gen_plus() -> np.ndarray:
    img = blank_grid()
    img[GRID_SIZE // 2, :] = 1.0
    img[:, GRID_SIZE // 2] = 1.0
    return img


def gen_minus() -> np.ndarray:
    img = blank_grid()
    img[GRID_SIZE // 2, :] = 1.0
    return img


def gen_equals() -> np.ndarray:
    img = blank_grid()
    img[GRID_SIZE // 2 - 1, :] = 1.0
    img[GRID_SIZE // 2 + 1, :] = 1.0
    return img


def shift(img: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(img)
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            nr = r + dy
            nc = c + dx
            if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
                out[nr, nc] = img[r, c]
    return out


def thicken(img: np.ndarray) -> np.ndarray:
    out = img.copy()
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if img[r, c] > 0:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        rr = r + dr
                        cc = c + dc
                        if 0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE:
                            out[rr, cc] = 1.0
    return out

# 
def dropout(img: np.ndarray, prob: float = 0.1) -> np.ndarray:
    mask = np.random.rand(GRID_SIZE, GRID_SIZE) > prob
    return img * mask


# Image warper
def random_augment_symbol(img: np.ndarray) -> np.ndarray:
    out = img.copy()

    if np.random.rand() < 0.5:
        out = thicken(out)

    dx = np.random.randint(-1, 2)
    dy = np.random.randint(-1, 2)
    out = shift(out, dx, dy)

    if np.random.rand() < 0.5:
        out = dropout(out, prob=0.1)

    return out.astype(np.float32)


def generate_symbol_dataset(samples_per_symbol: int = 2000):
    X = []
    y = []

    generators = [
        (gen_plus, LABEL_PLUS),
        (gen_minus, LABEL_MINUS),
        (gen_equals, LABEL_EQUALS),
    ]

    for gen_func, label in generators:
        for _ in range(samples_per_symbol):
            img = gen_func()
            img = random_augment_symbol(img)
            X.append(img)
            y.append(label)

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.int64)
    return X, y
