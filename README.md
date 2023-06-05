# On CNF encoding for SAT enumeration
Code for the paper "On CNF encoding for SAT enumeration"

Short version: [On CNF encoding for Disjoint SAT enumeration](https://doi.org/10.4230/LIPIcs.SAT.2023.14)<br/>
Gabriele Masina, Giuseppe Spallitta and Roberto Sebastiani, SAT '23.

Extended version: [On CNF encoding for SAT enumeration](https://arxiv.org/abs/2303.14971)<br/>
Gabriele Masina, Giuseppe Spallitta and Roberto Sebastiani, ArXiv.

##  Install
Requires Python >= 3.8.
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
