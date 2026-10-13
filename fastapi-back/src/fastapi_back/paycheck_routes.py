from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from database import get_db
from dependancies import get_current_user
from models import User, PlaidItems, PlaidAccounts, Paychecks, PaycheckDeposits, PaycheckAllocations
from schemas import PaycheckCreateSchema, PaycheckDepositCreateSchema, PaycheckResponseSchema

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

def validate_deposit(db: Session, deposit: PaycheckDepositCreateSchema, user_id: UUID) -> None:
    if deposit.account_id is not None:
        get_owned_account(db, deposit.account_id, user_id)
    elif not deposit.account_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Each deposit needs either account_id or account_name",
        )

def get_owned_paycheck(db: Session, paycheck_id: UUID, user_id: UUID) -> Paychecks:
    paycheck = (
        db.query(Paychecks)
        .filter(Paychecks.id == paycheck_id, Paychecks.user_id == user_id)
        .first()
    )
    if paycheck is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paycheck not found")
    return paycheck

def serialize_paycheck(db: Session, paycheck: Paychecks) -> dict:
    deposits = db.query(PaycheckDeposits).filter(PaycheckDeposits.paycheck_id == paycheck.id).all()

    deposit_data = []
    total_leftover = 0.0
    for deposit in deposits:
        account = None
        item = None
        if deposit.account_id is not None:
            account = db.query(PlaidAccounts).filter(PlaidAccounts.id == deposit.account_id).first()
            if account is not None:
                item = db.query(PlaidItems).filter(PlaidItems.id == account.plaid_item_id).first()
        allocations = (
            db.query(PaycheckAllocations)
            .filter(PaycheckAllocations.paycheck_deposit_id == deposit.id)
            .all()
        )
        allocated_total = sum(float(a.amount) for a in allocations)
        leftover = float(deposit.amount) - allocated_total
        total_leftover += leftover

        deposit_data.append({
            "id": deposit.id,
            "account_id": deposit.account_id,
            "account_name": account.name if account else (deposit.account_name or "Unnamed account"),
            "institution_name": item.institution_name if item else None,
            "amount": float(deposit.amount),
            "allocations": [
                {"id": a.id, "name": a.name, "amount": float(a.amount)}
                for a in allocations
            ],
            "leftover": leftover,
        })

    return {
        "id": paycheck.id,
        "pay_date": paycheck.pay_date,
        "deposits": deposit_data,
        "total_leftover": total_leftover,
        "created": paycheck.created,
        "editable": paycheck.pay_date >= date.today(),
    }

@router.post("", response_model=PaycheckResponseSchema, status_code=status.HTTP_201_CREATED)
def create_paycheck(
    body: PaycheckCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    for deposit in body.deposits:
        validate_deposit(db, deposit, current_user.id)

    paycheck = Paychecks(user_id=current_user.id, pay_date=body.pay_date)
    db.add(paycheck)
    db.commit()
    db.refresh(paycheck)

    for deposit_data in body.deposits:
        deposit = PaycheckDeposits(
            paycheck_id=paycheck.id,
            account_id=deposit_data.account_id,
            account_name=deposit_data.account_name,
            amount=deposit_data.amount,
        )
        db.add(deposit)
        db.commit()
        db.refresh(deposit)

        for allocation_data in deposit_data.allocations:
            db.add(PaycheckAllocations(
                paycheck_deposit_id=deposit.id,
                name=allocation_data.name,
                amount=allocation_data.amount,
            ))
        db.commit()

    return serialize_paycheck(db, paycheck)

@router.get("", response_model=list[PaycheckResponseSchema])
def list_paychecks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paychecks = (
        db.query(Paychecks)
        .filter(Paychecks.user_id == current_user.id)
        .order_by(Paychecks.pay_date.desc())
        .all()
    )
    return [serialize_paycheck(db, paycheck) for paycheck in paychecks]

@router.put("/{paycheck_id}", response_model=PaycheckResponseSchema)
def update_paycheck(
    paycheck_id: UUID,
    body: PaycheckCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paycheck = get_owned_paycheck(db, paycheck_id, current_user.id)

    if paycheck.pay_date < date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot edit a paycheck whose pay date has already passed",
        )

    for deposit in body.deposits:
        validate_deposit(db, deposit, current_user.id)

    old_deposits = db.query(PaycheckDeposits).filter(PaycheckDeposits.paycheck_id == paycheck.id).all()
    for deposit in old_deposits:
        db.query(PaycheckAllocations).filter(PaycheckAllocations.paycheck_deposit_id == deposit.id).delete()
    db.query(PaycheckDeposits).filter(PaycheckDeposits.paycheck_id == paycheck.id).delete()
    db.commit()

    paycheck.pay_date = body.pay_date
    db.commit()

    for deposit_data in body.deposits:
        deposit = PaycheckDeposits(
            paycheck_id=paycheck.id,
            account_id=deposit_data.account_id,
            account_name=deposit_data.account_name,
            amount=deposit_data.amount,
        )
        db.add(deposit)
        db.commit()
        db.refresh(deposit)

        for allocation_data in deposit_data.allocations:
            db.add(PaycheckAllocations(
                paycheck_deposit_id=deposit.id,
                name=allocation_data.name,
                amount=allocation_data.amount,
            ))
        db.commit()

    return serialize_paycheck(db, paycheck)

@router.delete("/{paycheck_id}")
def delete_paycheck(
    paycheck_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    paycheck = get_owned_paycheck(db, paycheck_id, current_user.id)

    deposits = db.query(PaycheckDeposits).filter(PaycheckDeposits.paycheck_id == paycheck.id).all()
    for deposit in deposits:
        db.query(PaycheckAllocations).filter(PaycheckAllocations.paycheck_deposit_id == deposit.id).delete()
    db.query(PaycheckDeposits).filter(PaycheckDeposits.paycheck_id == paycheck.id).delete()
    db.delete(paycheck)
    db.commit()

    return {"message": "Paycheck deleted"}
