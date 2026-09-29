// Same-origin API client. The browser only ever talks to /api/* on this app;
// it never sees Databricks hosts, tokens, or resource identifiers.

export type ApiErrorCode =
  | 'WAREHOUSE_UNAVAILABLE'
  | 'SEARCH_UNAVAILABLE'
  | 'MODEL_UNAVAILABLE'
  | 'UPSTREAM_TIMEOUT'
  | 'UNKNOWN_ASSET'
  | 'INVALID_REQUEST'
  | 'SERVICE_NOT_CONFIGURED'
  | 'NOT_FOUND'
  | 'NETWORK'
  | 'INTERNAL_ERROR'

export class ApiError extends Error {
  readonly code: ApiErrorCode
  readonly status: number

  constructor(code: ApiErrorCode, message: string, status: number) {
    super(message)
    this.code = code
    this.status = status
  }

  get retryable(): boolean {
    return ['WAREHOUSE_UNAVAILABLE', 'SEARCH_UNAVAILABLE', 'MODEL_UNAVAILABLE', 'UPSTREAM_TIMEOUT', 'NETWORK'].includes(
      this.code,
    )
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response
  try {
    res = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    })
  } catch {
    throw new ApiError('NETWORK', 'Could not reach the application server. Check your connection and retry.', 0)
  }
  const body = await res.json().catch(() => null)
  if (!res.ok) {
    const err = body?.error
    throw new ApiError(
      (err?.code as ApiErrorCode) ?? 'INTERNAL_ERROR',
      typeof err?.message === 'string' ? err.message : 'Something went wrong. Please try again.',
      res.status,
    )
  }
  return body as T
}

export const api = {
  get: <T,>(path: string) => request<T>(path),
  post: <T,>(path: string, payload: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(payload) }),
}
