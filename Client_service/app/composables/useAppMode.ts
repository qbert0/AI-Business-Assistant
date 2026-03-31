export const useAppMode = () => {
  // Mặc định là chế độ cá nhân
  const viewMode = useState<'personal' | 'organization'>('viewMode', () => 'personal')

  const toggleMode = () => {
    viewMode.value = viewMode.value === 'personal' ? 'organization' : 'personal'
  }

  return { viewMode, toggleMode }
}