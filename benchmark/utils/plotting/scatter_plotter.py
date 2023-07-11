import itertools
import math
import os

import matplotlib.pyplot as plt
import numpy as np
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

    def plot_models_all_vs_all(self):
        self._plot_all_vs_all("models", r"Size of $\mathcal{T}\hspace{-.1cm}\mathcal{A}$")

    def plot_time_all_vs_all(self):
        self._plot_all_vs_all("time", "Time (s)")

    def plot_size_all_vs_all(self):
        self._plot_all_vs_all("n_clauses", r"\# of clauses")

    def _plot_all_vs_all(self, param: Param, param_label: str):
        modes = self.get_modes()
        for mode1, mode2 in itertools.combinations(modes, 2):
            if mode1 != mode2:
                self._plot_scatter(param, param_label, mode1, mode2)

    def _plot_scatter(self, param: Param, param_label: str, modex: Mode, modey: Mode):
        data = self.data[param]
        ax = data.plot(kind="scatter", x=modex.value, y=modey.value, color="blue", marker="x", loglog=self.logscale)

        if param == "time" and self.timeout is not None:
            self.plot_timeout_lines(ax, self.timeout)
        if param == "models" and self.timeout_models is not None:
            self.plot_timeout_lines(ax, self.timeout_models)
        # axes labels
        plt.xlabel(f"{self.name_mapping[modex]} ({param_label})", fontsize=self.FONTSIZE)
        plt.ylabel(f"{self.name_mapping[modey]} ({param_label})", fontsize=self.FONTSIZE)
        plt.xticks(fontsize=self.TICKSIZE)
        plt.yticks(fontsize=self.TICKSIZE)

        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        ax.set_xlim(1, max(x1, y1))
        ax.set_ylim(1, max(x1, y1))
        self.plot_diagonal_lines(ax, max(data[modex.value].max(), data[modey.value].max()))

        # save figure
        outfile = os.path.join(self.output_dir,
                               "{}_compare_{}_vs_{}{}.pdf".format(param, modex.value, modey.value, self.filename))
        plt.gca().set_aspect("equal")
        plt.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.clf()

    def plot_diagonal_lines(self, ax, limit):
        k = 1
        ax.axline((1, 1), (10, 10), color="black", linestyle=":", alpha=0.8)
        for i in range(min(5, int(math.log10(limit)) + 1)):
            p1 = 10 ** i
            p2 = 10 ** (i + 1)
            ax.axline((p1, 1 * k), (p2, 10 * k), color="black", linestyle=":", alpha=0.2)
            ax.axline((1, p1 / k), (10, p2 / k), color="black", linestyle=":", alpha=0.2)

    def plot_timeout_lines(self, ax, timeout):
        ax.axhline(y=timeout, color="black", linestyle="--")
        ax.axvline(x=timeout, color="black", linestyle="--")
        ax.xaxis.set_major_formatter(CustomTicker(timeout))
        ax.yaxis.set_major_formatter(CustomTicker(timeout))
