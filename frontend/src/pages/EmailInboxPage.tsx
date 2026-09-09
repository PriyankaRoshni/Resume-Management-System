import { useEffect, useState } from 'react'
import styles from './pages.module.css'
import { apiFetch } from '../lib/api'

type InboxItem = {
  id: number
  sender: string
  subject: string
  received_at: string
  type: 'PDF' | 'DOCX'
  status: 'Processed' | 'Pending' | 'Unprocessed'
}

export function EmailInboxPage() {
  const [from, setFrom] = useState('2025-01-01')
  const [to, setTo] = useState('2025-01-02')
  const [source, setSource] = useState('All Sources')
  const [attachment, setAttachment] = useState('All Types')
  const [selected, setSelected] = useState<Record<string, boolean>>({})
  const [items, setItems] = useState<InboxItem[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const allChecked = items.length > 0 && items.every((i) => selected[String(i.id)])

  function toggleAll() {
    const next: Record<string, boolean> = {}
    for (const it of items) next[String(it.id)] = !allChecked
    setSelected(next)
  }

  async function fetchEmails(params?: { applyFilters?: boolean }) {
    setBusy(true)
    setError(null)
    try {
      const qp = new URLSearchParams()
      if (params?.applyFilters) {
        if (from) qp.set('from', `${from}T00:00:00`)
        if (to) qp.set('to', `${to}T23:59:59`)
        if (source !== 'All Sources') qp.set('source', source)
        if (attachment !== 'All Types') qp.set('attachment', attachment)
      }
      const res = await apiFetch(`/emails${qp.toString() ? `?${qp.toString()}` : ''}`)
      if (!res.ok) throw new Error(await res.text())
      const data = (await res.json()) as Array<{
        id: number
        sender: string
        subject: string
        received_at: string
        source: 'Gmail' | 'Outlook' | 'Other'
        attachment_type: 'PDF' | 'DOCX'
        status: 'Processed' | 'Pending' | 'Unprocessed'
      }>
      setItems(
        data.map((d) => ({
          id: d.id,
          sender: d.sender,
          subject: d.subject,
          received_at: d.received_at,
          type: d.attachment_type,
          status: d.status,
        })),
      )
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setBusy(false)
    }
  }

  useEffect(() => {
    fetchEmails().catch(() => {})
  }, [])

  return (
    <div className={styles.inboxGrid}>
      <aside className={`${styles.filterPanel} glass`}>
        <div className={styles.panelTitle}>Filters</div>

        <div className={styles.fieldGroup}>
          <div className={styles.fieldLabel}>Date Range</div>
          <label className={styles.field}>
            <div className={styles.fieldHint}>From Date</div>
            <input className="input" type="date" value={from} onChange={(e) => setFrom(e.target.value)} />
          </label>
          <label className={styles.field}>
            <div className={styles.fieldHint}>To Date</div>
            <input className="input" type="date" value={to} onChange={(e) => setTo(e.target.value)} />
          </label>
        </div>

        <label className={styles.field}>
          <div className={styles.fieldLabel}>Email Source</div>
          <select className="select" value={source} onChange={(e) => setSource(e.target.value)}>
            <option>All Sources</option>
            <option>Gmail</option>
            <option>Outlook</option>
          </select>
        </label>

        <label className={styles.field}>
          <div className={styles.fieldLabel}>Attachment Type</div>
          <select className="select" value={attachment} onChange={(e) => setAttachment(e.target.value)}>
            <option>All Types</option>
            <option>PDF</option>
            <option>DOCX</option>
          </select>
        </label>

        <div className={styles.btnRow}>
          <button className="btn btnPrimary" type="button" onClick={() => fetchEmails({ applyFilters: true })} disabled={busy}>
            Apply Filter
          </button>
          <button
            className="btn"
            type="button"
            onClick={() => {
              setFrom('2025-01-01')
              setTo('2025-01-02')
              setSource('All Sources')
              setAttachment('All Types')
              fetchEmails().catch(() => {})
            }}
            disabled={busy}
          >
            Reset
          </button>
        </div>
      </aside>

      <section className={`${styles.panel} glass`}>
        <div className={styles.panelHeader}>
          <div>
            <div className={styles.panelTitle}>Resume Emails</div>
            <div className={styles.panelSubtitle}>{items.length} emails found</div>
          </div>
          <div className={styles.headerActions}>
            <button className="btn btnPrimary" type="button">
              Process Selected
            </button>
            <button className="btn" type="button">
              Download
            </button>
          </div>
        </div>

        {error ? <div className={styles.errorBox}>{error}</div> : null}

        <div className={styles.tableWrap}>
          <table className="table">
            <thead>
              <tr>
                <th style={{ width: 42 }}>
                  <input type="checkbox" checked={allChecked} onChange={toggleAll} />
                </th>
                <th>Sender Email</th>
                <th>Subject</th>
                <th>Received</th>
                <th>Type</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.id}>
                  <td>
                    <input
                      type="checkbox"
                      checked={!!selected[String(it.id)]}
                      onChange={(e) => setSelected((s) => ({ ...s, [String(it.id)]: e.target.checked }))}
                    />
                  </td>
                  <td className="mono">{it.sender}</td>
                  <td>{it.subject}</td>
                  <td className="mono">{new Date(it.received_at).toLocaleString()}</td>
                  <td>{it.type}</td>
                  <td>
                    {it.status === 'Processed' ? (
                      <span className="badge badgeGood">Processed</span>
                    ) : it.status === 'Pending' ? (
                      <span className="badge badgeWarn">Pending</span>
                    ) : (
                      <span className="badge badgeDim">Unprocessed</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className={styles.noteRow}>
          <span className="muted">{busy ? 'Loading…' : 'Data source: backend /emails'}</span>
          <span className="muted mono">
            {from} → {to} · {source} · {attachment}
          </span>
        </div>
      </section>
    </div>
  )
}

