"""
Shared taxonomy tuples for the retail return intelligence system.
Values represent the standard vocabulary across all agents and contracts.
"""

ROOT_CAUSES = (
    "manufacturing_defect", "damaged_in_transit", "wrong_item_shipped",
    "size_fit_issue", "not_as_described", "quality_durability",
    "late_delivery", "change_of_mind", "policy_abuse_suspected", "unknown",
)
INTENTS = ("return", "exchange", "refund", "complaint", "unknown")
SENTIMENTS = ("positive", "neutral", "negative")
DECISIONS = ("approve", "reject", "escalate", "request_info")
SOURCE_TYPES = ("review", "supplier_record", "historical_return", "inventory", "policy")
