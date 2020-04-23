from pathlib import Path
from typing import Optional

import numpy as np
import tensorflow as tf
from PIL import Image
from ai import utils

MODELS_DIR = Path("ai", "models")
MAX_SPEED = 20.  # km/h
MIN_SPEED = 5.


class AI:
    def __init__(self, model_path: Optional[Path] = None):
        if model_path is None:
            self.model_path = Path(MODELS_DIR, "e2edriving.h5")
        else:
            self.model_path = model_path
        self.model = None
        self.speed_limit = MIN_SPEED

    def predict(self, image: Image, speed: float):
        # it is necessary to load the model
        # in the same thread it is executed in
        if self.model is None:
            self.model = tf.keras.models.load_model(self.model_path)

        img = np.asarray(image)
        img = utils.preprocess(img)
        img = np.array([img])
        steering_angle = float(self.model.predict(img, batch_size=1))

        if speed > self.speed_limit:
            self.speed_limit = MIN_SPEED  # slow down
        else:
            self.speed_limit = MAX_SPEED

        throttle = 1.0 - steering_angle ** 2 - (speed / self.speed_limit) ** 2
        return steering_angle, throttle
