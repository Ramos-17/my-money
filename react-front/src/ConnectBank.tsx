import { useEffect, useState } from "react"
import { usePlaidLink } from "react-plaid-link"
import { createLinkToken, exchangePublicToken, getAccounts } from "./api"

type ConnectBankProps = {
  onConnected?: () => void
}

function ConnectBank({ onConnected }: ConnectBankProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null)
  const [status, setStatus] = useState<string>("")
  const [hasAccounts, setHasAccounts] = useState(false)

  useEffect(() => {
    createLinkToken()
      .then(setLinkToken)
      .catch(() => setStatus("Could not start bank connection."))

    getAccounts()
      .then((accounts) => setHasAccounts(accounts.length > 0))
      .catch(() => {})
  }, [])

  const { open, ready } = usePlaidLink({
    token: linkToken ?? "",
    onSuccess: (publicToken, metadata) => {
      if (!publicToken) {
        setStatus("Bank connection did not return a token.")
        return
      }
      exchangePublicToken(publicToken, metadata.institution?.name ?? null)
        .then(() => {
          setStatus("Bank connected!")
          setHasAccounts(true)
          onConnected?.()
        })
        .catch(() => setStatus("Failed to finish connecting bank."))
    },
  })

  return (
    <div>
      <button type="button" onClick={() => open()} disabled={!ready || !linkToken}>
        {hasAccounts ? "Connect another bank" : "Connect a bank account"}
      </button>
      {status && <p>{status}</p>}
    </div>
  )
}

export default ConnectBank
