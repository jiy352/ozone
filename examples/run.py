import numpy as np

from openmdao.api import ExplicitComponent, Problem, ScipyOptimizer, IndepVarComp

from openode.api import ODEFunction, ExplicitTMIntegrator, ImplicitTMIntegrator, \
    RK4, ForwardEuler, ExplicitMidpoint, \
    VectorizedIntegrator, BackwardEuler, ImplicitMidpoint, RK4


class Comp(ExplicitComponent):

    def initialize(self):
        self.metadata.declare('num', default=1, type_=int)

    def setup(self):
        num = self.metadata['num']

        self.add_input('y', shape=(num, 1))
        self.add_input('t', shape=(num, 1))
        self.add_output('dy_dt', shape=(num, 1))

        self.declare_partials('dy_dt', 'y', val=np.eye(num))

        self.eye = np.eye(num)

    def compute(self, inputs, outputs):
        # True solution: e^t + sin(2*pi*t)
        two_pi_t = 2*np.pi*inputs['t']
        outputs['dy_dt'] = inputs['y'] + 2*np.pi*np.cos(two_pi_t) - np.sin(two_pi_t)

    def compute_partials(self, inputs, outputs, partials):
        two_pi_t = 2*np.pi*inputs['t']
        partials['dy_dt', 't'] = self.eye \
            * (-(2*np.pi)**2 * np.sin(two_pi_t) - 2*np.pi*np.cos(two_pi_t))


num = 50

formulation = 'SAND'
# formulation = 'MDF'

scheme = RK4()

# integrator_name = 'vectorized'
integrator_name = 'explicit'
# integrator_name = 'implicit'

ode_function = ODEFunction()
ode_function.set_system(Comp)
ode_function.declare_state('y', rate_target='dy_dt', state_targets='y')
ode_function.declare_time('t')

if integrator_name == 'vectorized':
    integrator = VectorizedIntegrator(
        ode_function=ode_function, time_spacing=np.arange(num),
        scheme=scheme, initial_conditions={'y': 1.}, start_time=0., end_time=1.,
        formulation=formulation,
    )
elif integrator_name == 'explicit':
    integrator = ExplicitTMIntegrator(
        ode_function=ode_function, time_spacing=np.arange(num),
        scheme=scheme, initial_conditions={'y': 1.}, start_time=0., end_time=1.,
    )
elif integrator_name == 'implicit':
    integrator = ImplicitTMIntegrator(
        ode_function=ode_function, time_spacing=np.arange(num),
        scheme=scheme, initial_conditions={'y': 1.}, start_time=0., end_time=1.,
    )

prob = Problem(integrator)

if formulation == 'SAND' and integrator_name == 'vectorized':
    prob.driver = ScipyOptimizer()
    prob.driver.options['optimizer'] = 'SLSQP'
    prob.driver.options['tol'] = 1e-9
    prob.driver.options['disp'] = True

    integrator.add_subsystem('dummy_comp', IndepVarComp('dummy_var', val=1.0))
    integrator.add_objective('dummy_comp.dummy_var')

prob.setup()

if formulation == 'SAND' and integrator_name == 'vectorized':
    prob.run_driver()
else:
    prob.run_model()
# prob.check_partials(compact_print=True)
# prob.check_partials(compact_print=False)

print(prob['output_comp.y'])

from openmdao.api import view_model

# view_model(prob)