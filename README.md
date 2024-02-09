# On CNF encoding for SAT and SMT enumeration
Code for the following papers:

Short version: [On CNF encoding for Disjoint SAT enumeration](https://doi.org/10.4230/LIPIcs.SAT.2023.14)<br/>
Gabriele Masina, Giuseppe Spallitta and Roberto Sebastiani, SAT '23.

Extended version: [On CNF encoding for SAT and SMT enumeration](https://arxiv.org/abs/2303.14971)<br/>
Gabriele Masina, Giuseppe Spallitta and Roberto Sebastiani, ArXiv.

##  Install
Requires Python >= 3.10.
```bash
pip install -e .
pysmt-install --msat
```

##  Run benchmarks
See the README.md in the `benchmark/` directory.

## Run examples
E.g., to run the example analyzed in the paper:
```bash
python3 examples/example0.py
```

##  Run tests
```bash
pytest test/
``` 
