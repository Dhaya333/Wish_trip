"""
Trains the CatBoost POI suitability model

    Traveller profile + Preference vector + POI attributes + Context
        -> suitability score in [0, 100]

Usage:
    python -m ml.train_poi_model

Writes the trained model to models/poi_model.cbm and prints holdout metrics.
"""
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

from data.seed_data import POIS
from ml.features import CATEGORICAL_COLS, poi_feature_columns
from ml.synthetic_data import generate_training_rows

MODEL_PATH = "models/poi_model.cbm"


def _prepare_poi_items():
    # POIS entries use a "zone" index key that isn't a model feature; the
    # rest of the dict matches the item shape expected by synthetic_data.
    items = []
    for p in POIS:
        item = dict(p)
        item.pop("zone", None)
        items.append(item)
    return items


def main():
    items = _prepare_poi_items()

    # Distinct seeds for train/test traveller-profile generation, so no
    # synthetic profile appears in both splits (Section 32 -- preventing
    # data leakage at the traveller-profile level).
    train_rows = generate_training_rows(items, n_profiles=500, is_hotel=False, seed=101)
    test_rows = generate_training_rows(items, n_profiles=120, is_hotel=False, seed=202)

    feature_cols = poi_feature_columns()
    train_df = pd.DataFrame(train_rows)
    test_df = pd.DataFrame(test_rows)

    X_train, y_train = train_df[feature_cols], train_df["label_suitability"]
    X_test, y_test = test_df[feature_cols], test_df["label_suitability"]

    cat_idx = [X_train.columns.get_loc(c) for c in CATEGORICAL_COLS]

    train_pool = Pool(X_train, y_train, cat_features=cat_idx)
    test_pool = Pool(X_test, y_test, cat_features=cat_idx)

    model = CatBoostRegressor(
        iterations=400,
        depth=6,
        learning_rate=0.06,
        loss_function="RMSE",
        random_seed=42,
        verbose=False,
    )
    model.fit(train_pool, eval_set=test_pool, use_best_model=True)

    preds = model.predict(test_pool)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds)

    print(f"POI model  -- MAE: {mae:.2f}  RMSE: {rmse:.2f}  R2: {r2:.3f}")

    model.save_model(MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()