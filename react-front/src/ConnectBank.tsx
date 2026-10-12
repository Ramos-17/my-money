import { useEffect, useState } from "react"
import { usePlaidLink } from "react-plaid-link"
import { createLinkToken, exchangePublicToken } from "./api"

type ConnectBankProps = {
  onConnected?: () => void
}

function ConnectBank({ onConnected }: ConnectBankProps) {
  const [linkToken, setLinkToken] = useState<string | null>(null)
  const [status, setStatus] = useState<string>("")

  useEffect(() => {
    createLinkToken()
      .then(setLinkToken)
      .catch(() => setStatus("Could not start bank connection."))
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
          onConnected?.()
        })
        .catch(() => setStatus("Failed to finish connecting bank."))
    },
  })

  return (
    <div>
      <button type="button" onClick={() => open()} disabled={!ready || !linkToken}>
        Connect a bank account
      </button>
      {status && <p>{status}</p>}
    </div>
  )
}

export default ConnectBank
