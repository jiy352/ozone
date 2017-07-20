import numpy as np
from six import iteritems

from openmdao.api import Group, IndepVarComp, NewtonSolver, DirectSolver, DenseJacobian

from openode.integrators.integrator import Integrator
from openode.components.vectorized_step_comp import VectorizedStepComp
from openode.components.vectorized_stage_comp import VectorizedStageComp
from openode.components.vectorized_output_comp import VectorizedOutputComp
from openode.utils.var_names import get_name


class VectorizedIntegrator(Integrator):
    """
    Integrate an explicit scheme with a relaxed time-marching approach.
    """

    def initialize(self):
        super(VectorizedIntegrator, self).initialize()

        self.metadata.declare('formulation', default='MDF', values=['MDF', 'SAND'])

    def setup(self):
        super(VectorizedIntegrator, self).setup()

        coupled_group = Group()
        self.add_subsystem('coupled_group', coupled_group)

        formulation = self.metadata['formulation']
        ode_function = self.metadata['ode_function']

        states, time_units, times = self._get_meta()
        glm_A, glm_B, glm_U, glm_V, num_stages, num_step_vars = self._get_scheme()

        num_time_steps = len(times)

        if formulation == 'SAND':
            comp = IndepVarComp()
            for state_name, state in iteritems(states):
                comp.add_output('Y:%s' % state_name,
                    shape=(num_time_steps - 1, num_stages,) + state['shape'],
                    units=state['units'])
                comp.add_design_var('Y:%s' % state_name)
            coupled_group.add_subsystem('desvars_comp', comp)

        comp = self._create_ode((num_time_steps - 1) * num_stages)
        coupled_group.add_subsystem('ode_comp', comp)
        self.connect(
            'time_comp.abscissa_times',
            ['.'.join(('coupled_group.ode_comp', t)) for t in ode_function._time_options['targets']],
        )

        comp = VectorizedStepComp(states=states, time_units=time_units,
            num_time_steps=num_time_steps, num_stages=num_stages, num_step_vars=num_step_vars,
            glm_B=glm_B, glm_V=glm_V,
        )
        coupled_group.add_subsystem('vectorized_step_comp', comp)
        self.connect('time_comp.h_vec', 'coupled_group.vectorized_step_comp.h_vec')
        self._connect_states(
            self._get_names('starting_comp', 'y_new'),
            self._get_names('coupled_group.vectorized_step_comp', 'y0'),
        )

        comp = VectorizedStageComp(states=states, time_units=time_units,
            num_time_steps=num_time_steps, num_stages=num_stages, num_step_vars=num_step_vars,
            glm_A=glm_A, glm_U=glm_U,
        )
        coupled_group.add_subsystem('vectorized_stage_comp', comp)
        self.connect('time_comp.h_vec', 'coupled_group.vectorized_stage_comp.h_vec')

        promotes_states = []
        for state_name in states:
            out_state_name = get_name('state', state_name)
            promotes_states.append(out_state_name)

        comp = VectorizedOutputComp(states=states,
            num_time_steps=num_time_steps, num_step_vars=num_step_vars,
        )
        self.add_subsystem('output_comp', comp, promotes_outputs=promotes_states)
        self._connect_states(
            self._get_names('coupled_group.vectorized_step_comp', 'y'),
            self._get_names('output_comp', 'y'),
        )

        for state_name, state in iteritems(states):
            size = np.prod(state['shape'])
            shape = state['shape']

            src_indices = np.arange((num_time_steps - 1) * num_stages * size)
            coupled_group.connect(
                'ode_comp.%s' % state['rate_target'],
                'vectorized_step_comp.{}'.format(get_name('F', state_name)),
                src_indices=src_indices,
            )
            coupled_group.connect(
                'ode_comp.%s' % state['rate_target'],
                'vectorized_stage_comp.{}'.format(get_name('F', state_name)),
                src_indices=src_indices,
            )

        ###
        self._connect_states(
            self._get_names('coupled_group.vectorized_step_comp', 'y'),
            self._get_names('coupled_group.vectorized_stage_comp', 'y'),
        )

        if formulation == 'MDF':
            self._connect_states(
                self._get_names('coupled_group.vectorized_stage_comp', 'Y_out'),
                self._get_names('coupled_group.ode_comp', 'state_targets'),
            )
        elif formulation == 'SAND':
            self._connect_states(
                self._get_names('coupled_group.desvars_comp', 'Y'),
                self._get_names('coupled_group.ode_comp', 'state_targets'),
            )
            self._connect_states(
                self._get_names('coupled_group.desvars_comp', 'Y'),
                self._get_names('coupled_group.vectorized_stage_comp', 'Y_in'),
            )
            for state_name, state in iteritems(states):
                coupled_group.add_constraint('vectorized_stage_comp.Y_out:%s' % state_name, equals=0.)

        if formulation == 'MDF':
            coupled_group.nonlinear_solver = NewtonSolver(iprint=2, maxiter=100)
            coupled_group.linear_solver = DirectSolver()
            coupled_group.jacobian = DenseJacobian()
