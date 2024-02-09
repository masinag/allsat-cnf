import itertools
import math
import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import LogFormatterSciNotation

from .plotter import Plotter, Param
from ..parsing import Mode


class CustomTicker(LogFormatterSciNotation):

    def __init__(self, models_timeout, *args, **kwargs):
        LogFormatterSciNotation.__init__(self, *args, **kwargs)
        self.models_timeout = models_timeout

    def __call__(self, x, pos=None):
        if x == self.models_timeout:
            return "TO"
        else:
            return LogFormatterSciNotation.__call__(self, x, pos)


class ScatterPlotter(Plotter):

    def plot_models_all_vs_all(self, separate_problem_sets=False):
        self._plot_all_vs_all("models", r"Size of $\mathcal{T}\hspace{-.1cm}\mathcal{A}$", separate_problem_sets)

    def plot_time_all_vs_all(self, separate_problem_sets=False):
        self._plot_all_vs_all("time", "Time (s)", separate_problem_sets)

    def plot_size_all_vs_all(self, separate_problem_sets=False):
        self._plot_all_vs_all("n_clauses", r"\# of clauses", separate_problem_sets)

    def _plot_all_vs_all(self, param: Param, param_label: str, separate_problem_sets):
        modes = self.get_modes()
        size = len(self.data)
        for mode1, mode2 in itertools.combinations(modes, 2):
            if mode1 != mode2:
                self._plot(param, param_label, mode1, mode2, separate_problem_sets)
                assert size == len(self.data)
        self._plot_legend("all")

    def _plot(self, param: Param, param_label: str, modex: Mode, modey: Mode, separate_problem_sets):
        if separate_problem_sets:
            for problem_set in self.get_problem_sets():
                data_set = self.data[self.data.index.get_level_values(0) == problem_set]
                self._plot_data(data_set, param, param_label, modex, modey, subdir=problem_set)
        else:
            self._plot_data(self.data, param, param_label, modex, modey, subdir="all")

    def _plot_data(self, data: pd.DataFrame, param: Param, param_label: str, modex: Mode, modey: Mode,
                   suffix: str = "", subdir: str = ""):
        fig, ax = plt.subplots()

        for problem_set in self.get_problem_sets():
            style = self.problem_set_styles[problem_set]
            color, marker = style.color, style.marker
            data_set = data[data.index.get_level_values(0) == problem_set]
            ax.scatter(x=data_set[(param, modex.value)],
                       y=data_set[(param, modey.value)],
                       color=color, alpha=0.8, marker=marker)
            ax.set_xscale("log")
            ax.set_yscale("log")

        # plot timeout lines
        if param == "time" and self.timeout is not None:
            self.plot_timeout_lines(ax, self.timeout)
        elif param == "models" and self.timeout_models is not None:
            self.plot_timeout_lines(ax, self.timeout_models)
        # axes labels
        ax.set_xlabel(f"{self.mode_styles[modex].label} ({param_label})", fontsize=self.FONTSIZE)
        ax.set_ylabel(f"{self.mode_styles[modey].label} ({param_label})", fontsize=self.FONTSIZE)
        ax.tick_params(axis='both', which='major', labelsize=self.TICKSIZE)
        ax.tick_params(axis='both', which='minor', labelsize=self.TICKSIZE)
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        ax.set_xlim(1, max(x1, y1))
        ax.set_ylim(1, max(x1, y1))
        self.plot_diagonal_lines(ax, max(data[(param, modex.value)].max(), data[(param, modey.value)].max()))
        # save figure
        if subdir:
            # ensure subdir exists or create it
            output_dir = os.path.join(self.output_dir, subdir)
            print("Creating subdir: ", output_dir)
            os.makedirs(output_dir, exist_ok=True)
            assert os.path.exists(output_dir)
        else:
            output_dir = self.output_dir
        outfile = os.path.join(output_dir,
                               "{}_compare_{}_vs_{}{}{}.pdf".format(param, modex.value, modey.value, self.filename,
                                                                    suffix))
        ax.set_aspect("equal")
        fig.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.close(fig)

    def plot_diagonal_lines(self, ax, limit):
        k = 1
        ax.axline((1, 1), (10, 10), color="black", linestyle=":", alpha=0.5, zorder=100000)
        for i in range(min(10, int(math.log10(limit)) + 1)):
            p1 = 10 ** i
            p2 = 10 ** (i + 1)
            ax.axline((p1, 1 * k), (p2, 10 * k), color="black", linestyle=":", alpha=0.2, zorder=100000)
            ax.axline((1, p1 / k), (10, p2 / k), color="black", linestyle=":", alpha=0.2, zorder=100000)

    def plot_timeout_lines(self, ax, timeout):
        ax.axhline(y=timeout, color="black", linestyle="--", alpha=0.5, zorder=100000)
        ax.axvline(x=timeout, color="black", linestyle="--", alpha=0.5, zorder=100000)
        ax.xaxis.set_major_formatter(CustomTicker(timeout))
        ax.yaxis.set_major_formatter(CustomTicker(timeout))

    def _plot_legend(self, subdir=""):
        # plot *only* the legend on a different file
        legend_fig = plt.figure("Legend plot")
        problem_sets = self.get_problem_sets()
        handles = [
            plt.Line2D([0], [0], color=self.problem_set_styles[ps].color, marker=self.problem_set_styles[ps].marker,
                       linestyle="None", markersize=10, markeredgewidth=2, alpha=0.8) for ps in problem_sets]
        legend_fig.legend(handles, [self.problem_set_styles[ps].label for ps in problem_sets], loc="center",
                          fontsize=self.FONTSIZE, ncol=len(problem_sets))
        output_dir = os.path.join(self.output_dir, subdir) if subdir else self.output_dir
        outfile = os.path.join(output_dir, "legend{}.pdf".format(self.filename))
        legend_fig.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.close(legend_fig)
