const ENV_BASE = import.meta.env.VITE_API_URL as string | undefined

const CANDIDATES = [ENV_BASE, 'http://localhost:8000', 'http://localhost:8001'].filter(Boolean) as string[]

let cachedBase: string | null = ENV_BASE ?? null

function joinUrl(base: string, path: string) {
  if (path.startsWith('http://') || path.startsWith('https://')) return path
  if (!path.startsWith('/')) path = `/${path}`
  return `${base.replace(/\/+$/, '')}${path}`
}

async function tryFetch(base: string, path: string, init?: RequestInit) {
  const url = joinUrl(base, path)
  const res = await fetch(url, init)
  return res
}

export async function apiFetch(path: string, init?: RequestInit) {
  const bases = cachedBase ? [cachedBase, ...CANDIDATES.filter((b) => b !== cachedBase)] : CANDIDATES

  let lastErr: unknown = null
  for (const base of bases) {
    try {
      const res = await tryFetch(base, path, init)
      // If we got a response at all, treat this base as valid (even if 4xx from app logic).
      cachedBase = base
      return res
    } catch (e) {
      lastErr = e
      // try next base
    }
  }
  throw lastErr instanceof Error ? lastErr : new Error(String(lastErr))
}

export function getApiBase() {
  return cachedBase ?? (CANDIDATES[0] ?? '')
}

