/**
 * Thin fetch wrapper around the FastAPI backend.
 *
 * Why this exists as its own module:
 * - Single place to change the base URL (e.g. when deploying)
 * - Consistent handling of rate limiting (429) and auth (401) so every
 *   component reacts to them the same way instead of each writing its
 *   own try/catch
 */

// Set at build time via VITE_API_BASE_URL (see .env.example / Docker
// setup) so a production build can point at a real backend URL instead
// of always hitting localhost - falls back to localhost:8000 for local
// dev when that env var isn't set.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
const TOKEN_KEY = 'dashboard_token'

export class RateLimitedError extends Error {
  constructor(message) {
    super(message)
    this.name = 'RateLimitedError'
  }
}

export class UnauthorizedError extends Error {
  constructor(message) {
    super(message)
    this.name = 'UnauthorizedError'
  }
}

export function getStoredToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setStoredToken(token) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
  } else {
    localStorage.removeItem(TOKEN_KEY)
  }
}

// AuthContext registers itself here so this module can react to a 401
// (drop the session everywhere at once) without importing React into
// what's otherwise a plain fetch wrapper.
let unauthorizedHandler = null
export function setUnauthorizedHandler(fn) {
  unauthorizedHandler = fn
}

async function request(path, options = {}) {
  const token = getStoredToken()
  const headers = { ...options.headers }
  if (token) headers.Authorization = `Bearer ${token}`

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (response.status === 401) {
    setStoredToken(null)
    unauthorizedHandler?.()
    throw new UnauthorizedError('Session expired - please log in again')
  }

  if (response.status === 429) {
    throw new RateLimitedError('Rate limit exceeded - keeping last known data')
  }

  if (response.status === 404) {
    // Some list endpoints 404 when filters match nothing - treat as empty.
    return null
  }

  if (!response.ok) {
    let detail = ''
    try {
      detail = (await response.json())?.detail ?? ''
    } catch {
      // response wasn't JSON - fall through with no detail
    }
    throw new Error(detail || `Request to ${path} failed with status ${response.status}`)
  }

  return response.json()
}

/** GET, with the stored bearer token attached automatically. */
export function apiGet(path) {
  return request(path)
}

/** POST a JSON body. The one unauthenticated caller is the login page. */
export function apiPost(path, body) {
  return request(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
