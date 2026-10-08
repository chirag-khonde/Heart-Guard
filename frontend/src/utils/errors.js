/**
 * Safely extracts a displayable error string from an API error response.
 * Prevents React child rendering errors when FastAPI returns validation errors
 * (422 Unprocessable Content) where detail is an array of error objects.
 *
 * @param {any} err - The error caught from an API call
 * @param {string} fallback - Default message if no message is extracted
 * @returns {string} Safe string message to display in UI
 */
export function formatApiError(err, fallback = 'An unexpected error occurred') {
  if (!err) return fallback

  const detail = err.response?.data?.detail
  if (typeof detail === 'string') {
    return detail
  }

  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object') {
          return item.msg || item.message || JSON.stringify(item)
        }
        return String(item)
      })
      .filter(Boolean)
      .join('; ')
  }

  if (detail && typeof detail === 'object') {
    return detail.msg || detail.message || JSON.stringify(detail)
  }

  if (err.response?.data?.message && typeof err.response.data.message === 'string') {
    return err.response.data.message
  }

  if (err.message && typeof err.message === 'string') {
    return err.message
  }

  return fallback
}
