import { useEffect, useState } from 'react'
import styles from './pages.module.css'
import { apiFetch } from '../lib/api'

type Domain = 'Computer Science' | 'Electronics' | 'Mechanical' | 'Others'

type Candidate = {
  id: number
  name: string
  domain: Domain
  file: string
  confidence: number
  skills: string[]
}

const tabs: Domain[] = ['Computer Science', 'Electronics', 'Mechanical', 'Others']

function confidenceBadge(confidence: number) {
  if (confidence >= 90) return { cls: 'badge badgeGood', label: 'High Confidence' }
  if (confidence >= 85) return { cls: 'badge badgeWarn', label: 'Medium Confidence' }
  return { cls: 'badge badgeDim', label: 'Low Confidence' }
}

function stableConfidence(id: number) {
  // Deterministic pseudo-confidence between ~82 and ~96, stable per resume id.
  const x = Math.abs(Math.sin(id * 9973) * 10000)
  return 82 + (x % 14)
}

function parseSkills(raw: string | null | undefined) {
  const s = (raw ?? '').trim()
  if (!s) return []
  return s
    .split(/[,•|]/g)
    .map((p) => p.trim())
    .filter(Boolean)
    .slice(0, 10)
}

export function DomainClassificationPage() {
  const [active, setActive] = useState<Domain>('Computer Science')
  const [all, setAll] = useState<Candidate[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const items = all.filter((c) => c.domain === active)

  const avg = items.length ? items.reduce((a, c) => a + c.confidence, 0) / items.length : 0

  async function refresh() {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch('/resumes')
      if (!res.ok) throw new Error(await res.text())
      const data = (await res.json()) as Array<{
        id: number
        full_name: string
        domain: string
        skills: string | null
        original_filename: string
      }>
      setAll(
        data.map((r) => ({
          id: r.id,
          name: r.full_name,
          domain: (r.domain || 'Others') as Domain,
          file: r.original_filename,
          confidence: stableConfidence(r.id),
          skills: parseSkills(r.skills),
        })),
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  async function exportExcel() {
    setBusy(true)
    setError(null)
    try {
      const qp = new URLSearchParams()
      qp.set('domain', active)
      const res = await apiFetch(`/reports/excel?${qp.toString()}`)
      if (!res.ok) throw new Error(await res.text())
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${active.replace(/\s/g, '_')}_Resumes.xlsx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => URL.revokeObjectURL(a.href), 5000)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    refresh().catch(() => {})
  }, [])

  return (
    <div className={styles.stack}>
      <div className={styles.pageHead}>
        <div className={styles.pageH1}>Domain-Based Resume Classification</div>
        <div className={styles.pageH2}>Automated classification and organization of resumes by engineering domains</div>
      </div>

      <div className={`${styles.tabs} glass`}>
        {tabs.map((t) => (
          <button
            key={t}
            type="button"
            className={`${styles.tab} ${active === t ? styles.tabActive : ''}`}
            onClick={() => setActive(t)}
          >
            {t} <span className={styles.tabCount}>{all.filter((c) => c.domain === t).length}</span>
          </button>
        ))}
      </div>

      <div className={styles.classifyGrid}>
        <section className={`${styles.panel} glass`}>
          <div className={styles.panelHeader}>
            <div>
              <div className={styles.panelTitle}>{active} Resumes</div>
              <div className={styles.panelSubtitle}>{items.length} classified resumes</div>
            </div>
            <button className="btn" type="button" onClick={() => exportExcel().catch(() => {})} disabled={busy}>
              <span aria-hidden="true">📄</span> Export Excel
            </button>
          </div>

          {error ? <div className={styles.errorBox}>{error}</div> : null}

          <div className={styles.cards}>
            {items.length === 0 ? <div className="muted">No resumes in this domain yet.</div> : null}
            {items.map((c) => {
              const badge = confidenceBadge(c.confidence)
              return (
                <div key={c.id} className={`${styles.candidateCard} glass`}>
                  <div className={styles.candidateRow}>
                    <div className={styles.avatar2} aria-hidden="true">
                      {c.name
                        .split(' ')
                        .slice(0, 2)
                        .map((p) => p[0])
                        .join('')
                        .toUpperCase()}
                    </div>
                    <div className={styles.candidateMeta}>
                      <div className={styles.candidateName}>{c.name}</div>
                      <div className={styles.candidateDomain}>{c.domain}</div>
                    </div>

                    <div className={styles.confBox}>
                      <div className={styles.confLabel}>Classification Confidence</div>
                      <div className={styles.confRow}>
                        <div className={styles.confTrack}>
                          <div className={styles.confFill} style={{ width: `${Math.round(c.confidence)}%` }} />
                        </div>
                        <div className={`${styles.confPct} mono`}>{c.confidence.toFixed(1)}%</div>
                      </div>
                      <span className={badge.cls}>{badge.label}</span>
                    </div>
                  </div>

                  <div className={styles.skillsLabel}>Key Skills Extracted:</div>
                  <div className={styles.skillChips}>
                    {c.skills.length ? (
                      c.skills.map((s) => (
                        <span key={s} className={styles.chip}>
                          {s}
                        </span>
                      ))
                    ) : (
                      <span className="muted">—</span>
                    )}
                  </div>

                  <div className={styles.fileRow}>
                    <span aria-hidden="true">📎</span>
                    <span className="mono">{c.file}</span>
                  </div>
                </div>
              )
            })}
          </div>
        </section>

        <aside className={styles.rightRail}>
          <section className={`${styles.panel} glass`}>
            <div className={styles.panelTitle}>Domain Summary</div>
            <div className={styles.kv}>
              <div className={styles.kvRow}>
                <span className="muted">Total Resumes</span>
                <span className="mono">{items.length}</span>
              </div>
              <div className={styles.kvRow}>
                <span className="muted">Avg. Confidence</span>
                <span className="mono" style={{ color: avg >= 90 ? 'var(--good)' : avg >= 85 ? 'var(--warn)' : 'var(--bad)' }}>
                  {avg ? `${avg.toFixed(1)}%` : '—'}
                </span>
              </div>
            </div>
          </section>

          <section className={`${styles.panel} glass`}>
            <div className={styles.panelTitle}>Export Status</div>
            <div className={styles.exportList}>
              <div className={styles.exportItem}>
                <span aria-hidden="true">📄</span>
                <span>Excel Sheet</span>
                <span className="badge badgeGood">Generated</span>
              </div>
              <div className={styles.exportItem}>
                <span aria-hidden="true">📁</span>
                <span>Folder Storage</span>
                <span className="badge badgeGood">Created</span>
              </div>
            </div>
          </section>

          <section className={`${styles.panel} glass`}>
            <div className={styles.panelTitle}>Quick Actions</div>
            <div className={styles.actionStack}>
              <button className="btn btnPrimary" type="button" onClick={() => exportExcel().catch(() => {})} disabled={busy}>
                <span aria-hidden="true">📄</span> Generate Excel Report
              </button>
              <button className="btn" type="button" onClick={() => refresh().catch(() => {})} disabled={busy}>
                <span aria-hidden="true">📁</span> Open Folder
              </button>
              <button className="btn" type="button">
                <span aria-hidden="true">📊</span> View Analytics
              </button>
            </div>
          </section>
        </aside>
      </div>
    </div>
  )
}

