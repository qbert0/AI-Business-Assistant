import type { FetchOptions } from 'ofetch'

type ApiFetchMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE' | 'HEAD' | 'OPTIONS'
type ApiFetchOptions = Omit<FetchOptions<'json'>, 'method'> & {
  method?: ApiFetchMethod | Lowercase<ApiFetchMethod>
}

export const useApiFetch = () => {
  const requestFetch = useRequestFetch()

  return <T>(url: string, options: ApiFetchOptions = {}) => {
    const token = getClientAuthToken()
    const headers = new Headers(options?.headers)

    if (token && !headers.has('Authorization')) {
      headers.set('Authorization', `Bearer ${token}`)
    }

    return requestFetch<T>(url, {
      ...options,
      headers
    } as Parameters<typeof requestFetch<T>>[1])
  }
}
