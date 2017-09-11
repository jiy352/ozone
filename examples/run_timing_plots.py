from ozone.doc_tests.test_timing_plot import Test

Test().test(savefig=True)



# import numpy as np
# import matplotlib.pylab as plt
# from six import iteritems
# import time
#
# from openmdao.api import ExplicitComponent, Problem, ScipyOptimizer, IndepVarComp
#
# from ozone.api import ODEFunction, ODEIntegrator
# from ozone.tests.ode_functions.simple_ode import LinearODEFunction, SimpleODEFunction, \
#     NonlinearODEFunction
# from ozone.utils.suppress_printing import nostdout
# from ozone.utils.misc import method_families
#
#
# ode_function = NonlinearODEFunction()
# ode_function = LinearODEFunction()
# # ode_function = SimpleODEFunction()
#
# initial_conditions = {'y': 1.}
# t0 = 1.e-7
# t1 = 1.e-6
#
# nums = [21, 26, 31, 36]
# # nums = [5]
# # nums = [11, 21, 31, 41]
#
# formulations = ['time-marching', 'solver-based', 'optimizer-based']
#
# colors = ['b', 'g', 'r', 'c', 'm', 'k']
#
#
# plt.figure(figsize=(20, 15))
#
# plot_index = 0
# for method_family_name, method_family in iteritems(method_families):
#     print(method_family_name)
#
#     plot_index += 1
#     plt.subplot(3, 3, plot_index)
#
#     method_name = method_family[1]
#
#     for j, formulation in enumerate(formulations):
#
#         step_sizes = np.zeros(len(nums))
#         run_times = np.zeros(len(nums))
#         for i, num in enumerate(nums):
#             times = np.linspace(t0, t1, num)
#
#             integrator = ODEIntegrator(ode_function, formulation, method_name,
#                 times=times, initial_conditions=initial_conditions)
#             prob = Problem(integrator)
#
#             if formulation == 'optimizer-based':
#                 prob.driver = ScipyOptimizer()
#                 prob.driver.options['optimizer'] = 'SLSQP'
#                 prob.driver.options['tol'] = 1e-9
#                 prob.driver.options['disp'] = True
#
#                 integrator.add_subsystem('dummy_comp', IndepVarComp('dummy_var', val=1.0))
#                 integrator.add_objective('dummy_comp.dummy_var')
#
#             with nostdout():
#                 prob.setup()
#                 time0 = time.time()
#                 prob.run_driver()
#                 time1 = time.time()
#
#             step_sizes[i] = (t1 - t0) / (num - 1)
#             run_times[i] = time1 - time0
#
#         plt.loglog(step_sizes, run_times, colors[j] + 'o-')
#         plt.loglog(
#             [step_sizes[0], step_sizes[-1]],
#             [run_times[0], run_times[0] * (step_sizes[0] / step_sizes[-1])],
#             colors[j] + ':',
#         )
#
#     legend_entries = []
#     for formulation in formulations:
#         legend_entries.append(formulation)
#         legend_entries.append('linear')
#
#     plt.title(method_name)
#     plt.legend(legend_entries)
#
# plt.savefig("time_vs_stepsize_plots.pdf")
