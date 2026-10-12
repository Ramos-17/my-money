from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from typing import Literal

class SignupSchema(BaseModel):
    email: EmailStr
    password: str
    first: str
    last: str
    username: str
    
class LoginSchema(BaseModel):
    username: str
    password: str

class UserResponseSchema(BaseModel):
    id: UUID
    email: EmailStr
    first: str
    last: str
    username: str
    created: datetime

    class Config:
        orm_mode = True

class PublicTokenSchema(BaseModel):
    public_token: str
    institution_name: str | None = None

class PlaidAccountResponseSchema(BaseModel):
    id: UUID
    name: str
    type: str
    subtype: str | None

    class Config:
        orm_mode = True

Frequency = Literal["weekly", "biweekly", "monthly"]

class IncomeSourceCreateSchema(BaseModel):
    amount: Decimal
    frequency: Frequency
    next_pay_date: date
    deposit_account_id: UUID

class IncomeSourceUpdateSchema(BaseModel):
    amount: Decimal | None = None
    frequency: Frequency | None = None
    next_pay_date: date | None = None
    deposit_account_id: UUID | None = None

class IncomeSourceResponseSchema(BaseModel):
    id: UUID
    amount: float
    frequency: str
    next_pay_date: date
    deposit_account_id: UUID
    created: datetime

    class Config:
        orm_mode = True

class BillCreateSchema(BaseModel):
    name: str
    amount: Decimal
    due_day_of_month: int = Field(ge=1, le=31)
    payment_account_id: UUID

class BillUpdateSchema(BaseModel):
    name: str | None = None
    amount: Decimal | None = None
    due_day_of_month: int | None = Field(default=None, ge=1, le=31)
    payment_account_id: UUID | None = None

class BillResponseSchema(BaseModel):
    id: UUID
    name: str
    amount: float
    due_day_of_month: int
    payment_account_id: UUID
    created: datetime

    class Config:
        orm_mode = True

class PaycheckAllocationCreateSchema(BaseModel):
    name: str
    amount: Decimal

class PaycheckDepositCreateSchema(BaseModel):
    account_id: UUID
    amount: Decimal
    allocations: list[PaycheckAllocationCreateSchema] = []

class PaycheckCreateSchema(BaseModel):
    pay_date: date
    deposits: list[PaycheckDepositCreateSchema] = []

class PaycheckAllocationResponseSchema(BaseModel):
    id: UUID
    name: str
    amount: float

class PaycheckDepositResponseSchema(BaseModel):
    id: UUID
    account_id: UUID
    account_name: str
    institution_name: str | None
    amount: float
    allocations: list[PaycheckAllocationResponseSchema]
    leftover: float

class PaycheckResponseSchema(BaseModel):
    id: UUID
    pay_date: date
    deposits: list[PaycheckDepositResponseSchema]
    total_leftover: float
    created: datetime

class RecurringChargeResponseSchema(BaseModel):
    id: UUID
    merchant_name: str
    amount: float
    interval_days: int
    last_seen_date: date
    next_expected_date: date
    amount_changed: bool
    previous_amount: float | None
    created: datetime

    class Config:
        orm_mode = True