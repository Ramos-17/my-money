from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from dependancies import get_current_user
from models import User, RecurringCharges
from schemas import RecurringChargeResponseSchema
from recurring_charges_service import run_detection_for_user
from notifications import run_detection_and_notify

router = APIRouter()

@router.get("", response_model=list[RecurringChargeResponseSchema])
def list_recurring_charges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(RecurringCharges)
        .filter(RecurringCharges.user_id == current_user.id)
        .order_by(RecurringCharges.next_expected_date)
        .all()
    )

@router.post("/scan", response_model=list[RecurringChargeResponseSchema])
def scan_recurring_charges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return run_detection_for_user(db, current_user.id)

@router.post("/scan-and-notify")
def scan_and_notify_recurring_charges(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    run_detection_and_notify(db, current_user)
    return {"message": "Scan complete, notifications sent for new or changed charges"}
