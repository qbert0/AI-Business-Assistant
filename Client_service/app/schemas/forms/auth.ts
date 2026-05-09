import { z } from 'zod'

export const loginSchema = z.object({
  email: z.string().email('Email is invalid'),
  password: z.string().min(8, 'Password must contain at least 8 characters')
})

export const registerSchema = z.object({
  full_name: z.string().min(2, 'Full name must contain at least 2 characters'),
  email: z.string().email('Email is invalid'),
  password: z.string().min(8, 'Password must contain at least 8 characters')
})

export type LoginInput = z.infer<typeof loginSchema>
export type RegisterInput = z.infer<typeof registerSchema>
