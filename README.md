# seagul
A utility library. I collected most of the software I use across projects in my resarch and put it here. 

Hightlights include:

- Implementations of several deep reinforcement learning algorithms, inlcuding [Proximal Policy Optimization](./seagul/rl/ppo),  [Augmented Random Search](./seagul/rl/ars), and [Soft Actor Critic](./seagul/rl/sac). Along with some novel modifications made as part of my research.

- [Nueral network utiltities](./seagul/nn.py), including supervised learning functionality mimicking keras' model.fit in pytorch, and an interface to make various MLPs, RBFs etc that are compatible with the rest of this library.

- [Custom OpenAI gym environments](./seagul/envs), that I've studied at some point or another in my research. 

- [Experiment utilities](./seagul/rl/run_utils), for saving RL experiments along with meta data, logs, and a mechanism to restore the trained agents.


This is a python package, after cloning I recommend you install it (in some sort of virtual environment) with:

```
pip install -e seagul/
```
 
You can install all the requirments with:

```
pip install -r requirements.txt
```
