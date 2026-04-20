import type { FetchOptions } from 'ofetch'

export const useApiFetch = () => {
  const requestFetch = useRequestFetch()

  return <T>(url: string, options: FetchOptions<'json'> = {}) => {
    const token = getClientAuthToken()
    const headers = new Headers(options?.headers)

    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    return requestFetch<T>(url, {
      ...options,
      headers
    })
  }
}
