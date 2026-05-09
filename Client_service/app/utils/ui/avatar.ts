const avatarPaletteClasses = [
  'avatar-tone-terracotta',
  'avatar-tone-teal',
  'avatar-tone-bronze',
  'avatar-tone-green',
  'avatar-tone-plum',
  'avatar-tone-clay'
]

const getAvatarSeed = (name: string) => name.split('').reduce((sum, char) => sum + char.charCodeAt(0), 0)

export const createInitials = (name: string) =>
  name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
    .join('')

export const getAvatarToneClass = (name: string) => avatarPaletteClasses[getAvatarSeed(name) % avatarPaletteClasses.length]
