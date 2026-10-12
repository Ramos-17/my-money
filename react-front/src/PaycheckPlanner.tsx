import { useEffect, useState } from "react"
import {
  listPaychecks,
  createPaycheck,
  updatePaycheck,
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
  const [editingPaycheckId, setEditingPaycheckId] = useState<string | null>(null)
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

  function resetForm() {
    setPayDate("")
    setDeposits([emptyDeposit()])
    setEditingPaycheckId(null)
  }

  function handleEdit(paycheck: Paycheck) {
    setError("")
    setEditingPaycheckId(paycheck.id)
    setPayDate(paycheck.pay_date)
    setDeposits(
      paycheck.deposits.map((deposit) => ({
        accountId: deposit.account_id,
        amount: String(deposit.amount),
        allocations: deposit.allocations.length
          ? deposit.allocations.map((allocation) => ({
              name: allocation.name,
              amount: String(allocation.amount),
            }))
          : [{ name: "", amount: "" }],
      })),
    )
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")

    const payload = deposits
      .filter((deposit) => deposit.accountId && deposit.amount)
      .map((deposit) => ({
        account_id: deposit.accountId,
        amount: Number(deposit.amount),
        allocations: deposit.allocations
          .filter((allocation) => allocation.name && allocation.amount)
          .map((allocation) => ({ name: allocation.name, amount: Number(allocation.amount) })),
      }))

    if (payload.length === 0) {
      setError("Select an account and enter an amount for at least one deposit.")
      return
    }

    try {
      if (editingPaycheckId) {
        await updatePaycheck(editingPaycheckId, payDate, payload)
      } else {
        await createPaycheck(payDate, payload)
      }
      resetForm()
      loadPaychecks()
    } catch {
      setError(editingPaycheckId ? "Could not save changes." : "Could not add paycheck.")
    }
  }

  async function handleDelete(paycheckId: string) {
    setError("")
    try {
      await deletePaycheck(paycheckId)
      if (editingPaycheckId === paycheckId) {
        resetForm()
      }
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
            <div key={deposit.id} className="deposit-block">
              <p className="deposit-heading">
                {deposit.institution_name ?? "Unknown bank"} — {deposit.account_name}
              </p>
              <p className="deposit-amount">Deposit: ${deposit.amount.toFixed(2)}</p>
              {deposit.allocations.length > 0 && (
                <>
                  <p className="items-label">Items</p>
                  <ul>
                    {deposit.allocations.map((allocation) => (
                      <li key={allocation.id}>
                        {allocation.name}: ${allocation.amount.toFixed(2)}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              <p>Leftover: ${deposit.leftover.toFixed(2)}</p>
            </div>
          ))}
          <p>
            <strong>Total Leftover: ${paycheck.total_leftover.toFixed(2)}</strong>
          </p>
          {paycheck.editable && (
            <button type="button" onClick={() => handleEdit(paycheck)}>
              Edit
            </button>
          )}
          <button type="button" onClick={() => handleDelete(paycheck.id)}>
            Delete
          </button>
        </div>
      ))}

      <form onSubmit={handleSubmit}>
        <h3>{editingPaycheckId ? "Edit paycheck" : "Add a paycheck"}</h3>
        <input
          type="date"
          value={payDate}
          onChange={(e) => setPayDate(e.target.value)}
        />

        {deposits.map((deposit, depositIndex) => (
          <div key={depositIndex} className="deposit-form-row">
            <label className="field-label">Account and deposit amount</label>
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
              placeholder="Deposit amount"
              value={deposit.amount}
              onChange={(e) => updateDeposit(depositIndex, { amount: e.target.value })}
            />
            {deposits.length > 1 && (
              <button type="button" onClick={() => removeDeposit(depositIndex)}>
                Remove account
              </button>
            )}

            <label className="field-label items-label">Items for this account</label>
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
                  placeholder="Item amount"
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
          {editingPaycheckId ? "Save changes" : "Add paycheck"}
        </button>
        {editingPaycheckId && (
          <button type="button" onClick={resetForm}>
            Cancel
          </button>
        )}
      </form>
    </div>
  )
}

export default PaycheckPlanner
