import { z } from 'zod'
import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE, AUTH_TOKEN_MAX_AGE } from '../../../app/constants/auth'
import { createJwt } from '../../utils/jwt'
import { findUserByEmail, stripPassword } from '../../utils/mockData'

const loginSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
})

export default defineEventHandler(async (event) => {
  const body = loginSchema.parse(await readBody(event))
  const user = findUserByEmail(body.email)

  if (!user || user.password !== body.password) {
    throw createError({ statusCode: 401, statusMessage: 'Invalid email or password' })
  }

  const token = createJwt({ sub: user.id, email: user.email, role: user.role })

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

  return {
    token,
    tokenType: 'Bearer',
    user: stripPassword(user)
  }
})
