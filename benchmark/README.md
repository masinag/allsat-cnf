# Run benchmarks

## Install dependencies
To run the benchmarks, you need to install the `benchmark` extra:
```bash
pip install "..[benchmark]"
```

## Generate and run the benchmark
For each set of benchmarks in:
* `aig`
* `iscas85`
* `syn_bool`
* `syn_lra`
* `wmi`

You can generate the benchmarks using the scripts:
```bash
./run_<bench>_gen.sh
```

Then, you can run the enumeration experiments with
```bash
./run_<bench>_eval_enum
```

You can also run the satisfiability experiments with
```bash
./run_<bench>_eval_sat
```

The results can then be plotted using
```bash
./plot.sh
```
