import numpy as np
import unittest
from itertools import product
from parameterized import parameterized

from ozone.api import ODEIntegrator
from ozone.tests.ode_functions.simple_ode import SimpleODEFunction
from ozone.utils.compute_order import compute_convergence_order, compute_ideal_error
from ozone.utils.misc import scheme_classes, scheme_families


class Test(unittest.TestCase):

    def setUp(self):
        self.num_time_steps_vector = np.array([10, 15, 20])

        self.ode_function = SimpleODEFunction()

        self.initial_conditions = {'y': 1.}
        self.t0 = 0.
        self.t1 = 1.

        self.state_name = 'y'

        self.integrator_name = 'MDF'

    def perform_test(self, scheme_name):
        errors_vector, step_sizes_vector, orders_vector = compute_convergence_order(
            self.num_time_steps_vector, self.t0, self.t1, self.state_name,
            self.ode_function, self.integrator_name, scheme_name, self.initial_conditions)

        average_order = np.sum(orders_vector) / len(orders_vector)

        return average_order

    @parameterized.expand(scheme_classes.keys())
    def test(self, scheme_name):
        errors_vector, step_sizes_vector, orders_vector, ideal_order = compute_convergence_order(
            self.num_time_steps_vector, self.t0, self.t1, self.state_name,
            self.ode_function, self.integrator_name, scheme_name, self.initial_conditions)

        average_order = np.sum(orders_vector) / len(orders_vector)

        self.assertTrue( np.abs(ideal_order - average_order) < 1. )

        print('%18s  %1.1f  %1i  %1.1f'
            % (scheme_name[:18], average_order, ideal_order, np.abs(ideal_order - average_order)))


if __name__ == '__main__':
    unittest.main()