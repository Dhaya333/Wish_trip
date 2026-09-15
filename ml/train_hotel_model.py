"""
Trains the CatBoost hotel suitability model (Section 13).

    Traveller type/party/budget/comfort + Hotel attributes + Context
        -> suitability score in [0, 100]

Usage:
    python -m ml.train_hotel_model

Writes the trained model to models/hotel_model.cbm and prints holdout
metrics (Section 34).
"""
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from data.seed_data import HOTELS
from ml.features import CATEGORICAL_COLS, hotel_feature_columns
from ml.synthetic_data import generate_training_rows

MODEL_PATH = "models/hotel_model.cbm"


def _prepare_hotel_items():
    items = []
    for h in HOTELS:
        item = dict(h)
        item.pop("zone", None)
        items.append(item)
    return items


def main():
    items = _prepare_hotel_items()

    train_rows = generate_training_rows(items, n_profiles=500, is_hotel=True, seed=303)
    test_rows = generate_training_rows(items, n_profiles=120, is_hotel=True, seed=404)

    feature_cols = hotel_feature_columns()
    train_df = pd.DataFrame(train_rows)
    test_df = pd.DataFrame(test_rows)

    X_train, y_train = train_df[feature_cols], train_df["label_suitability"]
    X_test, y_test = test_df[feature_cols], test_df["label_suitability"]

    cat_idx = [X_train.columns.get_loc(c) for c in CATEGORICAL_COLS]

    train_pool = Pool(X_train, y_train, cat_features=cat_idx)
    test_pool = Pool(X_test, y_test, cat_features=cat_idx)

    model = CatBoostRegressor(
        iterations=350,
        depth=5,
        learning_rate=0.07,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )
    model.fit(train_pool, eval_set=test_pool, use_best_model=True)

    preds = model.predict(test_pool)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print(f"Hotel model -- MAE: {mae:.2f}  RMSE: {rmse:.2f}  R2: {r2:.3f}")

    model.save_model(MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()