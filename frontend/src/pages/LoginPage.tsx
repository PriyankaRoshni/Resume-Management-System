import { useState } from 'react'
import styles from './login.module.css'

export function LoginPage() {
  const [busy, setBusy] = useState(false)

  function signInWithGoogle() {
    setBusy(true)
    window.location.href = '/auth/google/start'
  }

  return (
    <div className={`appRoot ${styles.wrap}`}>
      <div className={`${styles.card} glass2`}>
        <div className={styles.title}>Welcome back</div>
        <div className={styles.subtitle}>Sign in to your account to continue</div>

        <div className={styles.social}>
          <button className="btn" type="button" onClick={signInWithGoogle} disabled={busy}>
            <span aria-hidden="true">G</span>
            Continue with Google
          </button>
        </div>

        <div className={styles.divider}>
          <span />
          <span className={styles.dividerText}>OR</span>
          <span />
        </div>

        <p className={styles.subtitle}>You&apos;ll be redirected to Google to grant access to your Gmail inbox.</p>
      </div>
    </div>
  )
}

