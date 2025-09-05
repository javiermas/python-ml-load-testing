from locust import HttpUser, task, between
import random
import numpy as np
from run import ID_VALUE_0, ID_VALUE_1, ID_VALUE_2


class PredictAPIUser(HttpUser):
    """
    High-volume user for stress testing.
    Makes requests more frequently with minimal wait time.
    """
    
    wait_time = between(0.1, 0.5)
    
    @task
    def predict_requests(self):
        """Rapid prediction requests for stress testing."""
        payload = {
            "id_0": random.choice(ID_VALUE_0),
            "id_1": random.choice(ID_VALUE_1),
            "id_2": random.choice(ID_VALUE_2),
            "continuous_feature": np.random.normal(0, 10)
        }
        
        self.client.post("/predict", json=payload)
