export const useAuth = () => {
  // Sử dụng cookie để lưu token đăng nhập (tên cookie là 'auth_token')
  const token = useCookie('auth_token')

  // Hàm xử lý đăng nhập (giả lập)
  const login = () => {
    token.value = 'my-secret-token-123' // Gán token khi đăng nhập thành công
    navigateTo('/dashboard')            // Chuyển hướng vào app
  }

  // Hàm xử lý đăng xuất
  const logout = () => {
    token.value = null                  // Xóa token
    navigateTo('/login')                // Đuổi ra ngoài trang đăng nhập
  }

  return { token, login, logout }
}