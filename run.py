from fastapi import FastAPI, Request, Response
import uvicorn
import numpy as np
import json
from itertools import product
from contextlib import asynccontextmanager

ID_VALUE_0 = ["apples", "bananas", "cherries"]
ID_VALUE_1 = ["red", "green", "blue"]
ID_VALUE_2 = ["small", "medium", "large"]
NUM_DISCRETE_FEATURES = 50
NUM_CONTINUOUS_DERIVED_FEATURES = 4

TOTAL_FEATURES = NUM_DISCRETE_FEATURES + NUM_CONTINUOUS_DERIVED_FEATURES


# --- FastAPI Lifespan (Startup/Shutdown) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Initializing Python server with means and feature store...")

    app.coefficient_means = np.random.rand(TOTAL_FEATURES)
    app.feature_store = _build_feature_store()

    print(f"Coefficient means array size: {app.coefficient_means.shape}")
    print(f"Feature store contains {len(app.feature_store)} discrete entries.")
    print(f"Each request will result in a matrix of size (1, {TOTAL_FEATURES}).")

    print("\n--- Running a sample prediction during startup ---")
    test_id_values = ["apples", "red", "small"]
    test_continuous_feature = 15.75
    result = prepare_features_and_predict(test_id_values, test_continuous_feature)

    print(f"Sample result vector: {result}")
    print("----------------------------------------")

    print("Server ready on http://0.0.0.0:8080")

    yield  # Server is running

    # Cleanup logic (optional)
    print("Shutting down server...")


app = FastAPI(lifespan=lifespan)


@app.post("/predict")
async def predict(request: Request):
    request_json = await request.json()

    id_values = [request_json["id_0"], request_json["id_1"], request_json["id_2"]]
    continuous_feature = request_json["continuous_feature"]
    result = prepare_features_and_predict(id_values, continuous_feature)
    response = Response(
        content=json.dumps(
            {
                "result": result.tolist(),
            }
        ),
        media_type="application/json",
    )
    return response


# --- Helper Functions ---
def _features_to_key(features):
    """Converts a list of discrete ID values to a string key."""
    return "_".join(features)


def _sigmoid(x):
    return 1 / (1 + np.exp(-x))


def _predict(data_matrix, coeffs):
    return _sigmoid(np.dot(data_matrix, coeffs))


def _sample_coeffs(means):
    """Samples coefficients based on learned means."""
    return np.random.normal(means, 0.5)


def _build_feature_store():
    """Builds the in-memory feature store for discrete combinations."""
    feature_store = {}
    all_id_values = product(ID_VALUE_0, ID_VALUE_1, ID_VALUE_2)
    for i, (id_0, id_1, id_2) in enumerate(all_id_values):
        key = _features_to_key([id_0, id_1, id_2])
        # Each entry in the store is a matrix of NUM_DISCRETE_FEATURES
        matrix = np.random.rand(1, NUM_DISCRETE_FEATURES)
        feature_store[key] = matrix

    print(f"Feature store size: {len(feature_store)} discrete combinations.")
    return feature_store


def _generate_continuous_features(continuous_feature: float) -> np.ndarray:
    feat_sq = continuous_feature**2
    feat_log = np.log1p(continuous_feature)
    feat_sqrt = np.sqrt(continuous_feature)

    # Combine them into a NumPy array (reshape to (1, N) for concatenation with data_matrix)
    continuous_features = np.array(
        [continuous_feature, feat_sq, feat_log, feat_sqrt]
    ).reshape(1, NUM_CONTINUOUS_DERIVED_FEATURES)

    return continuous_features


def _get_feature_matrix(
    id_values: list[str], continuous_feature: float
) -> np.ndarray:
    key = _features_to_key(id_values)
    data_matrix_static = app.feature_store[key]
    continuous_features = _generate_continuous_features(continuous_feature)
    return np.concatenate((data_matrix_static, continuous_features), axis=1)


def prepare_features_and_predict(
    id_values: list[str], continuous_feature: float
) -> np.ndarray:
    data_matrix_augmented = _get_feature_matrix(id_values, continuous_feature)
    coeffs = _sample_coeffs(app.coefficient_means)
    result = _predict(data_matrix_augmented, coeffs)
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
