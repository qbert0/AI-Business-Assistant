export default defineNuxtRouteMiddleware((to, from) => {
  // Lấy token từ cookie
  const token = useCookie('auth_token')

  // Khai báo những trang ai cũng vào được (Public routes)
  const publicRoutes = ['/login', '/register']

  // TRƯỜNG HỢP 1: Chưa đăng nhập (không có token)
  if (!token.value) {
    // Nếu cố tình vào các trang KHÔNG nằm trong publicRoutes
    if (!publicRoutes.includes(to.path)) {
      return navigateTo('/login') // Bắt quay xe về trang đăng nhập
    }
  }

  // TRƯỜNG HỢP 2: Đã đăng nhập (có token)
  if (token.value) {
    // Nếu lại cố tình truy cập vào trang login hoặc register
    if (publicRoutes.includes(to.path)) {
      return navigateTo('/dashboard') // Đẩy thẳng vào dashboard, không cho log in lại
    }
  }
})