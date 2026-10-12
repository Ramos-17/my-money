from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_back.auth import router as auth_router
from fastapi_back.plaid_routes import router as plaid_router
from fastapi_back.budget_routes import router as budget_router
from fastapi_back.recurring_charges_routes import router as recurring_charges_router
from fastapi_back.paycheck_routes import router as paycheck_router
from fastapi_back.internal_routes import router as internal_router

app = FastAPI(title="MyMoney API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(plaid_router, prefix="/plaid", tags=["plaid"])
app.include_router(budget_router, prefix="/budget", tags=["budget"])
app.include_router(recurring_charges_router, prefix="/recurring-charges", tags=["recurring-charges"])
app.include_router(paycheck_router, prefix="/paychecks", tags=["paychecks"])
app.include_router(internal_router, prefix="/internal", tags=["internal"])
