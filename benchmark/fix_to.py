import argparse as ap
import json
import os


def parse_args():
    parser = ap.ArgumentParser()
    parser.add_argument('dir', type=str)

    return parser.parse_args()


def main():
    args = parse_args()

    # find files recursively
    for root, dirs, files in os.walk(args.dir):
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r') as f:
                    res = json.load(f)

                for r in res["results"]:
                    if r["time"] > 3599:
                        r["time"] = 3600
                        r["models"] = None
                        r["model_count"] = None
                        r["enum_timed_out"] = True

                with open(file_path, 'w') as f:
                    json.dump(res, f, indent=4)


if __name__ == '__main__':
    main()
