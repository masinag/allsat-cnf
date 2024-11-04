# Run benchmarks

## Install dependencies
To run the benchmarks, you need to install the `benchmark` extra:
```bash
pip install "..[benchmark]"
```

## 3rd party solvers
`TabularAllSAT`, `TabularAllSMT`, `D4`, and `decdnnf_rs` are 3rd party solvers.

They must be compiled and their binaries must be in the `bin` directory.

Details are provided in `bin/README.md`.

## Generate and run the benchmark
For each set of benchmarks in:
* `aig` (Boolean)
* `iscas85` (Boolean)
* `syn_bool` (Boolean)
* `syn_lra` (SMT-LRA)
* `wmi` (SMT-LRA)

You can generate the benchmarks using the scripts:
```bash
./run_<bench>_gen.sh
```

Then, you can run the enumeration experiments with
```bash
./run_<bench>_eval_enum_<solver>
```
where `<solver>` can be:
* `msat` for MathSAT, for all benchmarks
* `tabularallsat` for TabularAllSAT, only for Boolean benchmarks
* `tabularallsmt` for TabularAllSMT, only for SMT-LRA benchmarks
* `d4` for D4, only for Boolean benchmarks. D4 is run both for counting and enumeration in combination with `decdnnf_rs`.

You can also run the satisfiability experiments with
```bash
./run_<bench>_eval_msat_sat
```

The results can then be plotted using
```bash
./plot.sh
```
