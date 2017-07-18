import numpy as np
from six import iteritems
import scipy.sparse

from openmdao.utils.options_dictionary import OptionsDictionary

from openmdao.api import ExplicitComponent

from openode.utils.var_names import get_y_new_name, get_step_name


class TMOutputComp(ExplicitComponent):

    def initialize(self):
        self.metadata.declare('states', type_=dict, required=True)
        self.metadata.declare('times', type_=np.ndarray, required=True)
        self.metadata.declare('num_stages', type_=int, required=True)

    def setup(self):
        times = self.metadata['times']

        num_time_steps = len(times)

        self.declare_partials('*', '*', dependent=False)

        for state_name, state in iteritems(self.metadata['states']):
            size = np.prod(state['shape'])

            for i_step in range(num_time_steps):
                name = get_step_name(i_step, state_name)

                self.add_input(name, src_indices=np.arange(size).reshape(state['shape']),
                    units=state['units'])

            self.add_output(state_name, shape=(num_time_steps,) + state['shape'],
                units=state['units'])

            vals = np.ones(size)
            full_rows = np.arange(num_time_steps * size).reshape((num_time_steps, size))
            cols = np.arange(size)

            for i_step in range(num_time_steps):
                name = get_step_name(i_step, state_name)

                rows = full_rows[i_step, :]

                self.declare_partials(state_name, name, val=vals, rows=rows, cols=cols)

    def compute(self, inputs, outputs):
        times = self.metadata['times']

        num_time_steps = len(times)

        for state_name, state in iteritems(self.metadata['states']):

            for i_step in range(num_time_steps):
                name = get_step_name(i_step, state_name)

                outputs[state_name][i_step, :] = inputs[name]
