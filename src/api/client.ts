const DEFAULT_API_URL =
  'http://localhost:8000'

declare global {
  interface Window {
    __APP_CONFIG__?: {
      API_URL?: string
      APP_ENV?: string
    }
  }
}

export const API_URL = (
  window.__APP_CONFIG__?.API_URL ||
  import.meta.env.VITE_API_URL ||
  DEFAULT_API_URL
).replace(/\/$/, '')

export class ApiError extends Error {
  status: number
  requestId: string | null

  constructor(message: string, status: number, requestId: string | null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.requestId = requestId
  }
}

function normalizeDetail(detail: unknown): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'object' && item && 'msg' in item) {
          return String(item.msg)
        }
        return String(item)
      })
      .join('. ')
  }
  return 'Não foi possível concluir a operação.'
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
): Promise<T> {
  const headers = new Headers(options.headers)
  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, { ...options, headers })
  } catch {
    throw new ApiError('Não foi possível conectar à API.', 0, null)
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new ApiError(
      normalizeDetail(payload?.detail),
      response.status,
      response.headers.get('X-Request-ID'),
    )
  }

  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export async function apiDownload(
  path: string,
  token?: string | null,
): Promise<{ blob: Blob; filename: string }> {
  const headers = new Headers()
  if (token) headers.set('Authorization', `Bearer ${token}`)

  let response: Response
  try {
    response = await fetch(`${API_URL}${path}`, { headers })
  } catch {
    throw new ApiError('Não foi possível conectar à API.', 0, null)
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => null)
    throw new ApiError(
      normalizeDetail(payload?.detail),
      response.status,
      response.headers.get('X-Request-ID'),
    )
  }

  const disposition = response.headers.get('Content-Disposition') || ''
  const filename =
    disposition.match(/filename="?([^"]+)"?/)?.[1] || 'export.csv'
  return { blob: await response.blob(), filename }
}
