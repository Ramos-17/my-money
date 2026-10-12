import re
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from uuid import UUID
from sqlalchemy.orm import Session
from models import Transactions, RecurringCharges, RecurringChargeTransactions

AMOUNT_TOLERANCE = Decimal("0.05")
MIN_INTERVAL_DAYS = 25
MAX_INTERVAL_DAYS = 35
MIN_OCCURRENCES = 3

NOISE_PATTERNS = [
    r"\bSQ \*",
    r"\bTST\*",
    r"\bPAYPAL \*",
    r"\bPOS DEBIT\b",
    r"#\d+",
    r"\*\d+",
    r"\d{4,}",
]

def normalize_merchant_name(txn: Transactions) -> str:
    raw = txn.merchant_name or txn.name
    normalized = raw.upper().strip()
    for pattern in NOISE_PATTERNS:
        normalized = re.sub(pattern, "", normalized)
    normalized = re.sub(r"[.*#]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized

def amounts_within_tolerance(a: Decimal, b: Decimal) -> bool:
    if a == 0:
        return b == 0
    return abs(a - b) / abs(a) <= AMOUNT_TOLERANCE

def group_by_merchant(transactions: list[Transactions]) -> dict[str, list[Transactions]]:
    groups: dict[str, list[Transactions]] = defaultdict(list)
    for txn in transactions:
        groups[normalize_merchant_name(txn)].append(txn)
    return groups

def group_by_amount(transactions: list[Transactions]) -> list[list[Transactions]]:
    amount_groups: list[list[Transactions]] = []
    for txn in sorted(transactions, key=lambda t: t.date):
        for group in amount_groups:
            if amounts_within_tolerance(group[-1].amount, txn.amount):
                group.append(txn)
                break
        else:
            amount_groups.append([txn])
    return amount_groups

def find_consistent_interval(sorted_txns: list[Transactions]) -> int | None:
    if len(sorted_txns) < MIN_OCCURRENCES:
        return None

    gaps = [
        (sorted_txns[i + 1].date - sorted_txns[i].date).days
        for i in range(len(sorted_txns) - 1)
    ]
    consistent_gaps = [g for g in gaps if MIN_INTERVAL_DAYS <= g <= MAX_INTERVAL_DAYS]
    if len(consistent_gaps) < MIN_OCCURRENCES - 1:
        return None

    return round(sum(consistent_gaps) / len(consistent_gaps))

def run_detection_for_user(db: Session, user_id: UUID) -> list[RecurringCharges]:
    transactions = (
        db.query(Transactions)
        .filter(Transactions.user_id == user_id, Transactions.pending.is_(False))
        .order_by(Transactions.date)
        .all()
    )

    results = []
    for merchant_name, merchant_txns in group_by_merchant(transactions).items():
        for group in group_by_amount(merchant_txns):
            interval_days = find_consistent_interval(group)
            if interval_days is None:
                continue

            latest = group[-1]
            last_seen_date = latest.date
            next_expected_date = last_seen_date + timedelta(days=interval_days)

            existing = (
                db.query(RecurringCharges)
                .filter(
                    RecurringCharges.user_id == user_id,
                    RecurringCharges.merchant_name == merchant_name,
                )
                .first()
            )

            if existing is None:
                existing = RecurringCharges(
                    user_id=user_id,
                    merchant_name=merchant_name,
                    amount=latest.amount,
                    interval_days=interval_days,
                    last_seen_date=last_seen_date,
                    next_expected_date=next_expected_date,
                    amount_changed=False,
                    previous_amount=None,
                )
                db.add(existing)
            else:
                amount_changed = existing.amount != latest.amount
                existing.amount_changed = amount_changed
                existing.previous_amount = existing.amount if amount_changed else existing.previous_amount
                existing.amount = latest.amount
                existing.interval_days = interval_days
                existing.last_seen_date = last_seen_date
                existing.next_expected_date = next_expected_date

            db.commit()
            db.refresh(existing)

            linked_ids = {
                row.transaction_id
                for row in db.query(RecurringChargeTransactions.transaction_id)
                .filter(RecurringChargeTransactions.recurring_charge_id == existing.id)
                .all()
            }
            for txn in group:
                if txn.id not in linked_ids:
                    db.add(RecurringChargeTransactions(recurring_charge_id=existing.id, transaction_id=txn.id))
            db.commit()

            results.append(existing)

    return results
