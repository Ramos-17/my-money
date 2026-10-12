import { useEffect, useState } from "react"
import { getAccounts, type Account } from "./api"

type AccountsProps = {
  refreshSignal?: number
}

function Accounts({ refreshSignal }: AccountsProps) {
  const [accounts, setAccounts] = useState<Account[]>([])
  const [error, setError] = useState("")

  useEffect(() => {
    setError("")
    getAccounts()
      .then(setAccounts)
      .catch(() => setError("Could not load accounts."))
  }, [refreshSignal])

  if (error) {
    return <p>{error}</p>
  }

  if (accounts.length === 0) {
    return <p>No accounts yet.</p>
  }

  return (
    <ul>
      {accounts.map((account) => (
        <li key={account.account_id}>
          {account.institution_name ?? "Unknown bank"} — {account.name}: {" "}
          {account.current_balance != null ? account.current_balance.toFixed(2) : "—"}{" "}
          {account.iso_currency_code ?? ""}
        </li>
      ))}
    </ul>
  )
}

export default Accounts
