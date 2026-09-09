import { Navigate, Route, Routes } from 'react-router-dom'
import './styles/glass.css'

import { AppShell } from './components/layout/AppShell'
import { LoginPage } from './pages/LoginPage'
import { DashboardOverviewPage } from './pages/DashboardOverviewPage'
import { EmailInboxPage } from './pages/EmailInboxPage'
import { ResumeProcessingPage } from './pages/ResumeProcessingPage'
import { DomainClassificationPage } from './pages/DomainClassificationPage'
import { ExcelReportsPage } from './pages/ExcelReportsPage'
import { useEffect, useState } from 'react'
import { apiFetch } from './lib/api'

type Me = {
  id: number
  email: string
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<Me | null | undefined>(undefined)

  useEffect(() => {
    apiFetch('/me')
      .then(async (res) => {
        if (!res.ok) {
          setUser(null)
          return
        }
        const data = (await res.json()) as Me
        setUser(data)
      })
      .catch(() => {
        setUser(null)
      })
  }, [])

  if (user === undefined) {
    return null
  }
  if (user === null) {
    return <Navigate to="/login" replace />
  }
  return <>{children}</>
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardOverviewPage />} />
        <Route path="/inbox" element={<EmailInboxPage />} />
        <Route path="/processing" element={<ResumeProcessingPage />} />
        <Route path="/classification" element={<DomainClassificationPage />} />
        <Route path="/excel" element={<ExcelReportsPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}

export default App
