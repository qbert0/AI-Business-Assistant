import { createJwt } from '../../../utils/jwt'
import { findUserByEmail, stripPassword } from '../../../utils/mockData'

const AUTH_REDIRECT_QUERY = 'redirect'
const DEFAULT_AUTH_REDIRECT = '/dashboard'

export default defineEventHandler((event) => {
  const user = findUserByEmail('chau@example.com')
  const query = getQuery(event)
  const redirectQuery = query[AUTH_REDIRECT_QUERY]
  const redirect = Array.isArray(redirectQuery) ? redirectQuery[0] : redirectQuery

  if (!user) {
    throw createError({ statusCode: 500, statusMessage: 'Demo user not found' })
  }

  const token = createJwt({ sub: user.id, email: user.email, role: user.role })

  setCookie(event, 'auth_token', token, {
    httpOnly: true,
    sameSite: 'lax',
    secure: process.env.NODE_ENV === 'production',
    path: '/',
    maxAge: 60 * 60 * 24 * 7
  })

  const redirectTarget =
    typeof redirect === 'string' && redirect.startsWith('/') && !redirect.startsWith('//') && !redirect.startsWith('/\\')
      ? redirect
      : DEFAULT_AUTH_REDIRECT

  return sendRedirect(event, redirectTarget)
})
