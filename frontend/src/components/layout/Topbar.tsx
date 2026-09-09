import styles from './shell.module.css'

export function Topbar() {
  return (
    <header className={styles.topbar}>
      <div>
        <div className={styles.pageTitle}>Dashboard Overview</div>
        <div className={styles.pageSubtitle}>Monitor system performance and resume processing analytics</div>
      </div>
      <div className={styles.topbarRight}>
        <button className="btn" type="button" aria-label="Notifications">
          <span aria-hidden="true">🔔</span>
          <span className="badge badgeWarn">3</span>
        </button>
        <div className={`${styles.userChip} glass`}>
          <div className={styles.avatar} aria-hidden="true">
            A
          </div>
          <div className={styles.userMeta}>
            <div className={styles.userName}>User</div>
            <div className={styles.userRole}>Administrator</div>
          </div>
        </div>
      </div>
    </header>
  )
}

