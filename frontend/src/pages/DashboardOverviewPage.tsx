import { useEffect, useMemo, useState } from 'react'
import styles from './pages.module.css'
import { apiFetch } from '../lib/api'

type Stat = { label: string; value: string; tint: 'blue' | 'green' | 'amber' | 'rose' }

type Overview = {
  total_emails_processed: number
  total_resumes_extracted: number
  domains_identified: number
  pending_resumes: number
  domain_counts: Array<{ name: string; value: number }>
  trend: Array<{ month: string; value: number }>
}

const DEFAULT_OVERVIEW: Overview = {
  total_emails_processed: 0,
  total_resumes_extracted: 0,
  domains_identified: 0,
  pending_resumes: 0,
  domain_counts: [],
  trend: [],
}

export function DashboardOverviewPage() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [overview, setOverview] = useState<Overview>(DEFAULT_OVERVIEW)

  async function refresh() {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch('/dashboard/overview')
      if (!res.ok) throw new Error(await res.text())
      const data = (await res.json()) as Overview
      setOverview(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    refresh().catch(() => {})
  }, [])

  const stats: Stat[] = useMemo(
    () => [
      { label: 'Total Emails Processed', value: String(overview.total_emails_processed), tint: 'blue' },
      { label: 'Total Resumes Extracted', value: String(overview.total_resumes_extracted), tint: 'green' },
      { label: 'Domains Identified', value: String(overview.domains_identified), tint: 'amber' },
      { label: 'Pending Resumes', value: String(overview.pending_resumes), tint: 'rose' },
    ],
    [overview],
  )

  const domainCounts = useMemo(() => overview.domain_counts, [overview.domain_counts])
  const trend = useMemo(() => overview.trend.map((t) => ({ month: t.month, v: t.value })), [overview.trend])

  const maxTrend = Math.max(1, ...trend.map((t) => t.v))
  const maxDomain = Math.max(1, ...domainCounts.map((d) => d.value))

  return (
    <div className={styles.stack}>
      <div className={styles.statsGrid}>
        {stats.map((s) => (
          <div key={s.label} className={`${styles.statCard} glass`}>
            <div className={`${styles.statIcon} ${styles[`tint_${s.tint}`]}`} aria-hidden="true" />
            <div className={styles.statValue}>{s.value}</div>
            <div className={styles.statLabel}>{s.label}</div>
          </div>
        ))}
      </div>

      <div className={styles.twoCol}>
        <section className={`${styles.panel} glass`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Resumes per Domain</div>
            <button className="btn" type="button" onClick={() => refresh().catch(() => {})} disabled={busy}>
              {busy ? 'Loading…' : 'Refresh'}
            </button>
          </div>

          <div className={styles.domainList}>
            {domainCounts.length === 0 ? (
              <div className="muted">No domain data yet. Upload resumes to populate.</div>
            ) : null}
            {domainCounts.map((d) => (
              <div key={d.name} className={styles.domainRow}>
                <div className={styles.domainName}>{d.name}</div>
                <div className={styles.domainBarTrack}>
                  <div
                    className={styles.domainBarFill}
                    style={{ width: `${Math.round((d.value / maxDomain) * 100)}%` }}
                  />
                </div>
                <div className={styles.domainValue}>{d.value}</div>
              </div>
            ))}
          </div>
        </section>

        <section className={`${styles.panel} glass`}>
          <div className={styles.panelHeader}>
            <div className={styles.panelTitle}>Processing Trend</div>
            <button className="btn" type="button" onClick={() => refresh().catch(() => {})} disabled={busy}>
              {busy ? 'Loading…' : 'Refresh'}
            </button>
          </div>

          <div className={styles.trendChart}>
            {trend.length === 0 ? (
              <div className="muted">No trend data yet.</div>
            ) : null}
            {trend.map((t) => (
              <div key={t.month} className={styles.trendCol}>
                <div
                  className={styles.trendBar}
                  style={{ height: `${Math.max(6, Math.round((t.v / maxTrend) * 100))}%` }}
                />
                <div className={styles.trendLabel}>{t.month}</div>
              </div>
            ))}
          </div>
        </section>
      </div>

      {error ? <div className={styles.errorBox}>{error}</div> : null}
    </div>
  )
}

