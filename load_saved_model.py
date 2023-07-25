
import keras
import numpy as np
import tensorflow as tf
import os

IMAGE_SHAPE = (224,224)
tumors = ["glioma", "meningioma", "notumor", "pituitary"]

class load_model:
    def __init__(self):
        self.save_model = keras.models.load_model(os.path.join("trained_models", "trained_on_all_datasets_94.h5"))


    def predict(self, img_path):
        image = tf.io.read_file(img_path)
        image = tf.image.decode_png(image, channels=3)
        image = tf.image.resize(image, IMAGE_SHAPE)
        # image = image/255
        image = np.array([image])

        prediction_value = np.argmax(self.save_model.predict(image))
        return tumors[prediction_value]
    
    def predict2(self, image):
        # image = tf.image.decode_png(image, channels=3)
        image = tf.image.resize(image, IMAGE_SHAPE)
        # image = image/255
        image = np.array([image])

        prediction_value = np.argmax(self.save_model.predict(image))
        return tumors[prediction_value]
    


