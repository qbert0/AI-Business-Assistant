import {
  organizeSettingsSchema,
  passwordSettingsSchema,
  paymentSettingsSchema,
  profileSettingsSchema,
  type OrganizeSettingsInput,
  type PasswordSettingsInput,
  type PaymentSettingsInput,
  type ProfileSettingsInput
} from '@/schemas/settings'

const firstIssue = (issues: Array<{ message: string }>) => issues[0]?.message ?? 'Invalid input'

export const useSettingsForms = () => {
  const profileErrors = ref<string | null>(null)
  const passwordErrors = ref<string | null>(null)
  const paymentErrors = ref<string | null>(null)
  const organizeErrors = ref<string | null>(null)

  const validateProfile = (payload: ProfileSettingsInput) => {
    const result = profileSettingsSchema.safeParse(payload)
    profileErrors.value = result.success ? null : firstIssue(result.error.issues)
    return result.success
  }

  const validatePassword = (payload: PasswordSettingsInput) => {
    const result = passwordSettingsSchema.safeParse(payload)
    passwordErrors.value = result.success ? null : firstIssue(result.error.issues)
    return result.success
  }

  const validatePayment = (payload: PaymentSettingsInput) => {
    const result = paymentSettingsSchema.safeParse(payload)
    paymentErrors.value = result.success ? null : firstIssue(result.error.issues)
    return result.success
  }

  const validateOrganize = (payload: OrganizeSettingsInput) => {
    const result = organizeSettingsSchema.safeParse(payload)
    organizeErrors.value = result.success ? null : firstIssue(result.error.issues)
    return result.success
  }

  return {
    profileErrors,
    passwordErrors,
    paymentErrors,
    organizeErrors,
    validateProfile,
    validatePassword,
    validatePayment,
    validateOrganize
  }
}
