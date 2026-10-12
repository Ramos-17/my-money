CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    first VARCHAR(255) NOT NULL,
    last VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    username VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE plaid_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    item_id VARCHAR(255) NOT NULL UNIQUE,
    access_token TEXT NOT NULL UNIQUE,
    user_id UUID NOT NULL REFERENCES users(id),
    institution_name VARCHAR(255)
);

CREATE TABLE plaid_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    plaid_item_id UUID NOT NULL REFERENCES plaid_items(id),
    account_id VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(255) NOT NULL,
    subtype VARCHAR(255)
);

CREATE TABLE income_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    amount NUMERIC(10,2) NOT NULL,
    frequency VARCHAR(20) NOT NULL,
    next_pay_date DATE NOT NULL,
    deposit_account_id UUID NOT NULL REFERENCES plaid_accounts(id),
    user_id UUID NOT NULL REFERENCES users(id)
);

CREATE TABLE bills (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    name VARCHAR(255) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    due_day_of_month INTEGER NOT NULL,
    payment_account_id UUID NOT NULL REFERENCES plaid_accounts(id),
    user_id UUID NOT NULL REFERENCES users(id)
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    transaction_id VARCHAR(255) NOT NULL UNIQUE,
    account_id UUID NOT NULL REFERENCES plaid_accounts(id),
    user_id UUID NOT NULL REFERENCES users(id),
    merchant_name VARCHAR(255),
    name VARCHAR(255) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    date DATE NOT NULL,
    pending BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE recurring_charges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    user_id UUID NOT NULL REFERENCES users(id),
    merchant_name VARCHAR(255) NOT NULL,
    amount NUMERIC(10,2) NOT NULL,
    interval_days INTEGER NOT NULL,
    last_seen_date DATE NOT NULL,
    next_expected_date DATE NOT NULL,
    amount_changed BOOLEAN NOT NULL DEFAULT false,
    previous_amount NUMERIC(10,2)
);

CREATE TABLE recurring_charge_transactions (
    recurring_charge_id UUID NOT NULL REFERENCES recurring_charges(id),
    transaction_id UUID NOT NULL REFERENCES transactions(id),
    PRIMARY KEY (recurring_charge_id, transaction_id)
);

CREATE TABLE paychecks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    user_id UUID NOT NULL REFERENCES users(id),
    pay_date DATE NOT NULL
);

CREATE TABLE paycheck_deposits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    paycheck_id UUID NOT NULL REFERENCES paychecks(id),
    account_id UUID NOT NULL REFERENCES plaid_accounts(id),
    amount NUMERIC(10,2) NOT NULL
);

CREATE TABLE paycheck_allocations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    paycheck_deposit_id UUID NOT NULL REFERENCES paycheck_deposits(id),
    name VARCHAR(255) NOT NULL,
    amount NUMERIC(10,2) NOT NULL
);
