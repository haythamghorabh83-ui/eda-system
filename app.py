import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. إعدادات الصفحة والأيقونة (Favicon)
st.set_page_config(
    page_title="EDA Mobile System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. جلب الروابط من Secrets مع خطة بديلة (Fallback) في حال عدم وجودها
try:
    LINK_INSPECTORS = st.secrets["LINK_INSPECTORS"]
    LINK_ACHIEVEMENTS = st.secrets["LINK_ACHIEVEMENTS"]
except Exception:
    # الروابط التي زودتني بها (تستخدم في حال فشل السيكرتس)
    LINK_INSPECTORS = "https://docs.google.com/spreadsheets/d/1wfIdnwszEI0_EURhyH-LcFLfwXhJSO15/edit"
    LINK_ACHIEVEMENTS = "https://docs.google.com/spreadsheets/d/1cgXGh4hp54XNZY7JbgS7ZjiLjPmYeOFz/edit"

# روابط القراءة السريعة (لحل مشكلة 404)
READ_LINK_INS = LINK_INSPECTORS.replace('/edit', '/export?format=csv')
READ_LINK_ACH = LINK_ACHIEVEMENTS.replace('/edit', '/export?format=csv')

# 3. تنسيق الواجهة (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .main-title { font-size: 32px; color: #1a4a7a; text-align: center; font-weight: bold; margin-top: -50px; }
    .sub-title { font-size: 18px; color: #d4a017; text-align: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 12px; height: 3.5em; font-weight: bold; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# عرض الشعار في المنتصف
col_l, col_m, col_r = st.columns([1, 1, 1])
with col_m:
    st.image("https://www.edaegypt.gov.eg/media/1001/logo.png", use_container_width=True)

st.markdown('<p class="main-title">هيئة الدواء المصرية</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">نظام الإدارة الميدانية الذكي</p>', unsafe_allow_html=True)

# 4. الاتصال بقواعد البيانات
conn = st.connection("gsheets", type=GSheetsConnection)

# 5. نظام الدخول
if 'auth' not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.header("🔐 تسجيل الدخول")
    pwd = st.text_input("كلمة المرور", type="password", key="pwd_input")
    if st.button("دخول", key="login_btn"):
        if pwd == "EDA2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("الكلمة غير صحيحة")
    if st.session_state.auth:
        if st.button("تسجيل خروج", key="logout_btn"):
            st.session_state.auth = False
            st.rerun()

# 6. التبويبات لعرض البيانات
tab1, tab2 = st.tabs(["👥 المفتشين", "📊 الإنجازات"])

with tab1:
    try:
        df_ins = pd.read_csv(READ_LINK_INS)
        st.dataframe(df_ins, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"خطأ في تحميل جدول المفتشين: {e}")

with tab2:
    try:
        df_ach = pd.read_csv(READ_LINK_ACH)
        st.dataframe(df_ach, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"خطأ في تحميل جدول الإنجازات: {e}")

# 7. لوحة التحكم (للمسؤول فقط)
if st.session_state.auth:
    st.divider()
    st.markdown("### 🛠️ لوحة التحكم السحابي")
    
    target = st.radio("اختر الجدول للتعديل:", ["المفتشين", "الإنجازات"], horizontal=True, key="tbl_radio")
    active_url = LINK_INSPECTORS if target == "المفتشين" else LINK_ACHIEVEMENTS
    active_read = READ_LINK_INS if target == "المفتشين" else READ_LINK_ACH

    try:
        df_active = pd.read_csv(active_read)
        
        c1, c2, c3 = st.columns(3)
        if c1.button("➕ إضافة", key="add_nav"): st.session_state.mode = "add"
        if c2.button("📝 تعديل", key="edit_nav"): st.session_state.mode = "edit"
        if c3.button("🗑️ حذف", key="del_nav"): st.session_state.mode = "delete"

        # نموذج الإضافة
        if st.session_state.get('mode') == "add":
            with st.form("form_add"):
                st.info(f"إضافة سجل إلى {target}")
                new_data = {}
                cols = st.columns(2)
                for i, col_name in enumerate(df_active.columns):
                    with cols[i % 2]:
                        new_data[col_name] = st.text_input(col_name, key=f"in_add_{i}")
                if st.form_submit_button("حفظ"):
                    updated = pd.concat([df_active, pd.DataFrame([new_data])], ignore_index=True)
                    conn.update(spreadsheet=active_url, data=updated)
                    st.success("تم الحفظ!")
                    st.rerun()

        # نموذج التعديل
        elif st.session_state.get('mode') == "edit":
            row_idx = st.selectbox("رقم السجل:", df_active.index, key="sel_edit")
            with st.form("form_edit"):
                up_data = {}
                cols = st.columns(2)
                for i, col_name in enumerate(df_active.columns):
                    with cols[i % 2]:
                        up_data[col_name] = st.text_input(f"تعديل {col_name}", value=str(df_active.at[row_idx, col_name]), key=f"in_ed_{i}")
                if st.form_submit_button("تحديث"):
                    for c in df_active.columns: df_active.at[row_idx, c] = up_data[c]
                    conn.update(spreadsheet=active_url, data=df_active)
                    st.success("تم التحديث!")
                    st.rerun()

        # نموذج الحذف
        elif st.session_state.get('mode') == "delete":
            row_del = st.selectbox("رقم السجل للحذف:", df_active.index, key="sel_del")
            if st.button("تأكيد الحذف النهائي", key="btn_confirm_del"):
                df_active = df_active.drop(row_del)
                conn.update(spreadsheet=active_url, data=df_active)
                st.success("تم الحذف!")
                st.rerun()

    except Exception as e:
        st.error(f"تأكد من صلاحيات الـ Editor للرابط: {e}")
else:
    st.info("💡 سجل دخولك من القائمة الجانبية لإدارة البيانات.")