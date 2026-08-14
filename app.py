import streamlit as st
import sqlite3
import pandas as pd
from io import BytesIO
from datetime import datetime
import hashlib

# =========================
# CẤU HÌNH
# =========================
st.set_page_config(
    page_title="Quản lý khách hàng",
    page_icon="📋",
    layout="wide"
)

DB_FILE = "customers.db"

# =========================
# DATABASE
# =========================
def get_connection():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT NOT NULL,
            name TEXT NOT NULL,
            address TEXT,
            note TEXT,
            created_at TEXT
        )
    """)

    conn.commit()
    conn.close()


def add_customer(phone, name, address, note):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers
        (phone, name, address, note, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (
        phone,
        name,
        address,
        note,
        datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ))

    conn.commit()
    conn.close()


def get_customers():
    conn = get_connection()

    df = pd.read_sql_query("""
        SELECT
            id AS "STT",
            phone AS "Số điện thoại",
            name AS "Tên khách hàng",
            address AS "Địa chỉ",
            note AS "Ghi chú",
            created_at AS "Thời gian lưu"
        FROM customers
        ORDER BY id DESC
    """, conn)

    conn.close()
    return df


def delete_customer(customer_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM customers WHERE id = ?",
        (customer_id,)
    )

    conn.commit()
    conn.close()


# =========================
# XUẤT EXCEL
# =========================
def export_excel(df):
    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Khach hang"
        )

    output.seek(0)
    return output


# =========================
# ADMIN LOGIN
# =========================
ADMIN_PASSWORD = "123456"


def check_password(password):
    return password == ADMIN_PASSWORD


# =========================
# KHỞI TẠO
# =========================
init_database()


# =========================
# SIDEBAR
# =========================
st.sidebar.title("📋 QUẢN LÝ KHÁCH HÀNG")

page = st.sidebar.radio(
    "Chọn trang",
    [
        "👤 Nhập thông tin khách hàng",
        "🔐 Admin"
    ]
)


# =====================================================
# TRANG NHẬP KHÁCH HÀNG
# =====================================================
if page == "👤 Nhập thông tin khách hàng":

    st.title("👤 THÔNG TIN KHÁCH HÀNG")
    st.write("Vui lòng điền đầy đủ thông tin bên dưới.")

    st.divider()

    with st.form("customer_form"):

        phone = st.text_input(
            "📱 Số điện thoại *",
            placeholder="Nhập số điện thoại"
        )

        name = st.text_input(
            "👤 Tên khách hàng *",
            placeholder="Nhập họ và tên"
        )

        address = st.text_area(
            "📍 Địa chỉ",
            placeholder="Nhập địa chỉ khách hàng"
        )

        note = st.text_area(
            "📝 Ghi chú",
            placeholder="Nhập ghi chú nếu có"
        )

        submitted = st.form_submit_button(
            "💾 LƯU THÔNG TIN",
            use_container_width=True
        )

        if submitted:

            if not phone.strip():
                st.error("❌ Vui lòng nhập số điện thoại.")

            elif not name.strip():
                st.error("❌ Vui lòng nhập tên khách hàng.")

            else:
                add_customer(
                    phone.strip(),
                    name.strip(),
                    address.strip(),
                    note.strip()
                )

                st.success(
                    "✅ Đã lưu thông tin khách hàng thành công!"
                )

                st.balloons()


# =====================================================
# TRANG ADMIN
# =====================================================
elif page == "🔐 Admin":

    st.title("🔐 ADMIN - QUẢN LÝ KHÁCH HÀNG")

    # -------------------------
    # LOGIN
    # -------------------------
    if "admin_logged_in" not in st.session_state:
        st.session_state.admin_logged_in = False

    if not st.session_state.admin_logged_in:

        st.subheader("Đăng nhập Admin")

        password = st.text_input(
            "Mật khẩu",
            type="password"
        )

        if st.button(
            "🔑 Đăng nhập",
            use_container_width=True
        ):

            if check_password(password):
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("❌ Mật khẩu không đúng.")

    else:

        # -------------------------
        # ADMIN CONTENT
        # -------------------------

        col1, col2 = st.columns([4, 1])

        with col1:
            st.subheader("📊 Danh sách khách hàng")

        with col2:
            if st.button("🚪 Đăng xuất"):
                st.session_state.admin_logged_in = False
                st.rerun()

        df = get_customers()

        # -------------------------
        # THỐNG KÊ
        # -------------------------

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "👥 Tổng khách hàng",
                len(df)
            )

        with col2:
            st.metric(
                "📱 Số điện thoại",
                df["Số điện thoại"].nunique()
                if not df.empty else 0
            )

        with col3:
            st.metric(
                "📅 Hôm nay",
                datetime.now().strftime("%d/%m/%Y")
            )

        st.divider()

        # -------------------------
        # TÌM KIẾM
        # -------------------------

        search = st.text_input(
            "🔎 Tìm kiếm khách hàng",
            placeholder="Nhập tên hoặc số điện thoại..."
        )

        if search:

            df = df[
                df["Tên khách hàng"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
                |
                df["Số điện thoại"]
                .astype(str)
                .str.contains(
                    search,
                    case=False,
                    na=False
                )
            ]

        # -------------------------
        # HIỂN THỊ BẢNG
        # -------------------------

        if df.empty:

            st.info("📭 Chưa có dữ liệu khách hàng.")

        else:

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.write(
                f"Hiển thị **{len(df)}** khách hàng."
            )

            # -------------------------
            # XUẤT EXCEL
            # -------------------------

            excel_file = export_excel(df)

            st.download_button(
                label="📥 XUẤT FILE EXCEL",
                data=excel_file,
                file_name=f"Danh_sach_khach_hang_{datetime.now().strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

            st.divider()

            # -------------------------
            # XÓA KHÁCH HÀNG
            # -------------------------

            st.subheader("🗑️ Xóa khách hàng")

            customer_options = {
                f'{row["Tên khách hàng"]} - {row["Số điện thoại"]}':
                row["STT"]
                for _, row in get_customers().iterrows()
            }

            if customer_options:

                selected_customer = st.selectbox(
                    "Chọn khách hàng muốn xóa",
                    list(customer_options.keys())
                )

                if st.button(
                    "🗑️ XÓA KHÁCH HÀNG",
                    type="secondary"
                ):

                    customer_id = customer_options[
                        selected_customer
                    ]

                    delete_customer(customer_id)

                    st.success(
                        "✅ Đã xóa khách hàng."
                    )

                    st.rerun()
