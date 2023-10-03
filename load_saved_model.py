
import keras
import numpy as np
import tensorflow as tf
import os

IMAGE_SHAPE = (256,256)
tumors = ["glioma", "meningioma", "notumor", "pituitary"]

class load_model:
    def __init__(self):
        self.save_model = tf.keras.models.load_model(os.path.join("trained_models", "ensemble_model_v2.h5"))

    def predict(self, image):
        image = np.array(image)
        if len(image.shape) > 2 :
            image = tf.image.resize(image, IMAGE_SHAPE)
        else:
            image_rgb = np.empty((image.shape[0], image.shape[1], 3), dtype=image.dtype)
            image_rgb[:, :, 0] = image
            image_rgb[:, :, 1] = image
            image_rgb[:, :, 2] = image
            image = image_rgb
            image = tf.image.resize(np.array(image), IMAGE_SHAPE)[:, :, :3]

        
        image = np.array([image])

        prediction_value = np.argmax(self.save_model.predict(image))
        return tumors[prediction_value]
    