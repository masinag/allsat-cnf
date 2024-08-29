import argparse
import json

import pandas as pd

from benchmark.io.file import get_input_files


def parse_inputs(input_files: list[str]) -> pd.DataFrame:
    data = []

    for filename in input_files:
        with open(filename) as f:
            result_out = json.load(f)
        if result_out["with_repetitions"]:
            # print(f"Skipping {filename} since it contains repetitions")
            continue
        # print(f"Found {filename}")
        mode = result_out["mode"]

        for result in result_out["results"]:
            if "model_count" not in result:
                # print(f"Skipping {result['filename']} since it does not contain model count")
                continue
            data.append(
                {
                    "filename": result["filename"],
                    "model_count": str(result["model_count"]),
                    "mode": mode,
                }
            )

    return pd.DataFrame(data)


def parse_args():
    parser = argparse.ArgumentParser(description="Check results")
    parser.add_argument("inputs", nargs="+", help="Folder and/or files containing result files as .json")
    return parser.parse_args()

def check_data(data: pd.DataFrame):
    errors = []
    n_checked = 0
    for g, d in data.groupby("filename"):
        vc = d["model_count"].value_counts()
        # remove the "None" key
        vc = vc[vc.index != "None"]
        if len(vc) > 1:
            errors.append((g, vc))
        else:
            n_checked += vc.sum()
    if errors:
        s = "\n".join(f"{g}:\n{vc}" for g, vc in errors)
        raise ValueError(f"Errors found:\n{s}")
    else:
        print(f"Checked {n_checked} results")

def main():
    args = parse_args()
    input_files = get_input_files(args.inputs)
    data = parse_inputs(input_files)
    check_data(data)


if __name__ == "__main__":
    main()
