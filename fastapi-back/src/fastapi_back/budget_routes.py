import calendar
from datetime import date, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from dependancies import get_current_user
from models import User, PlaidItems, PlaidAccounts, IncomeSources, Bills
from schemas import (
    IncomeSourceCreateSchema,
    IncomeSourceUpdateSchema,
    IncomeSourceResponseSchema,
    BillCreateSchema,
    BillUpdateSchema,
    BillResponseSchema,
)

router = APIRouter()

def get_owned_account(db: Session, account_id: UUID, user_id: UUID) -> PlaidAccounts:
    account = (
        db.query(PlaidAccounts)
        .join(PlaidItems, PlaidAccounts.plaid_item_id == PlaidItems.id)
        .filter(PlaidAccounts.id == account_id, PlaidItems.user_id == user_id)
        .first()
    )
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found")
    return account

def get_owned_income_source(db: Session, income_id: UUID, user_id: UUID) -> IncomeSources:
    income_source = (
        db.query(IncomeSources)
        .filter(IncomeSources.id == income_id, IncomeSources.user_id == user_id)
        .first()
    )
    if income_source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found")
    return income_source

def get_owned_bill(db: Session, bill_id: UUID, user_id: UUID) -> Bills:
    bill = db.query(Bills).filter(Bills.id == bill_id, Bills.user_id == user_id).first()
    if bill is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found")
    return bill

@router.post("/income", response_model=IncomeSourceResponseSchema)
def create_income_source(
    body: IncomeSourceCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_account(db, body.deposit_account_id, current_user.id)

    income_source = IncomeSources(
        amount=body.amount,
        frequency=body.frequency,
        next_pay_date=body.next_pay_date,
        deposit_account_id=body.deposit_account_id,
        user_id=current_user.id,
    )
    db.add(income_source)
    db.commit()
    db.refresh(income_source)
    return income_source

@router.get("/income", response_model=list[IncomeSourceResponseSchema])
def list_income_sources(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(IncomeSources).filter(IncomeSources.user_id == current_user.id).all()

@router.put("/income/{income_id}", response_model=IncomeSourceResponseSchema)
def update_income_source(
    income_id: UUID,
    body: IncomeSourceUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    income_source = get_owned_income_source(db, income_id, current_user.id)

    updates = body.model_dump(exclude_unset=True)
    if "deposit_account_id" in updates:
        get_owned_account(db, updates["deposit_account_id"], current_user.id)
    for field, value in updates.items():
        setattr(income_source, field, value)

    db.commit()
    db.refresh(income_source)
    return income_source

@router.delete("/income/{income_id}")
def delete_income_source(
    income_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    income_source = get_owned_income_source(db, income_id, current_user.id)
    db.delete(income_source)
    db.commit()
    return {"message": "Income source deleted"}

@router.post("/bills", response_model=BillResponseSchema)
def create_bill(
    body: BillCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    get_owned_account(db, body.payment_account_id, current_user.id)

    bill = Bills(
        name=body.name,
        amount=body.amount,
        due_day_of_month=body.due_day_of_month,
        payment_account_id=body.payment_account_id,
        user_id=current_user.id,
    )
    db.add(bill)
    db.commit()
    db.refresh(bill)
    return bill

@router.get("/bills", response_model=list[BillResponseSchema])
def list_bills(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(Bills).filter(Bills.user_id == current_user.id).all()

@router.put("/bills/{bill_id}", response_model=BillResponseSchema)
def update_bill(
    bill_id: UUID,
    body: BillUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = get_owned_bill(db, bill_id, current_user.id)

    updates = body.model_dump(exclude_unset=True)
    if "payment_account_id" in updates:
        get_owned_account(db, updates["payment_account_id"], current_user.id)
    for field, value in updates.items():
        setattr(bill, field, value)

    db.commit()
    db.refresh(bill)
    return bill

@router.delete("/bills/{bill_id}")
def delete_bill(
    bill_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bill = get_owned_bill(db, bill_id, current_user.id)
    db.delete(bill)
    db.commit()
    return {"message": "Bill deleted"}

def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def next_occurrence(d: date, frequency: str) -> date:
    if frequency == "weekly":
        return d + timedelta(days=7)
    if frequency == "biweekly":
        return d + timedelta(days=14)
    if frequency == "monthly":
        return add_months(d, 1)
    raise ValueError(f"Unknown frequency: {frequency}")

def generate_pay_dates(next_pay_date: date, frequency: str, today: date, window_end: date) -> list[date]:
    current = next_pay_date
    while current < today:
        current = next_occurrence(current, frequency)

    dates = []
    while current <= window_end:
        dates.append(current)
        current = next_occurrence(current, frequency)
    dates.append(current)
    return dates

def generate_bill_due_dates(due_day_of_month: int, start: date, end: date) -> list[date]:
    dates = []
    year, month = start.year, start.month
    while True:
        day = min(due_day_of_month, calendar.monthrange(year, month)[1])
        occurrence = date(year, month, day)
        if occurrence > end:
            break
        if occurrence >= start:
            dates.append(occurrence)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return dates

@router.get("/calendar")
def get_budget_calendar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    today = date.today()
    window_end = today + timedelta(days=60)

    income_sources = db.query(IncomeSources).filter(IncomeSources.user_id == current_user.id).all()
    bills = db.query(Bills).filter(Bills.user_id == current_user.id).all()

    pay_date_income: dict[date, list[dict]] = {}
    for source in income_sources:
        for pay_date in generate_pay_dates(source.next_pay_date, source.frequency, today, window_end):
            pay_date_income.setdefault(pay_date, []).append({
                "income_source_id": str(source.id),
                "amount": float(source.amount),
            })

    sorted_pay_dates = sorted(pay_date_income.keys())
    if not sorted_pay_dates:
        return {"calendar": []}

    bill_due_dates = {
        bill.id: generate_bill_due_dates(bill.due_day_of_month, today, sorted_pay_dates[-1])
        for bill in bills
    }

    calendar_entries = []
    for i, pay_date in enumerate(sorted_pay_dates):
        if pay_date > window_end:
            break
        next_pay_date = sorted_pay_dates[i + 1] if i + 1 < len(sorted_pay_dates) else None

        period_bills = []
        if next_pay_date is not None:
            for bill in bills:
                for due_date in bill_due_dates[bill.id]:
                    if pay_date <= due_date < next_pay_date:
                        period_bills.append({
                            "bill_id": str(bill.id),
                            "name": bill.name,
                            "amount": float(bill.amount),
                            "due_date": due_date.isoformat(),
                        })

        calendar_entries.append({
            "pay_date": pay_date.isoformat(),
            "income": pay_date_income[pay_date],
            "total_income": sum(item["amount"] for item in pay_date_income[pay_date]),
            "bills": period_bills,
        })

    return {"calendar": calendar_entries}
