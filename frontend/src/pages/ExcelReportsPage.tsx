import { useEffect, useMemo, useState } from 'react'
import styles from './pages.module.css'
import { apiFetch } from '../lib/api'

type Domain = 'Computer Science' | 'Electronics' | 'Mechanical' | 'Others'

type Row = {
  id: number
  name: string
  email: string
  domain: Domain
  skills: string
  education: string
  experience: string
  file: string
}

const domains: Domain[] = ['Computer Science', 'Electronics', 'Mechanical', 'Others']

export function ExcelReportsPage() {
  const [domain, setDomain] = useState<Domain>('Computer Science')
  const [allRows, setAllRows] = useState<Row[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setBusy(true)
    setError(null)
    try {
      const res = await apiFetch('/resumes')
      if (!res.ok) throw new Error(await res.text())
      const data = (await res.json()) as Array<{
        id: number
        full_name: string
        email: string | null
        domain: string
        skills: string | null
        education: string | null
        experience: string
        original_filename: string
      }>
      setAllRows(
        data.map((r) => ({
          id: r.id,
          name: r.full_name,
          email: r.email ?? '-',
          domain: (r.domain || 'Others') as Domain,
          skills: r.skills ?? '-',
          education: r.education ?? '-',
          experience: r.experience || '-',
          file: r.original_filename,
        })),
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    refresh().catch(() => {})
  }, [])

  const rows = useMemo(() => allRows.filter((r) => r.domain === domain), [allRows, domain])

  async function downloadExcel() {
    setBusy(true)
    setError(null)
    try {
      const qp = new URLSearchParams()
      qp.set('domain', domain)
      const res = await apiFetch(`/reports/excel?${qp.toString()}`)
      if (!res.ok) throw new Error(await res.text())
      const blob = await res.blob()
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${domain.replace(/\s/g, '_')}_Resumes.xlsx`
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

  return (
    <div className={styles.stack}>
      <div className={styles.pageHead}>
        <div className={styles.pageH1}>Domain-wise Excel Reports</div>
        <div className={styles.pageH2}>Generate and download structured resume data organized by engineering domains</div>
      </div>

      <section className={`${styles.panel} glass`}>
        <div className={styles.panelHeader}>
          <div className={styles.inline}>
            <span className="muted">Select Domain:</span>
            <select className="select" style={{ width: 220 }} value={domain} onChange={(e) => setDomain(e.target.value as Domain)}>
              {domains.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>
          <div className={styles.headerActions}>
            <button className="btn" type="button" onClick={() => refresh().catch(() => {})} disabled={busy}>
              {busy ? 'Loading…' : '⟳ Refresh Data'}
            </button>
            <button
              className="btn"
              type="button"
              onClick={() => downloadExcel().catch(() => {})}
              disabled={busy}
              style={{ borderColor: 'rgba(34,197,94,0.35)', background: 'rgba(34,197,94,0.14)' }}
            >
              {busy ? 'Working…' : '⬇ Download Excel'}
            </button>
          </div>
        </div>

        {error ? <div className={styles.errorBox}>{error}</div> : null}

        <div className={styles.excelHeader}>
          <div className={styles.excelTitle}>
            <span aria-hidden="true">📄</span> {domain.replace(/\s/g, '_')}_Resumes.xlsx
          </div>
          <div className="muted">{rows.length} records</div>
        </div>

        <div className={styles.tableWrap}>
          <table className="table">
            <thead>
              <tr>
                <th>Candidate Name</th>
                <th>Email ID</th>
                <th>Domain</th>
                <th>Skills Extracted</th>
                <th>Education</th>
                <th>Experience</th>
                <th>Resume File</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>{r.name}</td>
                  <td className="mono">{r.email}</td>
                  <td>{r.domain}</td>
                  <td>{r.skills}</td>
                  <td>{r.education}</td>
                  <td className="mono">{r.experience}</td>
                  <td className="mono">{r.file}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={styles.noteRow}>
          <span className="muted">Showing {rows.length} of {rows.length} records</span>
          <span className="muted">Rows per page: 50</span>
        </div>
      </section>
    </div>
  )
}

