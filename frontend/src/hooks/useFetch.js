import { useState, useEffect, useRef, useCallback } from 'react'
import { RateLimitedError } from '../api/client'

/**
 * Fetches on mount and again whenever `deps` changes - no interval,
 * no auto-refresh. This is mock data that only changes when someone
 * reseeds the database, so polling on a timer had nothing real to pick
 * up; it just added an unused "auto-refresh" control to the UI. Filter/
 * date changes still refetch immediately via the deps array.
 *
 * Exposes { data, error, loading, lastUpdated, rateLimited, refresh }.
 *
 * Design choice: on a 429 (RateLimitedError), the previous `data` is
 * kept as-is and `rateLimited` is set true for a moment instead of
 * clearing the panel to empty.
 *
 * @param {() => Promise<any>} fetchFn - function that returns the data
 * @param {Array} deps - dependency array (e.g. filter values) that
 *   triggers a fresh fetch when changed
 */
export function useFetch(fetchFn, deps = []) {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(null)
  const [rateLimited, setRateLimited] = useState(false)

  // fetchFn changes identity every render (it closes over deps), so we
  // keep the latest version in a ref rather than re-binding on every call.
  const fetchFnRef = useRef(fetchFn)
  fetchFnRef.current = fetchFn

  const runFetch = useCallback(async () => {
    try {
      const result = await fetchFnRef.current()
      setData(result)
      setError(null)
      setRateLimited(false)
      setLastUpdated(new Date())
    } catch (err) {
      if (err instanceof RateLimitedError) {
        setRateLimited(true)
        // Keep existing data - do not clear it.
      } else {
        setError(err.message)
      }
    } finally {
      setLoading(false)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    setLoading(true)
    runFetch()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)

  return { data, error, loading, lastUpdated, rateLimited, refresh: runFetch }
}
