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

import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import os

from mpc_parameters import MPCParam


def get_latex_plot_params():
    params = {'backend': 'ps',
            'text.latex.preamble': r"\usepackage{gensymb} \usepackage{amsmath}",
            'axes.labelsize': 12,
            'axes.titlesize': 12,
            'legend.fontsize': 12,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'text.usetex': True,
            'font.family': 'serif'
    }

    return params


def plot_timings(timing_dict):
    # latexify plot
    params = get_latex_plot_params()
    matplotlib.rcParams.update(params)

    print("timings\t\tmin\tmean\tmax\n--------------------------------")
    for k, v in timing_dict.items():
        print(f"{k:10}\t{np.min(v):.3f}\t {np.mean(v):.3f}\t {np.max(v):.3f}")

    medianprops = dict(linestyle='-', linewidth=2.5, color='darkgreen')
    green_square = dict(markerfacecolor='palegreen', marker='D')
    fig = plt.figure(0)
    ax = fig.add_subplot(111)
    ax.boxplot(timing_dict.values(), vert=False,
        flierprops=green_square, \
        medianprops=medianprops, showmeans=False)
    ax.set_yticklabels(timing_dict.keys())
    plt.grid()
    plt.xlabel('CPU time [ms]')
    plt.tight_layout()

    if not os.path.exists('figures'):
        os.makedirs('figures')
    plt.savefig(os.path.join("figures", "timings_diff_drive.pdf"),
        bbox_inches='tight', transparent=True, pad_inches=0.05)


def compute_min_dis(cfg:MPCParam, s:np.ndarray)->float:
    min_dist = np.inf
    for idx_obs in range(cfg.num_obs):
        min_dist = np.min([min_dist, \
            np.linalg.norm(s[:2] - cfg.obs_pos[idx_obs,:])-cfg.obs_radius[idx_obs]])
    return min_dist