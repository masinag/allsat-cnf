# Run benchmarks

To run the benchmarks, you need to install the `benchmark` extra:
```bash
pip install "..[benchmark]"
```

The benchmarks are organized in the following directories:
* `synthetic/` contains the synthetic Boolean and SMT(LRA) benchmarks
* `iscas85/` contains the ISCAS85 benchmarks
* `aig/` contains the AIG benchmarks
* `wmi/` contains the Weighted Model Integration benchmarks

To run a set of enumeration experiments, `cd` into the corresponding directory and run
`./run-enum.sh`.
Optionally, you can run `./run-sat.sh` to run also the satisfiability experiments.

Run  `./plot.sh` from this directory to generate the plots.