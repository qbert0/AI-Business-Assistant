export const useUiState = () => {
  const isAppDrawerOpen = useState<boolean>('ui-app-drawer-open', () => false)

  const openAppDrawer = () => {
    isAppDrawerOpen.value = true
  }

  const closeAppDrawer = () => {
    isAppDrawerOpen.value = false
  }

  const toggleAppDrawer = () => {
    isAppDrawerOpen.value = !isAppDrawerOpen.value
  }

  return {
    isAppDrawerOpen,
    openAppDrawer,
    closeAppDrawer,
    toggleAppDrawer
  }
}
