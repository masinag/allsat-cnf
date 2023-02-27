import itertools
import os

import matplotlib.pyplot as plt

from .plotter import Plotter, Param
from ..parsing import Mode


class ScatterPlotter(Plotter):

    def plot_models_all_vs_all(self):
        self._plot_all_vs_all("models")

    def plot_time_all_vs_all(self):
        self._plot_all_vs_all("time")

    def _plot_all_vs_all(self, param: Param):
        modes = self.get_modes()
        for mode1, mode2 in itertools.combinations(modes, 2):
            if mode1 != mode2:
                self._plot_scatter(param, mode1, mode2)

    def _plot_scatter(self, param: Param, modex: Mode, modey: Mode):
        data = self.data[param]
        ax = data.plot(kind="scatter", x=modex.value, y=modey.value, logy=self.logscale, color=self.colors[modex],
                       marker="x")
        # plot bisector
        x0, x1 = ax.get_xlim()
        y0, y1 = ax.get_ylim()
        ax.plot([min(x0, y0), max(x1, y1)], [min(x0, y0), max(x1, y1)], color="black", linestyle="--")
        if not self.logscale:
            ax.set_aspect("equal")
            x0, x1 = ax.get_xlim()
            y0, y1 = ax.get_ylim()
            ax.set_xlim(min(x0, y0), max(x1, y1))
            ax.set_ylim(min(x0, y0), max(x1, y1))
        plt.legend(loc=6, fontsize=self.FONTSIZE)
        # axes labels
        plt.xlabel(f"{modex.value} ({param})", fontsize=self.FONTSIZE)
        plt.ylabel(f"{modey.value} ({param})", fontsize=self.FONTSIZE)
        # save figure
        outfile = os.path.join(self.output_dir,
                               "{}_compare_{}_vs_{}{}.png".format(param, modex.value, modey.value, self.filename))
        plt.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.clf()
