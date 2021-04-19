import traceback
from pprint import pprint
import pandas as pd
import tqdm
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from tensorflow.keras.layers.experimental import preprocessing

sns.set()


def main():
    df = pd.read_csv("recipes.csv")
    df = df[df['num_ratings'] > 10]

    train = df.sample(frac=0.8, random_state=0)
    train_y = train['rating_avg']
    train_X = train.loc[:, [col for col in train.columns if 'uses_' in col]].fillna(0)

    test = df.drop(train.index)
    test_y = test['rating_avg']
    test_X = test.loc[:, [col for col in test.columns if 'uses_' in col]].fillna(0)

    # The data isn't normalised at all, so do some normalisation
    normalizer = preprocessing.Normalization()
    normalizer.adapt(np.array(train_X))

    model = keras.Sequential([
        normalizer,
        layers.Dense(64, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(1)
    ])
    model.compile(
        loss='mean_absolute_error',
        optimizer=tf.keras.optimizers.Adam(0.001)
    )

    history = model.fit(
        train_X, train_y,
        validation_split=0.2, epochs=100)
    plot_loss(history)

def plot_loss(history):
    plt.plot(history.history['loss'], label='loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.ylim([0, 10])
    plt.xlabel('Epoch')
    plt.ylabel('Error')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    main()
