from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert as pg_insert
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.accounts_balance_get_request_options import AccountsBalanceGetRequestOptions
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from dependancies import get_current_user
from database import get_db
from models import User, PlaidItems, PlaidAccounts, Transactions
from schemas import PublicTokenSchema
from plaid_client import client

router = APIRouter()

def sync_plaid_accounts_for_item(db: Session, item: PlaidItems) -> tuple[dict[str, PlaidAccounts], list]:
    request = AccountsBalanceGetRequest(
        access_token=item.access_token,
        options=AccountsBalanceGetRequestOptions(
            min_last_updated_datetime=datetime.now(timezone.utc) - timedelta(days=7),
        ),
    )
    response = client.accounts_balance_get(request)

    accounts_by_plaid_id: dict[str, PlaidAccounts] = {}
    for account in response["accounts"]:
        values = {
            "plaid_item_id": item.id,
            "account_id": account["account_id"],
            "name": account["name"],
            "type": str(account["type"]),
            "subtype": str(account["subtype"]) if account["subtype"] else None,
        }
        stmt = pg_insert(PlaidAccounts.__table__).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=[PlaidAccounts.__table__.c.account_id],
            set_={"name": values["name"], "type": values["type"], "subtype": values["subtype"]},
        ).returning(PlaidAccounts.__table__.c.id)
        account_row_id = db.execute(stmt).scalar_one()
        db.commit()
        accounts_by_plaid_id[account["account_id"]] = db.get(PlaidAccounts, account_row_id)

    return accounts_by_plaid_id, response["accounts"]
@router.post("/create_link_token")
def create_link_token(current_user: User = Depends(get_current_user)):
    request = LinkTokenCreateRequest(
        user = LinkTokenCreateRequestUser(
            client_user_id = str(current_user.id)
        ),
        client_name = "MyMoney",
        products = [Products("transactions")],
        country_codes = [CountryCode("US")],
        language = "en",
    )
    response=client.link_token_create(request)
    link_token = response["link_token"]
    return {"link_token": link_token}

@router.post("/exchange_public_token")
def exchange_public_token(
    body: PublicTokenSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    request = ItemPublicTokenExchangeRequest(public_token=body.public_token)
    response = client.item_public_token_exchange(request)

    plaid_item = PlaidItems(
        item_id=response["item_id"],
        access_token=response["access_token"],
        user_id=current_user.id,
        institution_name=body.institution_name,
    )
    db.add(plaid_item)
    db.commit()
    db.refresh(plaid_item)

    return {"item_id": plaid_item.item_id}

@router.get("/transactions")
def get_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(PlaidItems).filter(PlaidItems.user_id == current_user.id).all()

    transactions = []
    for item in items:
        accounts_by_plaid_id, _ = sync_plaid_accounts_for_item(db, item)

        cursor = None
        has_more = True
        while has_more:
            request = (
                TransactionsSyncRequest(access_token=item.access_token, cursor=cursor)
                if cursor
                else TransactionsSyncRequest(access_token=item.access_token)
            )
            response = client.transactions_sync(request)
            for txn in response["added"]:
                account = accounts_by_plaid_id.get(txn["account_id"])
                if account is None:
                    continue

                values = {
                    "transaction_id": txn["transaction_id"],
                    "account_id": account.id,
                    "user_id": current_user.id,
                    "merchant_name": txn["merchant_name"],
                    "name": txn["name"],
                    "amount": txn["amount"],
                    "date": txn["date"],
                    "pending": txn["pending"],
                }
                stmt = pg_insert(Transactions.__table__).values(**values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[Transactions.__table__.c.transaction_id],
                    set_={
                        "merchant_name": values["merchant_name"],
                        "name": values["name"],
                        "amount": values["amount"],
                        "date": values["date"],
                        "pending": values["pending"],
                    },
                )
                db.execute(stmt)
                db.commit()

                transactions.append({
                    "transaction_id": txn["transaction_id"],
                    "account_id": txn["account_id"],
                    "institution_name": item.institution_name,
                    "name": txn["name"],
                    "merchant_name": txn["merchant_name"],
                    "amount": float(txn["amount"]),
                    "date": txn["date"].isoformat(),
                    "pending": txn["pending"],
                })
            has_more = response["has_more"]
            cursor = response["next_cursor"]

    return {"transactions": transactions}

@router.get("/accounts")
def get_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(PlaidItems).filter(PlaidItems.user_id == current_user.id).all()

    accounts = []
    for item in items:
        accounts_by_plaid_id, raw_accounts = sync_plaid_accounts_for_item(db, item)

        for account in raw_accounts:
            plaid_account = accounts_by_plaid_id[account["account_id"]]
            accounts.append({
                "id": plaid_account.id,
                "account_id": account["account_id"],
                "institution_name": item.institution_name,
                "name": account["name"],
                "type": str(account["type"]),
                "subtype": str(account["subtype"]) if account["subtype"] else None,
                "available_balance": account["balances"]["available"],
                "current_balance": account["balances"]["current"],
                "iso_currency_code": account["balances"]["iso_currency_code"],
            })

    return {"accounts": accounts}