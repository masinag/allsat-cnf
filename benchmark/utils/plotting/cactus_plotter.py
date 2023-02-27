import os

import matplotlib.pyplot as plt

from .plotter import Plotter, Param


class CactusPlotter(Plotter):

    def plot_models(self):
        self._plot("models", "Number of problems", "Number of models")

    def plot_time(self):
        self._plot("time", "Number of problems", "Time (s)")

    def _plot(self, param: Param, xlabel: str, ylabel: str):
        n_problems = max(self.data.index) + 1

        plt.figure(figsize=self.FIGSIZE)

        modes = self.get_modes()
        for mode in modes:
            self.data[param][mode.value] \
                .sort_values(ignore_index=True) \
                .plot(linewidth=self.LINEWIDTH, color=self.colors[mode], label=mode)

        # legend
        plt.legend(loc=6, fontsize=self.FONTSIZE)
        # axes labels
        plt.xlabel(xlabel, fontsize=self.FONTSIZE)
        plt.ylabel(ylabel, fontsize=self.FONTSIZE)

        outfile = os.path.join(self.output_dir, "{}{}.png".format(param, self.filename))
        plt.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.clf()
