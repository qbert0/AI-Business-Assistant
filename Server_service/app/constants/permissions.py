DEFAULT_USER_PERMISSIONS = ["chat_advisory", "read_documents"]

ADMIN_PERMISSIONS = [
    "access_org_settings",
    "chat_advisory",
    "read_documents",
    "view_employees",
    "upload_documents",
    "view_analytics",
    "edit_sensitive_restrictions",
    "delete_chat_sessions",
]

PERMISSION_DESCRIPTIONS = {
    "access_org_settings": "Truy cap cai dat to chuc.",
    "chat_advisory": "Dung chat tu van theo tai lieu noi bo.",
    "read_documents": "Doc danh sach va metadata tai lieu.",
    "view_employees": "Xem danh sach nhan vien.",
    "upload_documents": "Upload va kich hoat pipeline xu ly tai lieu.",
    "view_analytics": "Xem dashboard phan tich to chuc.",
    "edit_sensitive_restrictions": "Sua cau hinh han che noi dung nhay cam.",
    "delete_chat_sessions": "Xoa doan chat.",
}
