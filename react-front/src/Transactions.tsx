import { useEffect, useState } from "react"
import { getTransactions, type Transaction } from "./api"

type TransactionsProps = {
  refreshSignal?: number
}

function Transactions({ refreshSignal }: TransactionsProps) {
  const [transactions, setTransactions] = useState<Transaction[]>([])
  const [error, setError] = useState("")

  function loadTransactions() {
    setError("")
    getTransactions()
      .then(setTransactions)
      .catch(() => setError("Could not load transactions."))
  }

  useEffect(loadTransactions, [refreshSignal])

  return (
    <div>
      <button type="button" onClick={loadTransactions}>
        Refresh transactions
      </button>
      {error && <p>{error}</p>}
      {!error && transactions.length === 0 && <p>No transactions yet.</p>}
      {transactions.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Date</th>
                <th>Bank</th>
                <th>Name</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => (
                <tr key={txn.transaction_id}>
                  <td>{txn.date}</td>
                  <td>{txn.institution_name ?? "—"}</td>
                  <td>{txn.name}</td>
                  <td>{txn.amount.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default Transactions
