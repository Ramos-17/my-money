import { useEffect, useState } from "react"
import { Routes, Route, Link } from "react-router-dom"
import { getCurrentUser, login, logout, signup } from "./api"
import Dashboard from "./Dashboard"
import PaycheckPlanner from "./PaycheckPlanner"
import "./App.css"

function App() {
  const [mode, setMode] = useState<"login" | "signup">("login")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [email, setEmail] = useState("")
  const [first, setFirst] = useState("")
  const [last, setLast] = useState("")
  const [isLoggedIn, setIsLoggedIn] = useState<boolean | null>(null)
  const [error, setError] = useState("")
  const [message, setMessage] = useState("")

  useEffect(() => {
    getCurrentUser().then((user) => setIsLoggedIn(user !== null))
  }, [])

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    try {
      await login(username, password)
      setIsLoggedIn(true)
    } catch {
      setError("Invalid username or password")
    }
  }

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    try {
      await signup(username, password, email, first, last)
      setMessage("Account created! You can log in now.")
      setMode("login")
      setPassword("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create account")
    }
  }

  async function handleLogout() {
    await logout()
    setIsLoggedIn(false)
  }

  if (isLoggedIn === null) {
    return <p>Loading...</p>
  }

  if (isLoggedIn) {
    return (
      <div>
        <h1>MyMoney</h1>
        <nav>
          <Link to="/">Dashboard</Link>
          <Link to="/bills">Track Bills</Link>
          <button type="button" onClick={handleLogout}>
            Log out
          </button>
        </nav>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/bills" element={<PaycheckPlanner />} />
        </Routes>
      </div>
    )
  }

  if (mode === "signup") {
    return (
      <form onSubmit={handleSignup}>
        <h1>Sign up</h1>
        <input
          type="text"
          placeholder="First name"
          value={first}
          onChange={(e) => setFirst(e.target.value)}
        />
        <input
          type="text"
          placeholder="Last name"
          value={last}
          onChange={(e) => setLast(e.target.value)}
        />
        <input
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <button type="submit">Sign up</button>
        {error && <p>{error}</p>}
        <p>
          Already have an account?{" "}
          <button type="button" onClick={() => { setMode("login"); setError("") }}>
            Log in
          </button>
        </p>
      </form>
    )
  }

  return (
    <form onSubmit={handleLogin}>
      <h1>MyMoney</h1>
      <input
        type="text"
        placeholder="Username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        type="password"
        placeholder="Password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button type="submit">Log in</button>
      {error && <p>{error}</p>}
      {message && <p>{message}</p>}
      <p>
        Need an account?{" "}
        <button type="button" onClick={() => { setMode("signup"); setError(""); setMessage("") }}>
          Sign up
        </button>
      </p>
    </form>
  )
}

export default App
