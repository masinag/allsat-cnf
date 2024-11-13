import os

import matplotlib.pyplot as plt
import pandas as pd

from .plotter import Plotter, Param


class CactusPlotter(Plotter):
    LINEWIDTH = 3

    def plot_time(self):
        self._plot("time", "Number of problems solved", "Cumulative time (s)")

    def _plot(self, param: Param, xlabel: str, ylabel: str):
        for problem_set in self.get_problem_sets():
            data_set = self.data[self.data.index.get_level_values(0) == problem_set].copy()
            self._plot_data(data_set, param, xlabel, ylabel, suffix=f"_{problem_set}")
        self._plot_legend()

    def _plot_data(self, data: pd.DataFrame, param: Param, xlabel: str, ylabel: str, suffix: str = ""):
        fig, ax = plt.subplots()
        # fill with None where "enum_timed_out" is True or None
        data.loc[data["enum_timed_out"].any(axis=1), param] = None
        data = data[param]
        modes = self.get_modes()
        for i, mode in enumerate(modes):
            ls = self.mode_styles[mode].linestyle
            color = self.mode_styles[mode].color
            label = self.mode_styles[mode].label
            series = data[mode.value].sort_values(ignore_index=True).cumsum()
            ax.plot(range(1, len(series) + 1), series, linewidth=self.LINEWIDTH, color=color, label=label,
                    linestyle=ls)

        n_instances = len(data)
        # ax.axhline(y=n_instances, color="black", linestyle="--", label="Total number of problems")

        # axes labels
        ax.set_xlabel(xlabel, fontsize=self.FONTSIZE)
        ax.set_ylabel(ylabel, fontsize=self.FONTSIZE)

        # axes ticks
        ax.tick_params(axis='both', which='major', labelsize=self.TICKSIZE)
        ax.tick_params(axis='both', which='minor', labelsize=self.TICKSIZE)

        outfile = os.path.join(self.output_dir, "{}_cactus{}{}.pdf".format(param, self.filename, suffix))
        fig.savefig(outfile, bbox_inches='tight')
        print("created {}".format(outfile))
        plt.close(fig)
        # plot *only* the legend on a different file

    def _plot_legend(self, suffix=""):
        legend_fig = plt.figure("Legend plot")
        modes = self.get_modes()
        handles = [plt.Line2D([0], [0], color=self.mode_styles[m].color, marker=self.mode_styles[m].marker,
                              linestyle=self.mode_styles[m].linestyle, linewidth=self.LINEWIDTH, markersize=10,
                              markeredgewidth=2, alpha=0.8) for m in modes]
        handles.append(plt.Line2D([0], [0], color="black", linestyle="--"))
        legend_fig.legend(handles, [self.mode_styles[m].label for m in modes] + ["Total number of problems"],
                          loc="center",
                          fontsize=self.FONTSIZE, ncol=len(modes) + 1)
        outfile_legend = os.path.join(self.output_dir, "legend{}.pdf".format(suffix))
        legend_fig.savefig(outfile_legend, bbox_inches='tight')
        print("created {}".format(outfile_legend))
        plt.close(legend_fig)
