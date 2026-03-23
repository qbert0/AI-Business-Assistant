import streamlit as st

# 1. CẤU HÌNH TRANG (Bắt buộc phải nằm ở dòng đầu tiên gọi lệnh st)
st.set_page_config(
    page_title="My App Dashboard",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# PHẦN 1: ĐỊNH NGHĨA CÁC TRANG (CONTENT)
# ==========================================
def page_home():
    st.title("🏠 Trang chủ")
    st.info("Đây là phần Content của Trang chủ. Nội dung thay đổi dựa theo menu bên trái.")
    st.write("Chào mừng bạn đến với hệ thống. Hãy chọn các tính năng ở thanh điều hướng.")

def page_profile():
    st.title("👤 Hồ sơ người dùng")
    st.write("Nội dung trang hồ sơ...")

def page_settings():
    st.title("⚙️ Cài đặt hệ thống")
    st.write("Nội dung trang cài đặt...")

# Khởi tạo các đối tượng Page của Streamlit
p_home = st.Page(page_home, title="Trang chủ", icon="🏠", default=True)
p_profile = st.Page(page_profile, title="Hồ sơ", icon="👤")
p_settings = st.Page(page_settings, title="Cài đặt", icon="⚙️")

# Gom nhóm Menu cho Sidebar
nav_structure = {
    "Chung": [p_home],
    "Cá nhân": [p_profile, p_settings]
}
pg = st.navigation(nav_structure)

# ==========================================
# PHẦN 2: CÁC COMPONENTS (HEADER, SIDEBAR, FOOTER)
# ==========================================

def render_header():
    """Tạo Header chứa Logo và Nút Đăng nhập/Đăng xuất"""
    # Chia làm 3 cột: Logo bên trái, khoảng trống ở giữa, Nút đăng nhập bên phải
    col_logo, col_space, col_login = st.columns([1, 5, 1])
    
    with col_logo:
        # Thay link bằng logo thật của bạn
        st.image("https://img.icons8.com/color/96/000000/python.png", width=50)
        
    with col_login:
        # Xử lý logic đăng nhập ảo bằng session_state
        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False

        if st.session_state.logged_in:
            st.write("👋 Chào, Admin!")
            if st.button("Đăng xuất", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun() # Tải lại trang để cập nhật UI
        else:
            if st.button("🔐 Đăng nhập", use_container_width=True, type="primary"):
                st.session_state.logged_in = True
                st.rerun()
                
    st.divider() # Đường kẻ ngang phân tách Header và Content

def render_sidebar():
    """Thiết lập Sidebar"""
    # Logo hiển thị ở trên cùng của Menu (Tính năng của Streamlit mới)
    st.logo(
        "https://img.icons8.com/color/96/000000/python.png",
        link="https://google.com"
    )
    
    with st.sidebar:
        st.caption("🚀 My App Version 1.0.0")
        st.divider()
        # Lưu ý: Menu điều hướng (Navigation) sẽ tự động được pg.run() render vào đây, 
        # bạn không cần code tay vẽ menu.

def render_footer():
    """Tạo Footer cố định ở cuối trang"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: grey; font-size: 0.9em; padding: 10px;'>
            © 2024 My App | Xây dựng bằng Python & Streamlit
        </div>
        """, 
        unsafe_allow_html=True
    )

# ==========================================
# PHẦN 3: RÁP NỐI VÀ CHẠY ỨNG DỤNG (MAIN)
# ==========================================
def main():
    # 1. Render Sidebar
    render_sidebar()
    
    # 2. Render Header
    render_header()
    
    # 3. Render Content (Nội dung thay đổi linh hoạt theo URL/Menu)
    pg.run()
    
    # 4. Render Footer
    render_footer()

if __name__ == "__main__":
    main()