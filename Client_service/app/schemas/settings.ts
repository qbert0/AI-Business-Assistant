import { z } from 'zod'

export const profileSettingsSchema = z.object({
  displayName: z.string().min(2).max(80),
  headline: z.string().min(2).max(120),
  bio: z.string().max(500).optional(),
  showEmail: z.boolean(),
  showOrganizations: z.boolean(),
  allowInvites: z.boolean()
})

export const passwordSettingsSchema = z.object({
  currentPassword: z.string().min(8),
  newPassword: z.string().min(8)
})

export const paymentSettingsSchema = z.object({
  plan: z.enum(['personal-trial', 'business']),
  cardLabel: z.string().min(4).max(80)
})

export const organizeSettingsSchema = z.object({
  defaultWorkspace: z.string().min(1)
})

export type ProfileSettingsInput = z.infer<typeof profileSettingsSchema>
export type PasswordSettingsInput = z.infer<typeof passwordSettingsSchema>
export type PaymentSettingsInput = z.infer<typeof paymentSettingsSchema>
export type OrganizeSettingsInput = z.infer<typeof organizeSettingsSchema>
