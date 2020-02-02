import xml.etree.ElementTree as ET

import numpy as np

import matplotlib.pyplot as plt
import toml
from mpl_toolkits import mplot3d


class Environment:
    def __init__(self, settings_file="configuration/settings.toml"):
        """ TODO
        """
        self.settings = toml.load(settings_file)
        self.dt = self.settings["environment"]["dt"]
        self.N = self.settings["environment"]["n"]

        # Placeholders
        self.names = np.empty(self.N)
        self.m = np.zeros(self.N)
        self.positions = np.zeros((self.N, 3))
        self.velocities = np.zeros((self.N, 3))
        self.accelerations = np.zeros((self.N, 3))
        
    def _reset(self):
        """ Resets the environment back to default positions. """
        self.m = np.random.uniform(0, 10, (self.N, 1))
        self.positions = np.random.uniform(-100, 100, (self.N, 3))
        self.velocities = np.random.uniform(-1, 1, (self.N, 3))
        self.accelerations = np.zeros((self.N, 2))

    def step(self, dt):
        pass

    def calculate_gravity_laws(self, positions):
        """ Calculates the net acceleration (ax, ay, az) due to 
        gravitation from all other bodies for all bodies.
        """
        force_between_bodies = np.zeros((self.N, self.N, 3))
        for i in range(0, self.N-1):
            for j in range(i+1, self.N):
                # Newton's law of Gravitation
                relative_position = positions[j] - positions[i]
                l2_norm = np.linalg.norm(relative_position) + 1e-6
                gravitational_force_ij = self.settings["const"]["G"]*self.m[i]*self.m[j]*relative_position/l2_norm**3 

                # Fji = -Fij <=> Fij = -Fji
                force_between_bodies[i, j] = gravitational_force_ij
                force_between_bodies[j, i] = -gravitational_force_ij
        
        # Net acceleration on each body
        accelerations = np.sum(force_between_bodies, axis=1) / self.m

        return accelerations

    def runge_kutta(self):
        """ Implementation of RK{1,2,3,4} with fixed step dt.
        See documentation for more details.
        """
        order = self.settings["RK"]["order"]
        
        # State information to integrate [v0, ..., vn, a0, ..., an]
        K_vals = np.zeros((order, self.N*2, 3)) 
        K_vals[:, :self.N] = np.copy(self.velocities)

        # Get the derivatives at each stage
        for i in range(order):
            if i > 0: 
                RK_B = np.array(self.settings["RK"]["B"][str(order)][i]).reshape(-1,1)
                RK_B = np.repeat(RK_B[:, :, np.newaxis], 3, axis=2)
                K_vals[i, self.N:] = self.calculate_gravity_laws(
                    self.positions + self.dt*np.sum(RK_B*K_vals[:-1, :self.N], axis=0)
                )
            else:
                K_vals[i, self.N:] = self.calculate_gravity_laws(self.positions)

        # Broadcast C for estimate updates
        RK_C = np.array(self.settings["RK"]["C"][str(order)])
        RK_C = np.repeat(RK_C[:, :, np.newaxis], 3, axis=2)

        # Update position estimate
        self.positions += np.sum(K_vals[:, :self.N]*RK_C*self.dt, axis=0)

        # Update velocity estimate
        self.velocities += np.sum(K_vals[:, self.N:]*RK_C*self.dt, axis=0)

    def huen_predictor_corrector(self):
        """ Implements Huen's predictor-corrector with fixed step dt.
        See documentation for more details.
        """
        curr_step = 0
        error = 1e99
        y_t = np.vstack((self.positions, self.velocities))
        y_predict = np.copy(y_t)
        y_corrector = np.copy(y_t)

        # Predictor
        f_t_acc = self.calculate_gravity_laws(self.positions)
        f_t_vel = self.velocities
        f_t = np.vstack((f_t_vel, f_t_acc))
        y_predict = np.vstack((self.positions, self.velocities)) + f_t*self.dt

        # Keep correcting until desired accuracy or max steps reached
        while curr_step < self.settings["HPC"]["max_steps"] and error > self.settings["HPC"]["epsilon"]:
            # Corrector
            f_t_acc = self.calculate_gravity_laws(y_predict[:self.N])
            f_t_correct = np.vstack((y_predict[self.N:], f_t_acc))
            average_accel = 0.5*(f_t + f_t_correct)
            y_corrector = y_t + self.dt*average_accel

            # Relative Error; added offset to avoid 0 denominator            
            error = np.max(np.abs(y_corrector - y_predict)/(y_corrector + 1e-6))

            y_predict = np.copy(y_corrector)
            curr_step += 1

        self.positions = y_predict[:self.N]
        self.velocities = y_predict[self.N:]

    def collision_combine(self, collision_distance=3):
        """ Checks if any two particles are close, if they are 
        then their masses are combined, and the resultant position is the average
        of their current relative position.

        :param collision_distance: Euclidan distance which classifies
            as a successful "collision".
        """
        bodies = np.repeat(self.positions[:, np.newaxis, :], self.N, axis=1)  
        other_bodies = np.repeat(self.positions[np.newaxis], self.N, axis=0)
        euclidean_distances_w = np.linalg.norm(bodies - other_bodies, axis=2)
        # euclidean_distances = euclidean_distances_w[np.nonzero(euclidean_distances_w)].reshape(-1,self.N-1)
            # min_vals = np.amin(euclidean_distances, axis=1)
        collidedMask = euclidean_distances_w < collision_distance
        nonZeroMask = euclidean_distances_w != 0
        hasCollidedMask = np.logical_and(collidedMask, nonZeroMask)
        collided_body1 = np.where(hasCollidedMask)
        arr = np.transpose(np.vstack((collided_body1[0], collided_body1[1])))
        arr = np.unique(arr)

        # If you do collide, make sure that you are picking the one which was closest... (interesting problem...)
        import pdb; pdb.set_trace()

if __name__ == "__main__":
    env = Environment()
    env._reset()
    fig = plt.figure()
    ax = plt.axes(projection='3d')

    # Temporary plotting
    for i in range(1000):
        env.runge_kutta()
        # env.huen_predictor_corrector()        
        res = ax.scatter3D(env.positions[:,0], env.positions[:,1], env.positions[:,2], c='r')
        plt.pause(0.1)
        res.set_alpha(0.1)
        res.set_linewidth(0)
