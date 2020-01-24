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

class RBFLayer(Layer):
    def __init__(self, units, **kwargs):
        super(RBFLayer, self).__init__(**kwargs)
        self.units = units
    def build(self, input_shape):
        initializer_gaus = RandomNormal(mean=0.0, stddev=1.0, seed=None)
        self.mu = self.add_weight(name='mu',
                                #   shape=(int(input_shape[1]), self.units),
                                  shape=(self.units, input_shape[1]),
                                  initializer=initializer_gaus,
                                  trainable=True)
        self.sigma = self.add_weight(name='sigma',
                                #   shape=(int(input_shape[1]), self.units),
                                  shape=(self.units,),
                                  initializer='ones',
                                  trainable=True)
        self.input_weights = self.add_weight(name='input_weights',
                                  shape = (self.units,),
                                  initializer = 'random_uniform',
                                  trainable = True)
        super(RBFLayer, self).build(input_shape)

    def call(self, inputs):
        # diff = K.expand_dims(inputs) - self.mu
        # l2 = K.sum(K.pow(diff,2), axis=1)
        # res = K.exp(-1 * self.sigma * l2)
        # return res
        C = K.expand_dims(self.mu)
        H = K.transpose(C-K.transpose(inputs))
        return self.input_weights * K.exp(-self.sigma * K.sum(H**2, axis=1))

    def compute_output_shape(self, input_shape):
        return (input_shape[0], self.units)

class RBFModel(TFModelV2):
    def __init__(self, obs_space, action_space, num_outputs, model_config, name):
        super(RBFModel, self).__init__(obs_space, action_space, num_outputs, model_config, name)
        self.inputs = tf.keras.layers.Input(
            shape=obs_space.shape, name="observations")
        hidden_layer = RBFLayer(
            256)(self.inputs)
        output_layer = tf.keras.layers.Dense(
            num_outputs,
            name="my_output_layer",
            activation=tf.nn.relu,
            kernel_initializer='random_uniform')(hidden_layer)
        value_layer = tf.keras.layers.Dense(
            1,
            name="my_value_layer",
            activation=tf.nn.relu,
            kernel_initializer='random_uniform')(hidden_layer)
        self.base_model = tf.keras.Model(
            self.inputs, [output_layer, value_layer])
        self.register_variables(self.base_model.variables)

    def forward(self, input_dict, state, seq_lens):
        model_out, self._value_out = self.base_model(input_dict["obs"])
        return model_out, state
    def value_function(self):
        return self._value_out
        # return tf.reshape(self._value_out, [-1])

class MyKerasModel(TFModelV2):
    """Custom model for policy gradient algorithms."""

    def __init__(self, obs_space, action_space, num_outputs, model_config,
                 name):
        super(MyKerasModel, self).__init__(obs_space, action_space,
                                           num_outputs, model_config, name)
        self.inputs = tf.keras.layers.Input(
            shape=obs_space.shape, name="observations")
        layer_1 = tf.keras.layers.Dense(
            256,
            name="my_layer1",
            activation=tf.nn.relu,
            kernel_initializer=normc_initializer(1.0))(self.inputs)
        layer_out = tf.keras.layers.Dense(
            num_outputs,
            name="my_out",
            activation=None,
            kernel_initializer=normc_initializer(0.01))(layer_1)
        value_out = tf.keras.layers.Dense(
            1,
            name="value_out",
            activation=None,
            kernel_initializer=normc_initializer(0.01))(layer_1)
        self.base_model = tf.keras.Model(self.inputs, [layer_out, value_out])
        self.register_variables(self.base_model.variables)

    def forward(self, input_dict, state, seq_lens):
        model_out, self._value_out = self.base_model(input_dict["obs"])
        return model_out, state

    def value_function(self):
        return tf.reshape(self._value_out, [-1])

ModelCatalog.register_custom_model("rbf_model", RBFModel)
ModelCatalog.register_custom_model("my_keras_model", MyKerasModel)

# ray.init(local_mode=True) # local mode for debugging
ray.init()
tune.run(
    "SAC",
    stop={"episode_reward_mean": -200},
    config={
        "model": {
            "custom_model": "my_keras_model", # tune.grid_search(["rbf_model", "my_keras_model"]),
            "custom_options": {},  # extra options to pass to your model
        },
        "env": "Pendulum-v0",
        "num_gpus": 0,
        "num_workers": 1,
        "lr": 0.001, # tune.grid_search([0.01, 0.001, 0.0001]),
        "eager": True,
        "sample_batch_size": 1,
        "train_batch_size": 256,
        "timesteps_per_iteration": 1000,
        "evaluation_interval": 1
    },
)