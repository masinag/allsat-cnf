from itertools import product

import pytest
from pysmt.shortcuts import is_sat, get_atoms

from allsat_cnf.distributive_cnfizer import DistributiveCNF
from allsat_cnf.label_cnfizer import LabelCNFizer
from allsat_cnf.polarity_cnfizer import PolarityCNFizer
from allsat_cnf.utils import check_models, get_allsat, SolverOptions, is_cnf, get_clauses
from instances import bool_identity_examples, bool_single_polarity_examples, bool_double_polarity_examples, \
    lra_identity_examples, lra_single_polarity_examples, lra_double_polarity_examples, bool_ite_examples, \
    lra_ite_examples
from utils import get_data_from_examples


@pytest.mark.parametrize("cnfizer, phi",
                         product([DistributiveCNF(), PolarityCNFizer(), LabelCNFizer()], bool_identity_examples))
def test_bool_identity(cnfizer, phi):
    cnf = cnfizer.convert_as_formula(phi)
    assert cnf == phi


@pytest.mark.parametrize("cnfizer, phi, n, n_vars", get_data_from_examples(bool_single_polarity_examples))
def test_bool_number_of_clauses_single_polarity(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert is_cnf(cnf)
    assert len(get_clauses(cnf)) == n
    assert len(get_atoms(cnf)) == n_vars
    assert is_sat(phi) == is_sat(cnf)
    ta, _ = get_allsat(cnf, atoms=get_atoms(phi), solver_options=SolverOptions(use_ta=True))
    check_models(ta, phi)


@pytest.mark.parametrize("cnfizer, phi, n, n_vars", get_data_from_examples(bool_double_polarity_examples))
def test_bool_number_of_clauses_double_polarity(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert is_cnf(cnf)
    assert len(get_clauses(cnf)) == n
    assert len(get_atoms(cnf)) == n_vars
    assert is_sat(phi) == is_sat(cnf)
    ta, _ = get_allsat(cnf, atoms=get_atoms(phi), solver_options=SolverOptions(use_ta=True))
    check_models(ta, phi)


@pytest.mark.parametrize("cnfizer, phi", product([PolarityCNFizer(), LabelCNFizer()], lra_identity_examples))
def test_lra_identity(cnfizer, phi):
    cnf = cnfizer.convert_as_formula(phi)
    assert cnf == phi


@pytest.mark.parametrize("cnfizer, phi, n, n_vars", get_data_from_examples(lra_single_polarity_examples))
def test_lra_number_of_clauses_single_polarity(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert is_cnf(cnf)
    assert len(get_clauses(cnf)) == n
    assert len(get_atoms(cnf)) == n_vars
    assert is_sat(phi) == is_sat(cnf)
    ta, _ = get_allsat(cnf, atoms=get_atoms(phi), solver_options=SolverOptions(use_ta=True))
    check_models(ta, phi)


@pytest.mark.parametrize("cnfizer, phi, n, n_vars", get_data_from_examples(lra_double_polarity_examples))
def test_lra_number_of_clauses_double_polarity(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert is_cnf(cnf)
    assert len(get_clauses(cnf)) == n
    assert len(get_atoms(cnf)) == n_vars
    assert is_sat(phi) == is_sat(cnf)
    ta, _ = get_allsat(cnf, atoms=get_atoms(phi), solver_options=SolverOptions(use_ta=True))
    check_models(ta, phi)


@pytest.mark.parametrize("cnfizer, phi, n, n_vars", get_data_from_examples(bool_ite_examples))
def test_bool_ite_number_of_clauses(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert is_cnf(cnf)
    assert len(get_clauses(cnf)) == n
    assert len(get_atoms(cnf)) == n_vars
    assert is_sat(phi) == is_sat(cnf)
    ta, _ = get_allsat(cnf, atoms=get_atoms(phi), solver_options=SolverOptions(use_ta=True))
    check_models(ta, phi)


@pytest.mark.parametrize("cnfizer, phi, n, n_vars", get_data_from_examples(lra_ite_examples))
def test_lra_ite_number_of_clauses(cnfizer, phi, n, n_vars):
    cnf = cnfizer.convert_as_formula(phi)
    assert is_cnf(cnf)
    assert len(get_clauses(cnf)) == n
    assert len(get_atoms(cnf)) == n_vars
    assert is_sat(phi) == is_sat(cnf)
    ta, _ = get_allsat(cnf, atoms=get_atoms(phi), solver_options=SolverOptions(use_ta=True))
    check_models(ta, phi)
