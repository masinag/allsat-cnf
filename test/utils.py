from allsat_cnf.demorgan_cnfizer import DistributiveCNF
from allsat_cnf.label_cnfizer import LabelCNFizer
from allsat_cnf.polarity_cnfizer import PolarityCNFizer


def get_data_from_examples(examples):
    return [(DistributiveCNF(), e.formula, e.dm_expected_clauses, e.dm_expected_variables)
            for e in examples] + \
        [(PolarityCNFizer(), e.formula, e.pol_expected_clauses, e.pol_expected_variables)
         for e in examples] + \
        [(PolarityCNFizer(label_neg_polarity=True), e.formula, e.pol_expected_clauses,
          e.pol_expected_variables) for e in examples] + \
        [(LabelCNFizer(), e.formula, e.lab_expected_clauses, e.lab_expected_variables)
         for e in examples] + \
        [(PolarityCNFizer(nnf=True), e.formula, e.nnf_pol_expected_clauses,
          e.nnf_pol_expected_variables) for e in examples] + \
        [(LabelCNFizer(nnf=True), e.formula, e.nnf_lab_expected_clauses,
          e.nnf_lab_expected_variables) for e in examples] + \
        [(PolarityCNFizer(nnf=True, mutex_nnf_labels=True), e.formula,
          e.nnf_mutex_pol_expected_clauses, e.nnf_mutex_pol_expected_variables) for e in
         examples]
