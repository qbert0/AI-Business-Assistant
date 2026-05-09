import { z } from 'zod'

export const organizationCreateSchema = z.object({
  name: z.string().min(2).max(80),
  industry: z.string().min(2).max(80),
  description: z.string().min(8).max(500)
})

export const employeeCreateSchema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
  department: z.string().min(2),
  title: z.string().min(2),
  role: z.string().min(2),
  permissions: z.array(z.string())
})
