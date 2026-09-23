"""Test suite for bulk CSV loading, validation, and formula injection guard."""

from shared.retail_common.bulk_io import load_and_validate_csv, sanitize_csv_cell, pseudonymize_customer


def test_csv_formula_injection_guard():
    assert sanitize_csv_cell("=SUM(A1:A10)") == "'=SUM(A1:A10)"
    assert sanitize_csv_cell("+12345") == "'+12345"
    assert sanitize_csv_cell("-CMD") == "'-CMD"
    assert sanitize_csv_cell("@SUM") == "'@SUM"
    assert sanitize_csv_cell("Normal text") == "Normal text"


def test_customer_pseudonymization():
    cust1 = pseudonymize_customer("user_kasun_123")
    cust2 = pseudonymize_customer("user_kasun_123")
    cust3 = pseudonymize_customer("user_nimal_456")
    assert cust1 == cust2
    assert cust1 != cust3
    assert cust1.startswith("CUST-")
    assert pseudonymize_customer(None) is None


def test_csv_bulk_loading_valid():
    csv_data = """return_id,text,order_id,product_id,customer_ref,order_value_lkr
RET-001,Power bank battery swelling after 2 weeks,ORD-501,P-014,user_1,9200
RET-002,Shirt size is too small,ORD-502,P-027,user_2,4800
"""
    rows, errors = load_and_validate_csv(csv_data)
    assert len(errors) == 0
    assert len(rows) == 2
    assert rows[0].product_id == "P-014"
    assert rows[0].order_value_lkr == 9200.0
    assert rows[0].customer_ref.startswith("CUST-")


def test_csv_alias_and_error_handling():
    csv_data = """complaint,order_number,amount
Power bank broken,ORD-999,5500
,ORD-1000,2000
Valid complaint with bad price,ORD-1001,NotANumber
"""
    rows, errors = load_and_validate_csv(csv_data)
    assert len(rows) == 2
    assert any(e.field == "text" and e.row == 2 for e in errors)
    assert any(e.field == "order_value_lkr" and e.row == 3 for e in errors)
