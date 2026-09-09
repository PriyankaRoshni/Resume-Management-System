import { useEffect, useMemo, useState } from 'react'
import styles from './pages.module.css'
import { apiFetch, getApiBase } from '../lib/api'

type Resume = {
  id: number
  original_filename: string
  stored_path: string
  full_name: string
  profession: string
  experience: string
  created_at: string
}

export function ResumeProcessingPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [items, setItems] = useState<Resume[]>([])

  const canUpload = useMemo(() => !!selectedFile && !busy, [selectedFile, busy])

  async function refresh() {
    setError(null)
    const res = await apiFetch('/resumes')
    if (!res.ok) throw new Error(await res.text())
    const data = (await res.json()) as Resume[]
    setItems(data)
  }

  async function onUpload() {
    if (!selectedFile) return
    setBusy(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', selectedFile)
      const res = await apiFetch('/resumes/upload', { method: 'POST', body: form })
      if (!res.ok) throw new Error(await res.text())
      setSelectedFile(null)
      await refresh()
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    refresh().catch((e) => setError(e instanceof Error ? e.message : String(e)))
  }, [])

  return (
    <div className={styles.stack}>
      <section className={`${styles.panel} glass`}>
        <div className={styles.panelHeader}>
          <div>
            <div className={styles.panelTitle}>Resume Processing</div>
            <div className={styles.panelSubtitle}>Upload a PDF/DOCX and classify it (current backend capability)</div>
          </div>
          <div className={styles.headerActions}>
            <button className="btn" type="button" onClick={() => refresh().catch(() => {})} disabled={busy}>
              Refresh
            </button>
          </div>
        </div>

        <div className={styles.uploadRow}>
          <input
            className={styles.file}
            type="file"
            accept=".pdf,.docx"
            onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            disabled={busy}
          />
          <button className="btn btnPrimary" onClick={onUpload} disabled={!canUpload} type="button">
            {busy ? 'Working…' : 'Upload & Classify'}
          </button>
        </div>

        <div className={styles.noteRow}>
          <span className="muted">
            Backend: <span className="mono">{getApiBase() || '(auto)'}</span>
          </span>
          <span className="muted">Allowed: PDF, DOCX</span>
        </div>

        {error ? <div className={styles.errorBox}>{error}</div> : null}
      </section>

      <section className={`${styles.panel} glass`}>
        <div className={styles.panelHeader}>
          <div className={styles.panelTitle}>Processed Resumes</div>
          <div className={styles.panelSubtitle}>{items.length} record(s)</div>
        </div>

        <div className={styles.tableWrap}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Profession (current)</th>
                <th>Experience</th>
                <th>File</th>
                <th>Created</th>
              </tr>
            </thead>
            <tbody>
              {items.length === 0 ? (
                <tr>
                  <td colSpan={6} className={styles.empty}>
                    No resumes yet. Upload one to get started.
                  </td>
                </tr>
              ) : (
                items.map((r) => (
                  <tr key={r.id}>
                    <td className="mono">{r.id}</td>
                    <td>{r.full_name}</td>
                    <td>{r.profession}</td>
                    <td>{r.experience || '-'}</td>
                    <td className="mono">{r.original_filename}</td>
                    <td className="mono">{new Date(r.created_at).toLocaleString()}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}

