import ray
from ray import tune
import ray.rllib.agents.ppo as ppo
from ray.rllib.models import ModelCatalog
from ray.rllib.models.tf.tf_modelv2 import TFModelV2
from tensorflow.keras.layers import Layer
from keras.initializers import RandomNormal
from tensorflow.keras import backend as K
import tensorflow as tf
from ray.rllib.models.tf.misc import normc_initializer
from ray.rllib.agents.dqn.distributional_q_model import DistributionalQModel
from ray.rllib.utils import try_import_tf
from ray.rllib.models.tf.visionnet_v2 import VisionNetwork as MyVisionNetwork
import datetime

from custom_rbf_layer_model_v2 import RBFModel1, MyKerasModel1

ModelCatalog.register_custom_model("rbf_model", RBFModel1)
ModelCatalog.register_custom_model("my_keras_model", MyKerasModel1)

log_dir="logs/fit/" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=1)

# ray.init(local_mode=True) # local mode for debugging
ray.init()
tune.run(
    "PPO",
    stop={"episode_reward_mean": -200},
    config={
        "model": {
            "custom_model": "rbf_model", # tune.grid_search(["rbf_model", "my_keras_model"]),
            "custom_options": {},  # extra options to pass to your model
        },
        "env": "Pendulum-v0",
        "train_batch_size": 2048,
        "vf_clip_param": 10.0,
        "num_workers": 0,
        "num_envs_per_worker": 10,
        "lambda": 0.1,
        "gamma": 0.95,
        "lr": 0.0003,
        "sgd_minibatch_size": 64,
        "num_sgd_iter": 10,
        "batch_mode": "complete_episodes",
        "observation_filter": "MeanStdFilter"

        # "lr": 0.001, # tune.grid_search([0.01, 0.001, 0.0001]),
        # "sample_batch_size": 1,
        # "train_batch_size": 256,
        # "use_gae": True,
        # "batch_mode": "complete_episodes"
    },
)