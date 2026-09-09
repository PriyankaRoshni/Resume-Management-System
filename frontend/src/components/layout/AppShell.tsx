import { Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import { apiFetch } from '../../lib/api'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import styles from './shell.module.css'

export function AppShell() {
  useEffect(() => {
    apiFetch('/emails/sync').catch(() => {})
  }, [])

  return (
    <div className={`appRoot ${styles.shell}`}>
      <Sidebar />
      <div className={styles.main}>
        <Topbar />
        <div className={styles.content}>
          <Outlet />
        </div>
        <footer className={styles.footer}>
          <span className={styles.footerText}>
            © {new Date().getFullYear()} Automated Resume Processing System
          </span>
        </footer>
      </div>
    </div>
  )
}

