"""
Replaced by test_demo_scenario_china_bd_e2e.py.
Signature competition demo now evaluates the China-Bangladesh (CNY / BDT) scenario.
"""
from tests.test_demo_scenario_china_bd_e2e import (
    test_signature_china_bd_demo_full_workflow_e2e,
    test_reverse_transfer_bdt_to_cny,
    test_mathematical_consistency_china_bd_dataset,
    test_default_currencies_and_absence_of_gbp_inr,
)

__all__ = [
    "test_signature_china_bd_demo_full_workflow_e2e",
    "test_reverse_transfer_bdt_to_cny",
    "test_mathematical_consistency_china_bd_dataset",
    "test_default_currencies_and_absence_of_gbp_inr",
]
