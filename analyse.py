print("imports...", end="")
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
print("done")

def main():
    print("Reading in CSV")
    df = pd.read_csv("recipes.csv")
    df = df[df['num_ratings'] > 10]
    df['rating_avg'] = df['rating_avg'] / 5
    # Get rid of all columns that aren't used much
    df = df.loc[:, (df.isna().sum() < df.shape[0] * 0.99)]

    sns.histplot(df['rating_avg'], bins=20)
    plt.show()
    df['rating_avg'].describe().T[['mean', 'std']]


    print(f"Preprocessing data ({len(df)} records available)")
    train = df.sample(frac=0.8, random_state=0)
    train_y = train['rating_avg']
    train_X = train.loc[:, [col for col in train.columns if 'uses_' in col]].fillna(0)

    test = df.drop(train.index)
    test_y = test['rating_avg']
    test_X = test.loc[:, [col for col in test.columns if 'uses_' in col]].fillna(0)

    # The data isn't normalised at all, so do some normalisation
    normalizer = preprocessing.Normalization()
    normalizer.adapt(np.array(train_X))

    print("Building model")
    model = keras.Sequential([
        normalizer,
        layers.Dense(32, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(1)
    ])

    model.compile(
        loss='mean_absolute_error',
        optimizer=tf.keras.optimizers.Adam(0.001)
    )

    callback = tf.keras.callbacks.EarlyStopping(
        monitor='val_loss', patience=10, min_delta=0.01
    )

    print("Fitting model")
    history = model.fit(
        train_X, train_y,
        validation_split=0.2, epochs=500
        # , callbacks=[callback]
    )

    val_loss = round(history.history["val_loss"][-1] * 1000) / 1000
    rating_loss = val_loss * 5
    print(f'Final val_loss is {val_loss} or {rating_loss} stars)')
    plot_loss(history)

    mae = tf.keras.losses.MeanAbsoluteError()
    baseline_mae = mae(test_y, train_y.mean()).numpy()
    model_mae = mae(test_y, model.predict(test_X).mean()).numpy()
    print(f"Baseline MAE is {baseline}, model's MAE is {model_mae}, \n"
          f"model is better by: {baseline - model_mae}")

    pred_y = model.predict(test_X)
    plt.scatter(test_y, (pred_y.T[0].T - test_y))
    plt.scatter(test_y, (train_y.mean() - test_y))
    plt.xlabel('Predictions [rating]')
    plt.ylabel('Absolute Error [rating]')
    plt.show()

def stus_thing():
    plt.figure(figsize=(30, 24))
    model = NMF(n_components=2)
    num_ingredients = 500
    top_ingredients = pd.Series(df[[c for c in df.columns.to_list() if 'uses_' in c]]
            .count()
            .sort_values(ascending=False)
            .head(num_ingredients).index
    )
    zeroed = df.loc[:, top_ingredients]
    zeroed.fillna(0, inplace=True)
    zeroed = zeroed.T
    # Fit the model to zeroed
    model.fit(zeroed)
    # Transform the televote_Rank: nmf_features
    nmf_features = model.transform(zeroed)

    inx = np.array(zeroed.index)
    xs = nmf_features[:, 0]
    # Select the 1th feature: ys
    ys = nmf_features[:, 1]
    # Scatter plot
    plt.scatter(xs, ys, alpha=0.5)
    # Annotate the points
    for x, y, inx in zip(xs, ys, inx):
        plt.annotate(inx, (x, y), fontsize=10, alpha=0.5)
    plt.savefig('nnmf.png')
    plt.show()


def plot_loss(history):
    plt.plot(history.history['loss'], label='loss')
    plt.plot(history.history['val_loss'], label='val_loss')
    plt.ylim([0, 0.2])
    # plt.xlim([3, history.epoch[-1]])
    plt.xlabel('Epoch')
    plt.ylabel('Error')
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    main()
