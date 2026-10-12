const API_BASE_URL = "http://localhost:8000"

export type CurrentUser = {
  id: string
  email: string
  first: string
  last: string
  username: string
}

export async function login(username: string, password: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ username, password }),
  })

  if (!response.ok) {
    throw new Error("Invalid username or password")
  }
}

export async function signup(
  username: string,
  password: string,
  email: string,
  first: string,
  last: string,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password, email, first, last }),
  })

  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new Error(data?.detail ?? "Could not create account")
  }
}

export async function logout(): Promise<void> {
  await fetch(`${API_BASE_URL}/auth/logout`, {
    method: "POST",
    credentials: "include",
  })
}

export async function getCurrentUser(): Promise<CurrentUser | null> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, {
    credentials: "include",
  })

  if (!response.ok) {
    return null
  }

  return response.json()
}

export async function createLinkToken(): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/plaid/create_link_token`, {
    method: "POST",
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to create link token")
  }

  const data = await response.json()
  return data.link_token
}

export async function exchangePublicToken(publicToken: string, institutionName: string | null): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/plaid/exchange_public_token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ public_token: publicToken, institution_name: institutionName }),
  })

  if (!response.ok) {
    throw new Error("Failed to exchange public token")
  }

  const data = await response.json()
  return data.item_id
}

export type Transaction = {
  transaction_id: string
  account_id: string
  institution_name: string | null
  name: string
  amount: number
  date: string
  pending: boolean
}

export async function getTransactions(): Promise<Transaction[]> {
  const response = await fetch(`${API_BASE_URL}/plaid/transactions`, {
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to load transactions")
  }

  const data = await response.json()
  return data.transactions
}

export type Account = {
  id: string
  account_id: string
  institution_name: string | null
  name: string
  type: string
  subtype: string | null
  available_balance: number | null
  current_balance: number | null
  iso_currency_code: string | null
}

export async function getAccounts(): Promise<Account[]> {
  const response = await fetch(`${API_BASE_URL}/plaid/accounts`, {
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to load accounts")
  }

  const data = await response.json()
  return data.accounts
}

export type PaycheckAllocation = {
  id: string
  name: string
  amount: number
}

export type PaycheckDeposit = {
  id: string
  account_id: string
  account_name: string
  institution_name: string | null
  amount: number
  allocations: PaycheckAllocation[]
  leftover: number
}

export type Paycheck = {
  id: string
  pay_date: string
  deposits: PaycheckDeposit[]
  total_leftover: number
  created: string
}

export type NewPaycheckAllocation = {
  name: string
  amount: number
}

export type NewPaycheckDeposit = {
  account_id: string
  amount: number
  allocations: NewPaycheckAllocation[]
}

export async function listPaychecks(): Promise<Paycheck[]> {
  const response = await fetch(`${API_BASE_URL}/paychecks`, {
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to load paychecks")
  }

  return response.json()
}

export async function createPaycheck(payDate: string, deposits: NewPaycheckDeposit[]): Promise<Paycheck> {
  const response = await fetch(`${API_BASE_URL}/paychecks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({ pay_date: payDate, deposits }),
  })

  if (!response.ok) {
    throw new Error("Failed to create paycheck")
  }

  return response.json()
}

export async function deletePaycheck(paycheckId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/paychecks/${paycheckId}`, {
    method: "DELETE",
    credentials: "include",
  })

  if (!response.ok) {
    throw new Error("Failed to delete paycheck")
  }
}
