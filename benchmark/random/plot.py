import argparse
import json
import os
import sys
from typing import List, Literal

import matplotlib.pyplot as plt
# import numpy as np
import pandas as pd

Param = Literal["time", "models"]

plt.style.use("ggplot")
fs = 10  # font size
ticks_fs = 15
lw = 2.5  # line width
figsize = (10, 8)
label_step = 5
ORDER = ["TTA", "AUTO", "ACT", "POL", "NNF_POL", "CND"]
COLOR = {
    "AUTO": "red",
    "TTA": "blue",
    "ACT": "green",
    "POL": "orange",
    "NNF_POL": "purple",
    "CND": "brown",
}
ORDER += [f"{mode}_REP" for mode in ORDER]
COLOR.update({f"{mode}_REP": COLOR[mode] for mode in COLOR})


def error(msg=""):
    print(msg)
    sys.exit(1)


def get_input_files(input_dirs: List[str]) -> List[str]:
    input_files = []
    for input_dir in input_dirs:
        if not os.path.exists(input_dir):
            error("Input folder '{}' does not exists".format(input_dir))
        for filename in os.listdir(input_dir):
            filepath = os.path.join(input_dir, filename)
            if os.path.isfile(filepath):
                _, ext = os.path.splitext(filepath)
                if ext == ".json":
                    input_files.append(filepath)
    if not input_files:
        error("No .json file found")
    input_files = sorted(input_files)
    print("Files found:\n\t{}".format("\n\t".join(input_files)))
    return input_files


def parse_inputs(input_files: List[str], with_repetitions: bool) -> pd.DataFrame:
    data = []
    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        mode = result_out["mode"]
        if with_repetitions != ("REP" in mode):
            continue
        for result in result_out["results"]:
            result["mode"] = mode
        data.extend(result_out["results"])

    return pd.DataFrame(data)


def scatter(outdir: str, data: pd.DataFrame, param: Param, filename: str, with_repetitions: bool, logscale=False):
    data = data[param]
    ax = plt.gca()
    modes = data.columns.get_level_values(0).unique()
    auto_mode = f"AUTO{'_REP' if with_repetitions else ''}"
    tta_mode = f"TTA{'_REP' if with_repetitions else ''}"
    for mode in filter(lambda x: x in modes, ORDER):
        if mode not in [auto_mode, tta_mode]:
            ax = data.plot(kind="scatter", x=auto_mode, y=mode, logx=logscale, label=mode, color=COLOR[mode],
                           marker="x", ax=ax)
    ax.set_aspect("equal")
    x0, x1 = ax.get_xlim()
    y0, y1 = ax.get_ylim()
    ax.set_xlim(min(x0, y0), max(x1, y1))
    ax.set_ylim(min(x0, y0), max(x1, y1))
    plt.legend(loc=6, fontsize=fs)
    # axes labels
    plt.xlabel(f"MathSAT CNF ({param})", fontsize=fs)
    plt.ylabel(f"Custom CNF ({param})", fontsize=fs)
    # save figure
    outfile = os.path.join(outdir, "{}_scatter{}.png".format(param, filename))
    plt.savefig(outfile, bbox_inches='tight')
    print("created {}".format(outfile))
    plt.clf()


def plot_data(outdir: str, data: pd.DataFrame, param: Param, xlabel: str, filename: str):
    n_problems = max(data.index) + 1

    plt.figure(figsize=figsize)

    # modes = data.columns.get_level_values(0).unique()
    # modes = [mode for mode in ORDER if mode in modes]
    data[param].plot(linewidth=lw, marker="x")

    ylabel = param

    # legend
    plt.legend(loc=6, fontsize=fs)
    # axes labels
    plt.xlabel(xlabel, fontsize=fs)
    plt.ylabel(ylabel, fontsize=fs)
    # xticks
    # positions = list(range(0, n_problems, label_step))
    # labels = list(range(frm or 0, to or total_problems, label_step))

    # plt.xticks(positions, labels, fontsize=ticks_fs)
    # plt.yticks(fontsize=ticks_fs, rotation=0)
    # plt.subplots_adjust(wspace=0.3, hspace=0.3)
    # if title:
    #     plt.title(title, fontsize=fs)

    outfile = os.path.join(outdir, "{}{}.png".format(param, filename))
    plt.savefig(outfile, bbox_inches='tight')
    print("created {}".format(outfile))
    plt.clf()


def group_data(data: pd.DataFrame):
    # aggregate and compute the mean for each query
    data = data \
        .groupby(["filename", "mode"]) \
        .aggregate(time=("time", "min"),
                   models=("models", "min")) \
        .unstack().reset_index(drop=True)

    # sort by increasing number of models
    modes = data.columns.get_level_values(0).unique()
    modes = [mode for mode in ORDER if mode in modes]
    sort_by = [(mode, "models") for mode in modes]
    data.sort_values(by=sort_by, inplace=True, ignore_index=True)
    return data


def parse_args():
    parser = argparse.ArgumentParser(description="Plot results")
    parser.add_argument(
        "input", nargs="+", help="Folder and/or files containing result files as .json")
    parser.add_argument("-o", "--output", default=os.getcwd(),
                        help="Output folder where to put the plots (default: cwd)")
    parser.add_argument("-f", "--filename", default="",
                        help="Filename suffix (default: '')")
    parser.add_argument("-r", "--with-repetitions", action="store_true", default=False,
                        help="Plot results for TA with repetitions")
    # parser.add_argument("--cactus", action="store_true",
    #                     help="If true use cactus plot")
    return parser.parse_args()


def main():
    args = parse_args()
    inputs: List[str] = args.input
    output_dir: str = args.output
    filename: str = args.filename
    with_repetitions: bool = args.with_repetitions

    if not os.path.exists(output_dir):
        error("Output folder '{}' does not exists".format(output_dir))

    input_files = get_input_files(inputs)
    data: pd.DataFrame = parse_inputs(input_files, with_repetitions)
    data: pd.DataFrame = group_data(data)
    xlabel = "Problem instances"
    plot_data(output_dir, data, "time", xlabel, filename)
    plot_data(output_dir, data, "models", xlabel, filename)
    scatter(output_dir, data, "time", filename, with_repetitions)
    scatter(output_dir, data, "models", filename, with_repetitions)


if __name__ == "__main__":
    main()
