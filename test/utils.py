from allsat_cnf.label_cnfizer import LabelCNFizer
from allsat_cnf.polarity_cnfizer import PolarityCNFizer


def get_data_from_examples(single_polarity_examples):
    return [(PolarityCNFizer(), e.formula, e.pol_expected_clauses, e.pol_expected_variables)
            for e in single_polarity_examples] + \
        [(PolarityCNFizer(label_neg_polarity=True), e.formula, e.pol_expected_clauses,
          e.pol_expected_variables) for e in single_polarity_examples] + \
        [(LabelCNFizer(), e.formula, e.lab_expected_clauses, e.lab_expected_variables)
         for e in single_polarity_examples] + \
        [(PolarityCNFizer(nnf=True), e.formula, e.nnf_pol_expected_clauses,
          e.nnf_pol_expected_variables) for e in single_polarity_examples] + \
        [(LabelCNFizer(nnf=True), e.formula, e.nnf_lab_expected_clauses,
          e.nnf_lab_expected_variables) for e in single_polarity_examples] + \
        [(PolarityCNFizer(nnf=True, mutex_nnf_labels=True), e.formula,
          e.nnf_mutex_pol_expected_clauses, e.nnf_mutex_pol_expected_variables) for e in
         single_polarity_examples]
