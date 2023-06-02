import os

import matplotlib.pyplot as plt

from .plotter import Plotter, Param


class ECDFPlotter(Plotter):
    LINEWIDTH = 3

    def plot_time(self):
        self._plot("time", "Time(s)", "Number of problems solved")

    def _plot(self, param: Param, xlabel: str, ylabel: str):
        # set the value of param where "enum_timed_out" is True to None
        data = self.data[param].copy()
        data[self.data["enum_timed_out"]] = None
        modes = self.get_modes()

        for i, mode in enumerate(modes):
            ls = self.linestyles[mode]
            series = data[mode.value].sort_values(ignore_index=True).cumsum()
            plt.plot(series, range(1, len(series) + 1), linewidth=self.LINEWIDTH,
                     color=self.colors[mode], label=self.name_mapping[mode], linestyle=ls)

        n_instances = len(data)
        plt.axhline(y=n_instances, color="black", linestyle="--", label="Total number of problems")

        # if self.logscale:
        #     plt.xscale("log")

        # legend
        plt.legend(loc="lower right", fontsize=self.FONTSIZE*0.95)
        # axes labels
        plt.xlabel(xlabel, fontsize=self.FONTSIZE)
        plt.ylabel(ylabel, fontsize=self.FONTSIZE)

        plt.xticks(fontsize=self.TICKSIZE)
        plt.yticks(fontsize=self.TICKSIZE)

        outfile = os.path.join(self.output_dir, "{}_ecdf{}.pdf".format(param, self.filename))
        plt.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.clf()
