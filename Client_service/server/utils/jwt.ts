import { createHmac, timingSafeEqual } from 'node:crypto'
import { AUTH_CLIENT_TOKEN_COOKIE, AUTH_TOKEN_COOKIE } from '../../app/constants/auth'

export interface JwtPayload {
  sub: string
  email: string
  role: 'admin' | 'user'
  exp: number
}

const getSecret = () => process.env.JWT_SECRET || 'local-dev-secret-change-me'

const encode = (value: unknown) =>
  Buffer.from(JSON.stringify(value)).toString('base64url')

const sign = (input: string) =>
  createHmac('sha256', getSecret()).update(input).digest('base64url')

export const createJwt = (payload: Omit<JwtPayload, 'exp'>, expiresInSeconds = 60 * 60 * 24 * 7) => {
  const header = encode({ alg: 'HS256', typ: 'JWT' })
  const body = encode({
    ...payload,
    exp: Math.floor(Date.now() / 1000) + expiresInSeconds
  })
  const signature = sign(`${header}.${body}`)

  return `${header}.${body}.${signature}`
}

export const verifyJwt = (token?: string | null): JwtPayload | null => {
  if (!token) {
    return null
  }

  const [header, body, signature] = token.split('.')
  if (!header || !body || !signature) {
    return null
  }

  const expected = sign(`${header}.${body}`)
  const receivedBuffer = Buffer.from(signature)
  const expectedBuffer = Buffer.from(expected)

  if (receivedBuffer.length !== expectedBuffer.length || !timingSafeEqual(receivedBuffer, expectedBuffer)) {
    return null
  }

  const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8')) as JwtPayload
  if (payload.exp < Math.floor(Date.now() / 1000)) {
    return null
  }

  return payload
}

const getBearerToken = (event: Parameters<typeof getHeader>[0]) => {
  const authorization = getHeader(event, 'authorization')

  if (!authorization?.startsWith('Bearer ')) {
    return null
  }

  return authorization.slice('Bearer '.length)
}

export const getAuthPayload = (event: Parameters<typeof getCookie>[0]) =>
  verifyJwt(getCookie(event, AUTH_TOKEN_COOKIE) || getCookie(event, AUTH_CLIENT_TOKEN_COOKIE) || getBearerToken(event))

export const requireAuthPayload = (event: Parameters<typeof getCookie>[0]) => {
  const payload = getAuthPayload(event)

  if (!payload) {
    throw createError({ statusCode: 401, statusMessage: 'Authentication required' })
  }

  return payload
}
