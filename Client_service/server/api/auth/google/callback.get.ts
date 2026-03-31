export default defineEventHandler(async (event) => {
  // 1. Lấy mã 'code' từ URL do Google trả về
  const query = getQuery(event)
  const code = query.code

  if (!code) {
    throw createError({ statusCode: 400, statusMessage: 'Thiếu mã xác thực từ Google' })
  }

  try {
    // 2. Gọi API của Google để đổi 'code' lấy 'access_token'
    const tokenResponse = await $fetch<any>('https://oauth2.googleapis.com/token', {
      method: 'POST',
      body: {
        client_id: process.env.GOOGLE_CLIENT_ID,
        client_secret: process.env.GOOGLE_CLIENT_SECRET,
        redirect_uri: process.env.GOOGLE_REDIRECT_URI,
        grant_type: 'authorization_code',
        code: code
      }
    })

    const accessToken = tokenResponse.access_token

    // 3. Dùng access_token để lấy thông tin cá nhân (email, tên, avatar)
    const userInfo = await $fetch<any>('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        Authorization: `Bearer ${accessToken}`
      }
    })

    // --- Ở BƯỚC NÀY ---
    // Trong thực tế: Bạn sẽ lưu userInfo.email vào Database của bạn, tạo một user mới nếu chưa có.
    console.log('Thông tin người dùng:', userInfo)

    // 4. Tạo phiên đăng nhập cho ứng dụng của bạn (Set Cookie)
    // Giống như file composables/useAuth.ts chúng ta làm trước đó
    setCookie(event, 'auth_token', 'my-secret-token-' + userInfo.id, {
      httpOnly: false,
      maxAge: 60 * 60 * 24 * 7 // Sống trong 7 ngày
    })

    // 5. Đăng nhập thành công, đá người dùng về trang Dashboard
    return sendRedirect(event, '/dashboard')

  } catch (error) {
    console.error('Lỗi xác thực Google:', error)
    return sendRedirect(event, '/login?error=auth_failed')
  }
})