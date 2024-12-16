# -*- coding: future_fstrings -*-
#
# Copyright (c) The acados authors.
#
# This file is part of acados.
#
# The 2-Clause BSD License
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.;
#
from matplotlib import pyplot as plt

from acados_template import AcadosOcp, AcadosOcpSolver, AcadosSimSolver
from acados_template.mpc_utils import AcadosCostConstraintEvaluator
from pendulum_model import export_pendulum_ode_model
from utils import plot_pendulum_eval, plot_pendulum
import numpy as np
import scipy.linalg
import math
from casadi import vertcat, SX

# Define constraints to make evaluation more challenging
constraint_par = {'omega_dot_min_1': -4,
                  'omega_dot_min_2': -6,
                  'iter_omega_change': 6,
                  'v_max': 5,
                  'F_max': 80}


def setup(x0, N_horizon, Tf, RTI=False):
    # create ocp object to formulate the OCP
    global constraint_par
    ocp = AcadosOcp()

    # set model
    model = export_pendulum_ode_model()
    omega_dot_min = SX.sym('omega_dot_min')

    ocp.model = model
    ocp.model.p = omega_dot_min
    ocp.model.con_h_expr = omega_dot_min - model.x[3]
    omega_dot_min_1 = constraint_par['omega_dot_min_1']
    ocp.parameter_values = np.array([omega_dot_min_1])

    nx = model.x.rows()
    nu = model.u.rows()
    ny = nx + nu
    ny_e = nx

    # set cost module
    ocp.cost.cost_type = 'NONLINEAR_LS'
    ocp.cost.cost_type_e = 'NONLINEAR_LS'

    Q_mat = 2 * np.diag([1e3, 1e3, 1e-2, 1e-2])
    R_mat = 2 * np.diag([1e-2])

    ocp.cost.W = scipy.linalg.block_diag(Q_mat, R_mat)
    ocp.cost.W_e = Q_mat * 10

    ocp.model.cost_y_expr = vertcat(model.x, model.u)
    ocp.model.cost_y_expr_e = model.x
    ocp.cost.yref = np.zeros((ny,))
    ocp.cost.yref_e = np.zeros((ny_e,))

    # set constraints
    ocp.constraints.lbu = np.array([-constraint_par['F_max']])
    ocp.constraints.ubu = np.array([+constraint_par['F_max']])

    ocp.constraints.idxbx = np.array([2])
    ocp.constraints.lbx = np.array([-constraint_par['v_max']])
    ocp.constraints.ubx = np.array([constraint_par['v_max']])

    ocp.constraints.idxbx_e = np.array([2])
    ocp.constraints.lbx_e = np.array([-constraint_par['v_max']])
    ocp.constraints.ubx_e = np.array([constraint_par['v_max']])

    ocp.constraints.idxsbx = np.array([0])
    ocp.constraints.lsbx = np.zeros((1,))
    ocp.constraints.usbx = np.zeros((1,))

    ocp.constraints.uh = np.array([0])
    ocp.constraints.lh = np.array([-10])
    ocp.constraints.idxsh = np.array([0])

    ocp.cost.zl = 2e3 * np.ones((2,))
    ocp.cost.Zl = 5e3 * np.ones((2,))
    ocp.cost.zu = ocp.cost.zl
    ocp.cost.Zu = ocp.cost.Zl

    ocp.constraints.idxsbx_e = np.array([0])
    ocp.constraints.lsbx_e = np.zeros((1,))
    ocp.constraints.usbx_e = np.zeros((1,))

    ocp.cost.zl_e = 1e3 * np.ones((1,))
    ocp.cost.Zl_e = 1e3 * np.ones((1,))
    ocp.cost.zu_e = ocp.cost.zl_e
    ocp.cost.Zu_e = ocp.cost.Zl_e

    ocp.constraints.x0 = x0
    ocp.constraints.idxbu = np.array([0])

    # set prediction horizon
    ocp.solver_options.N_horizon = N_horizon
    ocp.solver_options.tf = Tf

    ocp.solver_options.qp_solver = 'PARTIAL_CONDENSING_HPIPM'  # FULL_CONDENSING_QPOASES
    ocp.solver_options.hessian_approx = 'GAUSS_NEWTON'
    ocp.solver_options.integrator_type = 'IRK'
    ocp.solver_options.sim_method_newton_iter = 10

    if RTI:
        ocp.solver_options.nlp_solver_type = 'SQP_RTI'
    else:
        ocp.solver_options.nlp_solver_type = 'SQP'
        ocp.solver_options.globalization = 'MERIT_BACKTRACKING'  # turns on globalization
        ocp.solver_options.nlp_solver_max_iter = 150

    ocp.solver_options.qp_solver_cond_N = N_horizon

    solver_json = 'acados_ocp_' + model.name + '.json'
    acados_ocp_solver = AcadosOcpSolver(ocp, json_file=solver_json, save_p_global=True)

    # create an integrator with the same settings as used in the OCP solver.
    acados_integrator = AcadosSimSolver(ocp, json_file=solver_json)

    acados_evaluator = AcadosCostConstraintEvaluator(ocp, with_parametric_bounds=False)

    return acados_ocp_solver, acados_integrator, acados_evaluator


