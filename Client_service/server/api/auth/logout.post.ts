import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE } from '../../../app/constants/auth'

export default defineEventHandler((event) => {
  deleteCookie(event, AUTH_TOKEN_COOKIE, { path: '/' })
  deleteCookie(event, AUTH_CLIENT_TOKEN_COOKIE, { path: '/' })
  return { ok: true }
})
