import gym
import numpy as np
import pybullet as p
import pybullet_data


class PBMJWalker2dEnv(gym.Env):
    motor_joints = [4, 6, 8, 10, 12, 14]
    num_joints = 16

    def __init__(self,
                 render=False,
                 lateral_friction = 0.8,
                 restitution=.5,
                 torque_limit=100,
                 sub_steps=4,
                 frame_skip=4,  # pretty  sure we only need one of these
                 solver_iterations=5,
                 init_noise=.005,
                 dt=0.0165,
                 ):

        self.args = locals()
        self.frame_skip = frame_skip
        self.torque_limit=torque_limit
        self.init_noise = init_noise
        self.dt = dt

        low = -np.ones(6)
        self.action_space = gym.spaces.Box(low=low, high=-low, dtype=np.float32)

        low = -np.ones(17)*np.inf
        self.observation_space = gym.spaces.Box(low=low, high=-low, dtype=np.float32)

        if render:
            p.connect(p.GUI)
        else:
            p.connect(p.DIRECT)

        self.plane_id = p.loadSDF(pybullet_data.getDataPath() + "/plane_stadium.sdf")[0]
        self.walker_id = p.loadMJCF(pybullet_data.getDataPath() + "/mjcf/walker2d.xml")[0]
        #flags=p.URDF_USE_SELF_COLLISION | p.URDF_USE_SELF_COLLISION_EXCLUDE_ALL_PARENTS)[0] # TODO not sure the self collision needs to be here..

        p.setGravity(0, 0, -9.8)
        p.changeDynamics(self.plane_id, -1, lateralFriction=lateral_friction, restitution=restitution)
        p.setPhysicsEngineParameter(fixedTimeStep=dt, numSubSteps=sub_steps, numSolverIterations=solver_iterations)

        self.reset()

    def step(self, a):

        a = np.clip(a,-1,1)
        forces = a*np.array([40, 40, 12, 40, 40, 12]).tolist()

        x_before = p.getBasePositionAndOrientation(self.walker_id)[0][0]

        p.setJointMotorControlArray(self.walker_id, self.motor_joints, p.TORQUE_CONTROL, forces=forces)
        for i in range(self.frame_skip):
            p.stepSimulation()

        x_after = p.getBasePositionAndOrientation(self.walker_id)[0][0]
        base_pose = p.getBasePositionAndOrientation(self.walker_id)
        height = base_pose[0][2]
        pitch  = p.getEulerFromQuaternion(base_pose[1])[1] # Pitch

        reward = (x_after - x_before) / (self.dt*self.frame_skip)
        reward += 1.0  # alive bonus
        reward -= 1e-3 * np.square(a).sum()

        done = not (0.8 < height < 2.0 and -1.0 < pitch < 1.0)

        return self._get_obs(), reward, done, {}

    def _get_obs(self):

        state = []

        base_pose = p.getBasePositionAndOrientation(self.walker_id)
        state.append(base_pose[0][2]) # Z
        state.append(p.getEulerFromQuaternion(base_pose[1])[1]) # Pitch

        for s in p.getJointStates(self.walker_id, self.motor_joints):
            state.append(s[0])

        base_vel = p.getBaseVelocity(self.walker_id)

        state.append(np.clip(base_vel[0][0], -10, 10))  # Z
        state.append(np.clip(base_vel[0][2],-10,10)) # Z
        state.append(np.clip(base_vel[1][1],-10,10)) # Pitch

        for s in p.getJointStates(self.walker_id, self.motor_joints):
            state.append(np.clip(s[1], -10,10))
        return state

    def reset(self):

        p.resetBasePositionAndOrientation(self.walker_id, [0,0,0],[0,0,0,1])

        for i in range(p.getNumJoints(self.walker_id)):
            init_ang = np.random.uniform(low=-self.init_noise, high=self.init_noise)
            init_vel = np.random.uniform(low=-self.init_noise, high=self.init_noise)
            p.resetJointState(self.walker_id, i,init_ang,init_vel)

        init_x = np.random.uniform(low=-self.init_noise, high=self.init_noise)
        init_z = np.random.uniform(low=-self.init_noise, high=self.init_noise)
        init_pitch = np.random.uniform(low=-self.init_noise, high=self.init_noise)
        init_pos = [init_x, 0, init_z]
        init_orn = p.getQuaternionFromEuler([0, init_pitch, 0])
        p.resetBasePositionAndOrientation(self.walker_id, init_pos, init_orn)

        init_vx = np.random.uniform(low=-self.init_noise, high=self.init_noise)
        init_vz = np.random.uniform(low=-self.init_noise, high=self.init_noise)
        init_vp = np.random.uniform(low=-self.init_noise, high=self.init_noise)
        p.resetBaseVelocity(self.walker_id,[init_vx,0,init_vz], [0,init_vp,0])

        p.setJointMotorControlArray(self.walker_id,
                                    [i for i in range(p.getNumJoints(self.walker_id))],
                                    p.POSITION_CONTROL,
                                    positionGains=[0.1] * self.num_joints,
                                    velocityGains=[0.1] * self.num_joints,
                                    forces=[0 for _ in range(p.getNumJoints(self.walker_id))]
                                    )
        return self._get_obs()




