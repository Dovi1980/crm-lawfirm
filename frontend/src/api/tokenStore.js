/**
 * In-memory access token store.
 *
 * The access token is kept in a module variable (memory only), NOT in
 * localStorage — so an XSS can't trivially exfiltrate a persisted session.
 * It's lost on full page reload, which is fine: on load the app does a silent
 * refresh using the HttpOnly refresh cookie to get a fresh access token.
 */
let _accessToken = null

export function getAccessToken() {
  return _accessToken
}

export function setAccessToken(token) {
  _accessToken = token || null
}

export function clearAccessToken() {
  _accessToken = null
}
