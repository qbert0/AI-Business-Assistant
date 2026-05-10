declare const process: {
  env: Record<string, string | undefined>
}

declare const Buffer: {
  from(value: string | ArrayBuffer | ArrayBufferView, encoding?: string): {
    length: number
    toString(encoding?: string): string
  }
}

declare module 'node:crypto' {
  export const randomUUID: () => string
  export const timingSafeEqual: (a: { length: number }, b: { length: number }) => boolean
  export const createHmac: (
    algorithm: string,
    key: string
  ) => {
    update: (input: string) => {
      digest: (encoding: string) => string
    }
  }
}
