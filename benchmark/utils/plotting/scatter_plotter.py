import itertools
import os

import matplotlib.pyplot as plt
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
        self._plot_all_vs_all("models")

    def plot_time_all_vs_all(self):
        self._plot_all_vs_all("time")

    def plot_size_all_vs_all(self):
        self._plot_all_vs_all("n_clauses")

    def _plot_all_vs_all(self, param: Param):
        modes = self.get_modes()
        for mode1, mode2 in itertools.combinations(modes, 2):
            if mode1 != mode2:
                self._plot_scatter(param, mode1, mode2)

    def _plot_scatter(self, param: Param, modex: Mode, modey: Mode):
        data = self.data[param]
        ax = data.plot(kind="scatter", x=modex.value, y=modey.value, loglog=self.logscale,
                       color="blue", marker="x")
        if param == "time" and self.timeout is not None:
            self.plot_timeout_lines(ax, self.timeout)
        if param == "models" and self.timeout_models is not None:
            self.plot_timeout_lines(ax, self.timeout_models)
        # axes labels
        plt.xlabel(f"{self.name_mapping[modex]} ({param})", fontsize=self.FONTSIZE)
        plt.ylabel(f"{self.name_mapping[modey]} ({param})", fontsize=self.FONTSIZE)
        plt.xticks(fontsize=self.TICKSIZE)
        plt.yticks(fontsize=self.TICKSIZE)
        # plot bisector
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        ax.plot([min(x0, y0), max(x1, y1)], [min(x0, y0), max(x1, y1)], color="black", linestyle="dotted")

        # save figure
        outfile = os.path.join(self.output_dir,
                               "{}_compare_{}_vs_{}{}.pdf".format(param, modex.value, modey.value, self.filename))
        plt.gca().set_aspect("equal")
        plt.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.clf()

    def plot_timeout_lines(self, ax, timeout):
        ax.axhline(y=timeout, color="black", linestyle="--")
        ax.axvline(x=timeout, color="black", linestyle="--")
        ax.xaxis.set_major_formatter(CustomTicker(timeout))
        ax.yaxis.set_major_formatter(CustomTicker(timeout))
