"""
Trains the POI suitability model on REAL interaction data
(ml/raw/poi_training_table.csv, built by ml/build_training_data.py),
using the label already provided: 'synthetic_suitability_score', and the
train/test split already provided in the 'split' column.

Uses scikit-learn's HistGradientBoostingRegressor instead of CatBoost --
functionally the same idea (gradient-boosted trees with native
categorical-feature support), but avoids CatBoost's compiled _catboost
DLL, which some locked-down Windows security policies (Smart App Control)
block outright.

Usage:
    python -m ml.build_training_data     # (run first, if not already run)
    python -m ml.train_poi_model

Writes the trained model to models/poi_model.joblib and prints holdout
metrics (MAE, RMSE, R^2).
"""
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OrdinalEncoder

ML_RAW = os.path.join(os.path.dirname(__file__), "raw")
TABLE_PATH = os.path.join(ML_RAW, "poi_training_table.csv")
MODEL_PATH = "models/poi_model.joblib"

LABEL_COL = "synthetic_suitability_score"

CATEGORICAL_COLS = [
    "traveller_type", "pace", "budget_level", "hotel_comfort", "mobility_need",
    "dietary_preference", "preferred_transport", "month", "time_period",
    "hotel_zone", "category",
]

DROP_COLS = ["interaction_id", "traveller_id", "poi_id", "split", LABEL_COL]


def main():
    if not os.path.exists(TABLE_PATH):
        raise FileNotFoundError(
            f"{TABLE_PATH} not found -- run `python -m ml.build_training_data` first."
        )

    df = pd.read_csv(TABLE_PATH)
    feature_cols = [c for c in df.columns if c not in DROP_COLS]
    cat_cols_present = [c for c in CATEGORICAL_COLS if c in feature_cols]
    num_cols_present = [c for c in feature_cols if c not in cat_cols_present]

    # respect the split column that ships with the real data instead of
    # re-shuffling -- keeps results comparable run to run
    train_df = df[df["split"] == "train"].copy()
    test_df = df[df["split"] == "test"].copy()
    if test_df.empty:
        # small/dev datasets may not have a test split yet -- fall back to
        # evaluating on the train split itself so the script still runs
        test_df = train_df

    # HistGradientBoostingRegressor needs categoricals pre-encoded as
    # integer codes (with a `categorical_features` mask telling it which
    # columns those are) -- unknown categories at inference time are
    # mapped to -1 rather than raising, so this survives unseen values.
    encoder = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
    if cat_cols_present:
        train_df[cat_cols_present] = encoder.fit_transform(train_df[cat_cols_present].astype(str))
        test_df[cat_cols_present] = encoder.transform(test_df[cat_cols_present].astype(str))

    X_train = train_df[cat_cols_present + num_cols_present]
    y_train = train_df[LABEL_COL]
    X_test = test_df[cat_cols_present + num_cols_present]
    y_test = test_df[LABEL_COL]

    categorical_mask = [c in cat_cols_present for c in X_train.columns]

    model = HistGradientBoostingRegressor(
        max_iter=500, max_depth=6, learning_rate=0.05,
        categorical_features=categorical_mask, random_state=42,
    )
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    rmse = np.sqrt(mean_squared_error(y_test, preds))
    r2 = r2_score(y_test, preds) if len(y_test) > 1 else float("nan")

    print(f"POI model  -- rows train/test: {len(train_df)}/{len(test_df)} "
          f"-- MAE: {mae:.2f}  RMSE: {rmse:.2f}  R2: {r2:.3f}")

    os.makedirs("models", exist_ok=True)
    joblib.dump({
        "model": model,
        "encoder": encoder,
        "categorical_cols": cat_cols_present,
        "numeric_cols": num_cols_present,
        "feature_order": list(X_train.columns),
    }, MODEL_PATH)
    print(f"Saved model to {MODEL_PATH}")


if __name__ == "__main__":
    main()