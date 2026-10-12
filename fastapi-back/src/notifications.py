from sqlalchemy.orm import Session
from models import User, RecurringCharges
from recurring_charges_service import run_detection_for_user
from email_service import send_email, build_new_charge_email, build_price_change_email

def run_detection_and_notify(db: Session, user: User) -> None:
    existing_ids_before = {
        row.id
        for row in db.query(RecurringCharges.id).filter(RecurringCharges.user_id == user.id).all()
    }

    results = run_detection_for_user(db, user.id)

    for charge in results:
        if charge.id not in existing_ids_before:
            subject, text_body, html_body = build_new_charge_email(charge)
            send_email(user.email, subject, text_body, html_body)
        elif charge.amount_changed:
            subject, text_body, html_body = build_price_change_email(charge)
            send_email(user.email, subject, text_body, html_body)
