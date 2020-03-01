import numpy as np
import toml


class InitialCondition:
    def __init__(self, config):
        self.m = np.array(config['mass'])
        self.positions = np.array(config[['x', 'y', 'z']])
        self.velocities = np.array(config[['vx', 'vy', 'vz']])


class Environment:
    """ Environment contains all the necessary
    utilities to move the point mass bodies and 
    calculate the gravitation interactions between each body.
    """

    def __init__(
        self,
    ):
        """ Setup the environment.

        :param config: is a preset configuration defined? (T/F)
        :param config_id: the ID of the particular initial
            configuraiton defined in the settings.
        :param settings_file: path of the settings to load.
        """
        self.initial_conditions = None
        self.config = None
        self.config_id = None
        self.settings = None
        self.dt = 0
        self.gt = 0
        self.N = 0
        self.G = 0
        self.t_max = 0

        # Placeholders
        self.names = np.empty(self.N)
        self.m = np.zeros(self.N)
        self.positions = np.zeros((self.N, 3))
        self.velocities = np.zeros((self.N, 3))
        self.accelerations = np.zeros((self.N, 3))

    @classmethod
    def from_config(
        cls,
        config=None,
        config_id=None,
        settings_file="configuration/settings.toml"
    ):
        """ Setup the environment.

        :param config: is a preset configuration defined? (T/F)
        :param config_id: the ID of the particular initial
            configuraiton defined in the settings.
        :param settings_file: path of the settings to load.
        """
        settings = toml.load(settings_file)

        if settings["environment"]["method"] == "HPC":
            self = HuenPredictorEnvironment()
            self._max_steps = settings["HPC"]["max_steps"]
            self._epsilon = settings["HPC"]["epsilon"]
        elif settings["environment"]["method"] == "RK":
            self = RungeKuttaEnvironment()
            self.order = int(settings["RK"]["order"])
            self.rk_b = {int(key): val for key, val in settings["RK"]["B"].items()}
            self.rk_c = {int(key): val for key, val in settings["RK"]["C"].items()}
        else:
            raise ValueError("Method must be one of HPC, RK")

        self.dt = settings["environment"]["dt"]
        self.t_max = settings["environment"]["t_max"]

        if config is not None:
            self.N = config.shape[0]
            self.G = settings['configs'][config_id]['G']
            self.initial_conditions = InitialCondition(config)
        else:
            self.N = settings['environment']['n']
            self.G = settings['const']['G']

        self.config = config
        self.config_id = config_id
        self.settings = settings

        return self

    def _reset(self):
        """ Resets the environment back to default positions. """
        # Positions defined by a configuration. Overrides the default values.
        if self.initial_conditions is not None:
            self.m = np.copy(self.initial_conditions.m)
            self.positions = np.copy(self.initial_conditions.positions)
            self.velocities = np.copy(self.initial_conditions.velocities)
        else:
            self.m = np.random.uniform(0, 2, (self.N, 1))
            self.positions = np.random.uniform(-100, 100, (self.N, 3))
            self.velocities = np.random.uniform(-1, 1, (self.N, 3))

        self.accelerations = np.zeros((self.N, 2))
        self.gt = 0

    def step(self):
        """ Update the environment a single timestep dt each call """
        if self.gt < self.t_max:
            self.iterate()
            self.gt += self.dt

    def iterate(self):
        pass

    def calculate_gravity_laws(self, positions):
        """ Calculates the net acceleration (ax, ay, az) due to 
        gravitation from all other bodies for all bodies.
        """
        force_between_bodies = np.zeros((self.N, self.N, 3))
        for i in range(0, self.N - 1):
            for j in range(i + 1, self.N):
                # Newton's law of Gravitation
                relative_position = positions[j] - positions[i]
                l2_norm = np.linalg.norm(relative_position) + 1e-6
                gravitational_force_ij = self.G * self.m[i] * self.m[j] * relative_position / l2_norm ** 3

                # Fji = -Fij <=> Fij = -Fji
                force_between_bodies[i, j] = gravitational_force_ij
                force_between_bodies[j, i] = -gravitational_force_ij

        # Net acceleration on each body
        accelerations = np.sum(force_between_bodies, axis=1) / self.m

        return accelerations

    def collision_combine(self, collision_distance=3):
        """ Checks if any two particles are close, if they are 
        then their masses are combined, and the resultant position is the average
        of their current relative position.

        :param collision_distance: Euclidan distance which classifies
            as a successful "collision".
        """
        # bodies = np.repeat(self.positions[:, np.newaxis, :], self.N, axis=1)  
        # other_bodies = np.repeat(self.positions[np.newaxis], self.N, axis=0)
        # euclidean_distances_w = np.linalg.norm(bodies - other_bodies, axis=2)
        # # euclidean_distances = euclidean_distances_w[np.nonzero(euclidean_distances_w)].reshape(-1,self.N-1)
        #     # min_vals = np.amin(euclidean_distances, axis=1)
        # collidedMask = euclidean_distances_w < collision_distance
        # nonZeroMask = euclidean_distances_w != 0
        # hasCollidedMask = np.logical_and(collidedMask, nonZeroMask)
        # collided_body1 = np.where(hasCollidedMask)
        # arr = np.transpose(np.vstack((collided_body1[0], collided_body1[1])))
        # arr = np.unique(arr)

        # If you do collide, make sure that you are picking the one which was closest... (interesting problem...)
        # import pdb; pdb.set_trace()
        pass


class HuenPredictorEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self._max_steps = 0
        self._epsilon = 0

    def iterate(self):
        """ Implements Huen's predictor-corrector with fixed step dt.
        See documentation for more details.
        """
        curr_step = 0
        error = 1e99
        y_t = np.vstack((self.positions, self.velocities))

        # Predictor
        f_t_acc = self.calculate_gravity_laws(self.positions)
        f_t_vel = self.velocities
        f_t = np.vstack((f_t_vel, f_t_acc))
        y_predict = np.vstack((self.positions, self.velocities)) + f_t * self.dt

        # Keep correcting until desired accuracy or max steps reached
        while curr_step < self._max_steps and error > self._epsilon:
            # Corrector
            f_t_acc = self.calculate_gravity_laws(y_predict[:self.N])
            f_t_correct = np.vstack((y_predict[self.N:], f_t_acc))
            average_accel = 0.5 * (f_t + f_t_correct)
            y_corrector = y_t + self.dt * average_accel

            # Relative Error; added offset to avoid 0 denominator
            error = np.max(np.abs(y_corrector - y_predict) / (y_corrector + 1e-6))

            y_predict = np.copy(y_corrector)
            curr_step += 1

        self.positions = y_predict[:self.N]
        self.velocities = y_predict[self.N:]


class RungeKuttaEnvironment(Environment):
    def __init__(self):
        super().__init__()
        self.order = None
        self.rk_b = None
        self.rk_c = None

    def iterate(self):
        """ Implementation of RK{1,2,3,4} with fixed step dt.
        See documentation for more details.
        """
        # State information to integrate [v0, ..., vn, a0, ..., an]
        K_vals = np.zeros((self.order, self.N * 2, 3))
        K_vals[:, :self.N] = np.copy(self.velocities)
        # Get the derivatives at each stage
        K_vals[0, self.N:] = self.calculate_gravity_laws(self.positions)
        for i in range(1, self.order):
            RK_B = np.array(self.rk_b[self.order][i]).reshape(-1, 1)
            RK_B = np.repeat(RK_B[:, :, np.newaxis], 3, axis=2)
            K_vals[i, self.N:] = self.calculate_gravity_laws(
                self.positions + self.dt * np.sum(RK_B * K_vals[:-1, :self.N], axis=0)
            )

        # Broadcast C for estimate updates
        RK_C = np.array(self.rk_c[self.order])
        RK_C = np.repeat(RK_C[:, :, np.newaxis], 3, axis=2)

        # Update position estimate
        self.positions += np.sum(K_vals[:, :self.N] * RK_C * self.dt, axis=0)

        # Update velocity estimate
        self.velocities += np.sum(K_vals[:, self.N:] * RK_C * self.dt, axis=0)
