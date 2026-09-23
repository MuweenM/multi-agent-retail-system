"""Comprehensive test suite for PII redaction (Prompt 1.2 requirement: 40+ cases)."""

from shared.retail_common.security.pii import redact_pii, luhn_check


def test_luhn_algorithm():
    # Valid Visa card sample
    assert luhn_check("4532015112830366") is True
    # Invalid card
    assert luhn_check("4532015112830367") is False
    # Short number
    assert luhn_check("123456") is False


def test_pii_benchmark_and_accuracy():
    # Test cases: (input_text, expected_types_found, preserved_tokens, forbidden_tokens)
    test_cases = [
        # --- Phone Numbers (Sri Lanka 07x, +94 7x, landlines) ---
        ("Call me on 0771234567 regarding phone defect", ["PHONE"], ["phone defect"], ["0771234567"]),
        ("My number is 071-9876543, please call back", ["PHONE"], ["please call back"], ["071-9876543"]),
        ("Contact +94 76 543 2109 for refund", ["PHONE"], ["refund"], ["+94 76 543 2109"]),
        ("Tel: +94771234567 item broken", ["PHONE"], ["item broken"], ["+94771234567"]),
        ("Home number 0112345678 not working", ["PHONE"], ["not working"], ["0112345678"]),
        ("Call 081-2233445 about power bank", ["PHONE"], ["power bank"], ["081-2233445"]),
        ("Whatsapp on 0751122334 thanks", ["PHONE"], ["thanks"], ["0751122334"]),
        ("Mobile 0709988776 is dead", ["PHONE"], ["is dead"], ["0709988776"]),
        ("Phone: 0723344556 please help", ["PHONE"], ["please help"], ["0723344556"]),
        ("Dial +94 11 2345678 today", ["PHONE"], ["today"], ["+94 11 2345678"]),

        # --- Email Addresses ---
        ("Send receipt to kasun.perera@gmail.com please", ["EMAIL"], ["Send receipt"], ["kasun.perera@gmail.com"]),
        ("My email is nimal_fernando@yahoo.com", ["EMAIL"], ["My email"], ["nimal_fernando@yahoo.com"]),
        ("Contact support_lanka@techstore.lk for RMA", ["EMAIL"], ["for RMA"], ["support_lanka@techstore.lk"]),
        ("Email: dilshan.99@hotmail.com with invoice", ["EMAIL"], ["with invoice"], ["dilshan.99@hotmail.com"]),
        ("Write to customer.service@domain.org", ["EMAIL"], ["Write to"], ["customer.service@domain.org"]),
        ("Complaints to info@ceylonharvest.com urgently", ["EMAIL"], ["urgently"], ["info@ceylonharvest.com"]),

        # --- Sri Lankan NICs (Old 9+V/X and New 12-digit) ---
        ("My NIC is 912345678V for identification", ["NIC"], ["for identification"], ["912345678V"]),
        ("National identity 854321987X submitted", ["NIC"], ["submitted"], ["854321987X"]),
        ("New NIC number 199512345678 attached", ["NIC"], ["attached"], ["199512345678"]),
        ("ID card 200198765432 verified", ["NIC"], ["verified"], ["200198765432"]),
        ("NIC 987654321v check order", ["NIC"], ["check order"], ["987654321v"]),
        ("NIC 200311223344 for warranty", ["NIC"], ["for warranty"], ["200311223344"]),

        # --- Payment Cards (Luhn Validated) ---
        ("Refund to card 4532015112830366 immediately", ["CARD"], ["Refund to card"], ["4532015112830366"]),
        ("Paid using card 4532-0151-1283-0366 on web", ["CARD"], ["on web"], ["4532-0151-1283-0366"]),
        ("Card ending with 4532 0151 1283 0366 charged twice", ["CARD"], ["charged twice"], ["4532 0151 1283 0366"]),

        # --- Addresses ---
        ("Deliver to No. 45, Galle Road, Colombo 03", ["ADDRESS"], ["Deliver to"], ["Galle Road"]),
        ("Address: 12/A Temple Road, Kandy", ["ADDRESS"], [], ["Temple Road, Kandy"]),
        ("Sent to Flower Road, Colombo 07", ["ADDRESS"], ["Sent to"], ["Flower Road"]),
        ("My shop is at Main Street, Negombo", ["ADDRESS"], ["My shop is at"], ["Main Street, Negombo"]),
        ("Pickup from Kandy Road, Kurunegala", ["ADDRESS"], ["Pickup from"], ["Kandy Road"]),
        ("Deliver to: High Level Road, Nugegoda", ["ADDRESS"], ["Deliver to:"], ["High Level Road"]),

        # --- Names with Intro prefixes ---
        ("My name is Kasun Perera, product broken", ["PERSON"], ["product broken"], ["Kasun Perera"]),
        ("I am Nimal Silva, need replacement", ["PERSON"], ["need replacement"], ["Nimal Silva"]),
        ("Customer: Dilshan Jayasinghe reporting defect", ["PERSON"], ["reporting defect"], ["Dilshan Jayasinghe"]),

        # --- FALSE POSITIVE TRAPS (Must NOT be redacted as PII) ---
        ("Order ORD-10293 for Galaxy A15 5G smartphone", [], ["ORD-10293", "Galaxy A15 5G"], ["[PHONE]", "[NIC]", "[CARD]"]),
        ("Product SKU-99021 price LKR 12,500 only", [], ["SKU-99021", "12,500"], ["[PHONE]", "[CARD]"]),
        ("Item P-014 20000mAh Power Bank bought for Rs. 9200", [], ["P-014", "20000mAh", "Rs. 9200"], ["[PHONE]", "[NIC]"]),
        ("Order ORD-9921 arrived 3 days late on 2026-09-15", [], ["ORD-9921", "2026-09-15"], ["[PHONE]", "[CARD]"]),
        ("Model Redmi 13C memory 128GB storage", [], ["Redmi 13C", "128GB"], ["[NIC]", "[CARD]"]),
        ("Returned size XL slim fit shirt P-027", [], ["size XL", "P-027"], ["[PHONE]", "[NIC]"]),
        ("Bought 3 items at Rs. 4500 each total 13500", [], ["Rs. 4500", "13500"], ["[CARD]", "[PHONE]"]),
    ]

    metrics = {
        "PHONE": {"tp": 0, "fn": 0, "fp": 0},
        "EMAIL": {"tp": 0, "fn": 0, "fp": 0},
        "NIC": {"tp": 0, "fn": 0, "fp": 0},
        "CARD": {"tp": 0, "fn": 0, "fp": 0},
        "ADDRESS": {"tp": 0, "fn": 0, "fp": 0},
        "PERSON": {"tp": 0, "fn": 0, "fp": 0},
    }

    assert len(test_cases) >= 40, f"Must have at least 40 test cases, found {len(test_cases)}"

    for text, expected_types, preserved, forbidden in test_cases:
        res = redact_pii(text)
        
        # Check preserved tokens
        for p in preserved:
            assert p.lower() in res.text.lower(), f"Preserved token '{p}' was mistakenly altered in: '{res.text}' (original: '{text}')"
        
        # Check forbidden tokens
        for f in forbidden:
            assert f not in res.text, f"Sensitive token '{f}' leaked into clean_text: '{res.text}'"

        # Calculate metrics
        for pii_type in metrics.keys():
            if pii_type in expected_types:
                if pii_type in res.types_found:
                    metrics[pii_type]["tp"] += 1
                else:
                    metrics[pii_type]["fn"] += 1
            else:
                if pii_type in res.types_found:
                    metrics[pii_type]["fp"] += 1

    print("\n--- PII Redaction Precision & Recall Table ---")
    print(f"{'PII Type':<12} | {'Precision':<10} | {'Recall':<10} | {'TP':<4} | {'FP':<4} | {'FN':<4}")
    print("-" * 55)
    for pii_type, counts in metrics.items():
        tp = counts["tp"]
        fp = counts["fp"]
        fn = counts["fn"]
        prec = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 1.0
        print(f"{pii_type:<12} | {prec:<10.2f} | {rec:<10.2f} | {tp:<4} | {fp:<4} | {fn:<4}")
        # Blueprint requirement: Recall >= 0.98 on phone, email, nic, card
        if pii_type in ("PHONE", "EMAIL", "NIC", "CARD") and (tp + fn) > 0:
            assert rec >= 0.98, f"PII Recall for {pii_type} must be >= 0.98, got {rec:.2f}"
