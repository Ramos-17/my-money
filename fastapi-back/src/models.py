from database import Base
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, Date, Numeric, ForeignKey, Boolean, text
from sqlalchemy.dialects.postgresql import UUID
import uuid
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    first = Column(String(255), nullable=False)    
    last = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    username = Column(String(255), nullable=False, unique=True)
    
class PlaidItems(Base):
    __tablename__ = "plaid_items"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    item_id = Column(String(255), nullable = False, unique = True)
    access_token = Column(Text, nullable = False, unique = True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    institution_name = Column(String(255), nullable=True)

class PlaidAccounts(Base):
    __tablename__ = "plaid_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    plaid_item_id = Column(UUID(as_uuid=True), ForeignKey("plaid_items.id"), nullable=False)
    account_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    type = Column(String(255), nullable=False)
    subtype = Column(String(255), nullable=True)

class IncomeSources(Base):
    __tablename__ = "income_sources"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    amount = Column(Numeric(10, 2), nullable=False)
    frequency = Column(String(20), nullable=False)
    next_pay_date = Column(Date, nullable=False)
    deposit_account_id = Column(UUID(as_uuid=True), ForeignKey("plaid_accounts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

class Bills(Base):
    __tablename__ = "bills"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    due_day_of_month = Column(Integer, nullable=False)
    payment_account_id = Column(UUID(as_uuid=True), ForeignKey("plaid_accounts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

class Transactions(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    transaction_id = Column(String(255), nullable=False, unique=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("plaid_accounts.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    merchant_name = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    date = Column(Date, nullable=False)
    pending = Column(Boolean, nullable=False, server_default=text("false"))

class RecurringCharges(Base):
    __tablename__ = "recurring_charges"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    merchant_name = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    interval_days = Column(Integer, nullable=False)
    last_seen_date = Column(Date, nullable=False)
    next_expected_date = Column(Date, nullable=False)
    amount_changed = Column(Boolean, nullable=False, server_default=text("false"))
    previous_amount = Column(Numeric(10, 2), nullable=True)

class RecurringChargeTransactions(Base):
    __tablename__ = "recurring_charge_transactions"
    recurring_charge_id = Column(UUID(as_uuid=True), ForeignKey("recurring_charges.id"), primary_key=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id"), primary_key=True)

class Paychecks(Base):
    __tablename__ = "paychecks"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    pay_date = Column(Date, nullable=False)

class PaycheckDeposits(Base):
    __tablename__ = "paycheck_deposits"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    paycheck_id = Column(UUID(as_uuid=True), ForeignKey("paychecks.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("plaid_accounts.id"), nullable=True)
    account_name = Column(String(255), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)

class PaycheckAllocations(Base):
    __tablename__ = "paycheck_allocations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    created = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    paycheck_deposit_id = Column(UUID(as_uuid=True), ForeignKey("paycheck_deposits.id"), nullable=False)
    name = Column(String(255), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)