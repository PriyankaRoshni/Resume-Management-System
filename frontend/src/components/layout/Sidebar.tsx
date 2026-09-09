import { NavLink, useNavigate } from 'react-router-dom'
import styles from './shell.module.css'

const items: Array<{ to: string; label: string }> = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/inbox', label: 'Email Inbox' },
  { to: '/processing', label: 'Resume Processing' },
  { to: '/classification', label: 'Domain Classification' },
  { to: '/excel', label: 'Excel Reports' },
]

export function Sidebar() {
  const nav = useNavigate()
  return (
    <aside className={`${styles.sidebar} glass2`}>
      <div className={styles.brandRow}>
        <div className={styles.brandIcon} aria-hidden="true">
          ✉
        </div>
        <div>
          <div className={styles.brandTitle}>Resume Processing</div>
          <div className={styles.brandSub}>System Dashboard</div>
        </div>
      </div>

      <nav className={styles.nav}>
        {items.map((it) => (
          <NavLink
            key={it.to}
            to={it.to}
            className={({ isActive }) => `${styles.navItem} ${isActive ? styles.navItemActive : ''}`}
          >
            <span className={styles.navDot} aria-hidden="true" />
            {it.label}
          </NavLink>
        ))}
      </nav>

      <div className={styles.sidebarBottom}>
        <button
          type="button"
          className={styles.navItem}
          onClick={() => {
            localStorage.removeItem('auth')
            nav('/login', { replace: true })
          }}
        >
          <span className={styles.navDot} aria-hidden="true" />
          Sign out
        </button>
      </div>
    </aside>
  )
}

