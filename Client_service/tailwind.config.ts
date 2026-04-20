import type { Config } from 'tailwindcss'

export default <Partial<Config>>{
  content: [
    './app/**/*.{vue,js,ts}',
    './components/**/*.{vue,js,ts}',
    './server/**/*.{js,ts}',
    './nuxt.config.{js,ts}'
  ],
  theme: {
    extend: {
      colors: {
        parchment: '#ffffff',
        ivory: '#ffffff',
        elevated: '#ffffff',
        warm: '#f5f5f7',
        near: '#1d1d1f',
        charcoal: '#000000',
        olive: 'rgba(0,0,0,0.8)',
        stone: 'rgba(0,0,0,0.48)',
        sand: '#f5f5f7',
        cream: 'rgba(0,0,0,0.08)',
        notion: '#0071e3',
        active: '#0066cc',
        focus: '#0071e3',
        badge: '#fafafc',
        teal: '#2a9d99',
        green: '#1aae39',
        orange: '#dd5b00',
        pink: '#ff64c8',
        purple: '#391c57',
        brown: '#523410',
        terracotta: '#0075de',
        coral: '#005bab',
        crimson: '#dd5b00',
        silver: '#a39e98'
      },
      fontFamily: {
        sans: [
          'Inter',
          'Noto Sans',
          '-apple-system',
          'system-ui',
          'Segoe UI',
          'Helvetica',
          'Arial',
          'sans-serif'
        ],
        serif: [
          'Inter',
          'Noto Sans',
          '-apple-system',
          'system-ui',
          'Segoe UI',
          'Helvetica',
          'Arial',
          'sans-serif'
        ]
      },
      fontSize: {
        micro: ['0.75rem', { lineHeight: '1.33', letterSpacing: '0.125px' }],
        caption: ['0.875rem', { lineHeight: '1.43' }],
        body: ['1rem', { lineHeight: '1.5' }],
        lead: ['1.25rem', { lineHeight: '1.4', letterSpacing: '-0.125px' }],
        title: ['1.375rem', { lineHeight: '1.27', letterSpacing: '-0.25px' }],
        page: ['2rem', { lineHeight: '1.18', letterSpacing: '-0.625px' }],
        hero: ['4rem', { lineHeight: '1', letterSpacing: '-2.125px' }]
      },
      spacing: {
        '4.5': '1.125rem',
        '5.5': '1.375rem',
        '7.5': '1.875rem'
      },
      borderRadius: {
        card: '0.5rem',
        panel: '0.75rem',
        control: '0.5rem'
      },
      boxShadow: {
        ring: 'none',
        whisper: 'none',
        menu: 'rgba(0, 0, 0, 0.22) 3px 5px 30px 0px'
      }
    },
    container: {
      center: true,
      padding: {
        DEFAULT: '1rem',
        md: '1.5rem',
        xl: '2rem'
      }
    }
  },
  plugins: []
}
