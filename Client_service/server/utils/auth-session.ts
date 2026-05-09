import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE, AUTH_TOKEN_MAX_AGE } from '../../app/constants/auth'

export const setAuthCookies = (event: Parameters<typeof setCookie>[0], token: string) => {
  setCookie(event, AUTH_TOKEN_COOKIE, token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: AUTH_TOKEN_MAX_AGE
  })

  setCookie(event, AUTH_CLIENT_TOKEN_COOKIE, token, {
    httpOnly: false,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: AUTH_TOKEN_MAX_AGE
  })
}
