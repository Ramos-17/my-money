import { useEffect, useState } from "react"
import {
  listPaychecks,
  createPaycheck,
  deletePaycheck,
  getAccounts,
  type Paycheck,
  type Account,
} from "./api"

type DraftAllocation = { name: string; amount: string }
type DraftDeposit = { accountId: string; amount: string; allocations: DraftAllocation[] }

function emptyDeposit(): DraftDeposit {
  return { accountId: "", amount: "", allocations: [{ name: "", amount: "" }] }
}

function formatShortDate(isoDate: string): string {
  const [, month, day] = isoDate.split("-")
  return `${Number(month)}/${Number(day)}`
}

function PaycheckPlanner() {
  const [paychecks, setPaychecks] = useState<Paycheck[]>([])
  const [accounts, setAccounts] = useState<Account[]>([])
  const [payDate, setPayDate] = useState("")
  const [deposits, setDeposits] = useState<DraftDeposit[]>([emptyDeposit()])
  const [error, setError] = useState("")

  function loadPaychecks() {
    setError("")
    listPaychecks()
      .then(setPaychecks)
      .catch(() => setError("Could not load paychecks."))
  }

  useEffect(() => {
    loadPaychecks()
    getAccounts()
      .then(setAccounts)
      .catch(() => setError("Could not load accounts."))
  }, [])

  function updateDeposit(index: number, changes: Partial<DraftDeposit>) {
    setDeposits((current) =>
      current.map((deposit, i) => (i === index ? { ...deposit, ...changes } : deposit)),
    )
  }

  function updateAllocation(depositIndex: number, allocationIndex: number, changes: Partial<DraftAllocation>) {
    setDeposits((current) =>
      current.map((deposit, i) => {
        if (i !== depositIndex) return deposit
        return {
          ...deposit,
          allocations: deposit.allocations.map((allocation, j) =>
            j === allocationIndex ? { ...allocation, ...changes } : allocation,
          ),
        }
      }),
    )
  }

  function addDeposit() {
    setDeposits((current) => [...current, emptyDeposit()])
  }

  function removeDeposit(index: number) {
    setDeposits((current) => current.filter((_, i) => i !== index))
  }

  function addAllocation(depositIndex: number) {
    setDeposits((current) =>
      current.map((deposit, i) =>
        i === depositIndex
          ? { ...deposit, allocations: [...deposit.allocations, { name: "", amount: "" }] }
          : deposit,
      ),
    )
  }

  function removeAllocation(depositIndex: number, allocationIndex: number) {
    setDeposits((current) =>
      current.map((deposit, i) =>
        i === depositIndex
          ? { ...deposit, allocations: deposit.allocations.filter((_, j) => j !== allocationIndex) }
          : deposit,
      ),
    )
  }

  async function handleAddPaycheck(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    try {
      const payload = deposits
        .filter((deposit) => deposit.accountId && deposit.amount)
        .map((deposit) => ({
          account_id: deposit.accountId,
          amount: Number(deposit.amount),
          allocations: deposit.allocations
            .filter((allocation) => allocation.name && allocation.amount)
            .map((allocation) => ({ name: allocation.name, amount: Number(allocation.amount) })),
        }))

      await createPaycheck(payDate, payload)
      setPayDate("")
      setDeposits([emptyDeposit()])
      loadPaychecks()
    } catch {
      setError("Could not add paycheck.")
    }
  }

  async function handleDelete(paycheckId: string) {
    setError("")
    try {
      await deletePaycheck(paycheckId)
      loadPaychecks()
    } catch {
      setError("Could not delete paycheck.")
    }
  }

  return (
    <div>
      {error && <p>{error}</p>}

      {paychecks.length === 0 && <p>No paychecks tracked yet.</p>}
      {paychecks.map((paycheck) => (
        <div key={paycheck.id} className="paycheck-card">
          <h3>Paycheck Date: {formatShortDate(paycheck.pay_date)}</h3>
          {paycheck.deposits.map((deposit) => (
            <div key={deposit.id}>
              <p>
                <strong>
                  {deposit.institution_name ?? "Unknown bank"} {deposit.account_name} Amount: $
                  {deposit.amount.toFixed(2)}
                </strong>
              </p>
              <ul>
                {deposit.allocations.map((allocation) => (
                  <li key={allocation.id}>
                    {allocation.name}: ${allocation.amount.toFixed(2)}
                  </li>
                ))}
              </ul>
              <p>Leftover: ${deposit.leftover.toFixed(2)}</p>
            </div>
          ))}
          <p>
            <strong>Total Leftover: ${paycheck.total_leftover.toFixed(2)}</strong>
          </p>
          <button type="button" onClick={() => handleDelete(paycheck.id)}>
            Delete
          </button>
        </div>
      ))}

      <form onSubmit={handleAddPaycheck}>
        <h3>Add a paycheck</h3>
        <input
          type="date"
          value={payDate}
          onChange={(e) => setPayDate(e.target.value)}
        />

        {deposits.map((deposit, depositIndex) => (
          <div key={depositIndex} className="deposit-form-row">
            <select
              value={deposit.accountId}
              onChange={(e) => updateDeposit(depositIndex, { accountId: e.target.value })}
            >
              <option value="">Select account</option>
              {accounts.map((account) => (
                <option key={account.id} value={account.id}>
                  {account.institution_name ?? "Unknown bank"} — {account.name}
                </option>
              ))}
            </select>
            <input
              type="number"
              step="0.01"
              placeholder="Amount"
              value={deposit.amount}
              onChange={(e) => updateDeposit(depositIndex, { amount: e.target.value })}
            />
            {deposits.length > 1 && (
              <button type="button" onClick={() => removeDeposit(depositIndex)}>
                Remove account
              </button>
            )}

            {deposit.allocations.map((allocation, allocationIndex) => (
              <div key={allocationIndex} className="allocation-form-row">
                <input
                  type="text"
                  placeholder="Item name"
                  value={allocation.name}
                  onChange={(e) => updateAllocation(depositIndex, allocationIndex, { name: e.target.value })}
                />
                <input
                  type="number"
                  step="0.01"
                  placeholder="Amount"
                  value={allocation.amount}
                  onChange={(e) => updateAllocation(depositIndex, allocationIndex, { amount: e.target.value })}
                />
                {deposit.allocations.length > 1 && (
                  <button type="button" onClick={() => removeAllocation(depositIndex, allocationIndex)}>
                    Remove item
                  </button>
                )}
              </div>
            ))}
            <button type="button" onClick={() => addAllocation(depositIndex)}>
              Add item
            </button>
          </div>
        ))}

        <button type="button" onClick={addDeposit}>
          Add account
        </button>

        <button type="submit" disabled={!payDate}>
          Add paycheck
        </button>
      </form>
    </div>
  )
}

export default PaycheckPlanner
