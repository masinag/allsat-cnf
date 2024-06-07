# On CNF encoding for SAT and SMT enumeration
Code for the following papers:

Short version: [On CNF encoding for Disjoint SAT enumeration](https://doi.org/10.4230/LIPIcs.SAT.2023.14)<br/>
Gabriele Masina, Giuseppe Spallitta and Roberto Sebastiani, SAT '23.<br/>
[Code for the short version](https://github.com/masinag/allsat-cnf/releases/tag/SAT23)

Extended version: [On CNF encoding for SAT and SMT enumeration](https://arxiv.org/abs/2303.14971)<br/>
Gabriele Masina, Giuseppe Spallitta and Roberto Sebastiani, ArXiv.

##  Install
Requires Python >= 3.10.

### Remote installation
If you only want to use the package as a library, you can install it directly from GitHub with the following commands.
```bash
pip install git+https://github.com/masinag/allsat-cnf.git
pysmt-install --msat
```
Then see the `examples/` folder for usage examples.

### Local installation
Otherwise, you can clone the repository and then install the package from it.
```bash
git clone https://github.com/masinag/allsat-cnf.git
cd allsat-cnf
pip install -e .
pysmt-install --msat
```
Then see the `examples/` folder for usage examples.

For running the benchmarks, also install the `[benchmark]` extra:
```bash
pip install -e ".[benchmark]"
```

For development, install the `[dev]` extra:
```bash
pip install -e ".[dev]"
```

##  Run benchmarks
See the README.md in the `benchmark/` directory.

## Run examples
E.g., to run the example of the paper:
```bash
python3 examples/example0.py
```

##  Run tests
```bash
pytest test/
``` 
