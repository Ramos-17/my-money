import { useState } from "react"
import ConnectBank from "./ConnectBank"
import Transactions from "./Transactions"
import Accounts from "./Accounts"

function Dashboard() {
  const [refreshSignal, setRefreshSignal] = useState(0)

  return (
    <div>
      <ConnectBank onConnected={() => setRefreshSignal((n) => n + 1)} />
      <h2>Accounts</h2>
      <Accounts refreshSignal={refreshSignal} />
      <h2>Transactions</h2>
      <Transactions refreshSignal={refreshSignal} />
    </div>
  )
}

export default Dashboard
