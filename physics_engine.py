import numpy as np
import pandas as pd


class PrimeMover:
    def __init__(self, force_init=0.0):
        self.max_force = np.infty
        self.force_current = np.clip(force_init, -self.max_force, self.max_force)
        self.force_history = [self.force_current]

    def update(self, force_current, dt=None):
        self.force_history.append(force_current)

    def get_state(self):
        return self.force_current

class Resistance:
    def __init__(self, df_resistance, resistance_init=0.0):
        self.resistance_current = resistance_init
        self.df_resistance = df_resistance
        self.column_speed, self.column_coef = self.df_resistance.columns.tolist()
        self.resistance_history = [self.resistance_current]

    def update(self, velocity, dt=None):
        if velocity not in self.df_resistance[self.column_speed]:
            df = pd.concat([self.df_resistance.copy(), 
                            pd.DataFrame([[velocity, np.nan]], columns=self.df_resistance.columns)])
            df = df.sort_values(self.column_speed).interpolate()
        else:
            df = self.df_resistance.copy()
        self.resistance_current = df.loc[df[self.column_speed]==velocity, self.column_coef].to_numpy()[0]
        self.resistance_history.append(self.resistance_current)

    def get_state(self):
        return self.resistance_current

class Mass:
    def __init__(self, mass, position_init=0.0, velocity_init=0.0, acceleration_init=0.0):
        self.mass = mass
        self.position_current = position_init
        self.position_history = [self.position_current]
        self.velocity_current = velocity_init
        self.velocity_history = [self.velocity_current]
        self.acceleration_current = acceleration_init
        self.acceleration_history = [self.acceleration_current]

    def update(self, force, dt):
        self.acceleration_current = force / self.mass
        self.acceleration_history.append(self.acceleration_current)
        self.velocity_current += self.acceleration_current * dt
        self.velocity_history.append(self.velocity_current)
        self.position_current += self.velocity_current * dt
        self.position_history.append(self.position_current)

    def get_state(self):
        return self.position_current, self.velocity_current, self.acceleration_current


class DigitalTwin:
    def __init__(self, timestep, mass_model, prime_mover_model, resistance_model, t0=0):
        self.timestep = timestep
        self.n_step = 0
        self.t_elapsed = t0
        self.xtime = [t0]
        
        # models
        self.mass_model = mass_model
        self.prime_mover_model = prime_mover_model
        self.resistance_model = resistance_model
        
        # initialize kinematics
        # self.position, self.velocity, self.acceleration = self.mass_model.get_state()
        
        # initialize forces
        self.force = self.prime_mover_model.get_state()
        self.resistance = self.resistance_model.get_state()

    def update(self, dummy=None, dt=None):
        
        self.prime_mover_model.update(self.force)
        self.force = self.prime_mover_model.get_state()

        _, velocity, _ = self.mass_model.get_state()
        self.resistance_model.update(velocity)
        self.resistance = self.resistance_model.get_state()

        self.mass_model.update(self.force-self.resistance, self.timestep)

        self.n_step += 1
        self.t_elapsed = self.n_step*self.timestep 
        self.xtime.append(self.t_elapsed)

        # self.position, self.velocity, self.acceleration = self.mass_model.get_state()

    def get_state(self):
        return 0
    