def update_comprehensive_dict(comprehensive_dict, input_dict):
    """
    Updates the global comprehensive_dict with the values from the input dictionary.
    Values for each key are stored in lists, which are appended to with each call.

    :param input_dict: A dictionary with keys and values to add to the comprehensive_dict.
    """
    for key, value in input_dict.items():
        if key not in comprehensive_dict:
            comprehensive_dict[key] = []  # Initialize the list if the key doesn't exist
        comprehensive_dict[key].append(value)  # Append the value to the list

    return comprehensive_dict


def main(use_RTI=False):
    global constraint_par
    x0 = np.array([0.0, np.pi, 0.0, 0.0])

    Tf = .8
    N_horizon = 40
    td = Tf/N_horizon

    ocp_solver, integrator, evaluator = setup(x0, N_horizon, Tf, use_RTI)

    nx = ocp_solver.acados_ocp.dims.nx
    nu = ocp_solver.acados_ocp.dims.nu

    Nsim = 100
    simX = np.zeros((Nsim + 1, nx))
    simU = np.zeros((Nsim, nu))
    eval_dict = {}

    simX[0, :] = x0

    if use_RTI:
        t_preparation = np.zeros((Nsim))
        t_feedback = np.zeros((Nsim))

    else:
        t = np.zeros((Nsim))

    # do some initial iterations to start with a good initial guess
    num_iter_initial = 5
    for _ in range(num_iter_initial):
        ocp_solver.solve_for_x0(x0_bar=x0)

    evaluator.update_all(ocp_solver)

    # closed loop
    for i in range(Nsim):

        # change constraint parameter in the middle of the simulation
        if i == constraint_par['iter_omega_change']:
            new_omega_dot_min = np.array([constraint_par['omega_dot_min_2']])
            for j in range(ocp_solver.acados_ocp.dims.N):
                ocp_solver.set(j, "p", new_omega_dot_min)
            evaluator.update_all(ocp_solver)

        if use_RTI:
            # preparation phase
            ocp_solver.options_set('rti_phase', 1)
            status = ocp_solver.solve()
            t_preparation[i] = ocp_solver.get_stats('time_tot')

            # set initial state
            ocp_solver.set(0, "lbx", simX[i, :])
            ocp_solver.set(0, "ubx", simX[i, :])

            # feedback phase
            ocp_solver.options_set('rti_phase', 2)
            status = ocp_solver.solve()
            t_feedback[i] = ocp_solver.get_stats('time_tot')

            simU[i, :] = ocp_solver.get(0, "u")

        else:
            # solve ocp and get next control input
            simU[i, :] = ocp_solver.solve_for_x0(x0_bar=simX[i, :])
            t[i] = ocp_solver.get_stats('time_tot')

        # evaluate the cost of the full trajectory
        solution_obj = ocp_solver.store_iterate_to_obj()
        cost_ext_eval = evaluator.evaluate_ocp_cost(solution_obj)
        cost_int_eval = ocp_solver.get_cost()
        rel_error_perc = np.abs(cost_ext_eval - cost_int_eval) / cost_int_eval * 100
        # formatted print relative error up to 3 decimal places
        print(f'cost_err_rel: {rel_error_perc:.8f} %')
        assert math.isclose(cost_ext_eval, cost_int_eval, rel_tol=1e-3)

        # simulate system
        simX[i + 1, :] = integrator.simulate(x=simX[i, :], u=simU[i, :])
        eval_iter = evaluator.evaluate(x=simX[i, :], u=simU[i, :])
        eval_dict = update_comprehensive_dict(eval_dict, eval_iter)

    # evaluate timings
    if use_RTI:
        # scale to milliseconds
        t_preparation *= 1000
        t_feedback *= 1000
        print(f'Computation time in preparation phase in ms: \
                min {np.min(t_preparation):.3f} median {np.median(t_preparation):.3f} max {np.max(t_preparation):.3f}')
        print(f'Computation time in feedback phase in ms:    \
                min {np.min(t_feedback):.3f} median {np.median(t_feedback):.3f} max {np.max(t_feedback):.3f}')
    else:
        # scale to milliseconds
        t *= 1000
        print(f'Computation time in ms: min {np.min(t):.3f} median {np.median(t):.3f} max {np.max(t):.3f}')

    # plot results
    model = ocp_solver.acados_ocp.model

    fix, axes = plot_pendulum_eval(
        np.linspace(0, td * Nsim, Nsim + 1),
        simU,
        simX,
        eval_dict,
        latexify=False,
        time_label=model.t_label,
        x_labels=model.x_labels,
        u_labels=model.u_labels)

    axes[2].axhline(constraint_par['v_max'], alpha=0.7, color='tab:red')
    axes[2].axhline(-constraint_par['v_max'], alpha=0.7, color='tab:red')

    constraint_omega_dot = np.empty(Nsim)
    constraint_omega_dot[:constraint_par['iter_omega_change']+1] = constraint_par['omega_dot_min_1']
    constraint_omega_dot[constraint_par['iter_omega_change']+1:] = constraint_par['omega_dot_min_2']
    axes[3].plot(np.linspace(0, td*Nsim, Nsim), constraint_omega_dot, alpha=0.7, color='tab:red')

    axes[-1].set_ylim([-1.2 * constraint_par['F_max'], 1.2 * constraint_par['F_max']])
    axes[-1].axhline(constraint_par['F_max'], alpha=0.7, color='tab:red')
    axes[-1].axhline(-constraint_par['F_max'], alpha=0.7, color='tab:red')
    plt.show()


if __name__ == '__main__':
    main(use_RTI=True)
