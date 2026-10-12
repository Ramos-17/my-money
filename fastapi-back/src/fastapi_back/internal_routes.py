import os
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from notifications import run_detection_and_notify

router = APIRouter()

def verify_cron_secret(x_cron_secret: str = Header(...)):
    expected = os.getenv("CRON_SECRET")
    if not expected or x_cron_secret != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid cron secret")

@router.post("/run-daily-scan", dependencies=[Depends(verify_cron_secret)])
def run_daily_scan(db: Session = Depends(get_db)):
    users = db.query(User).all()
    failed_user_ids = []
    for user in users:
        try:
            run_detection_and_notify(db, user)
        except Exception:
            db.rollback()
            failed_user_ids.append(str(user.id))

    return {
        "message": f"Scan complete for {len(users)} users",
        "failed_user_ids": failed_user_ids,
    }
