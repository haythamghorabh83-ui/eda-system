import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. إعدادات الصفحة والأيقونة (تم تحديث الأيقونة لتظهر في تبويب المتصفح)
st.set_page_config(
    page_title="EDA Mobile System",
    page_icon="🛡️", # يمكنك استبدالها برابط مباشر للصورة إذا توفر رابط دائم ينتهي بـ .png
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. جلب الروابط من Secrets مع خطة بديلة (Fallback)
try:
    LINK_INSPECTORS = st.secrets["LINK_INSPECTORS"]
    LINK_ACHIEVEMENTS = st.secrets["LINK_ACHIEVEMENTS"]
except Exception:
    # الروابط الافتراضية في حال عدم ضبط Secrets
    LINK_INSPECTORS = "https://docs.google.com/spreadsheets/d/1wfIdnwszEI0_EURhyH-LcFLfwXhJSO15/edit"
    LINK_ACHIEVEMENTS = "https://docs.google.com/spreadsheets/d/1cgXGh4hp54XNZY7JbgS7ZjiLjPmYeOFz/edit"

# تحويل الروابط لصيغة القراءة البرمجية CSV
READ_LINK_INS = LINK_INSPECTORS.replace('/edit', '/export?format=csv')
READ_LINK_ACH = LINK_ACHIEVEMENTS.replace('/edit', '/export?format=csv')

# 3. تنسيق الواجهة (CSS) لتحسين المظهر على الموبايل
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .main-title { font-size: 28px; color: #1a4a7a; text-align: center; font-weight: bold; margin-top: -30px; }
    .sub-title { font-size: 16px; color: #d4a017; text-align: center; margin-bottom: 20px; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 10px; height: 3.5em; background-color: #1a4a7a; color: white; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# 4. عرض الشعار الجديد (تم استخدام رابط الشعار الرسمي لضمان الظهور)
col_l, col_m, col_r = st.columns([1, 2, 1])
with col_m:
    # تأكد من رفع ملف "الشعار.jpg" إلى GitHub في نفس مجلد app.py
    try:
        st.image("الشعار.jpg", use_container_width=True)
    except:
        # رابط احتياطي في حال عدم وجود الملف محلياً
        st.image("https://www.edaegypt.gov.eg/media/1001/logo.png", use_container_width=True)

st.markdown('<p class="main-title">هيئة الدواء المصرية</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Egyptian Drug Authority</p>', unsafe_allow_html=True)

# 5. الاتصال بقاعدة البيانات
conn = st.connection("gsheets", type=GSheetsConnection)

# 6. نظام تسجيل الدخول في القائمة الجانبية
if 'auth' not in st.session_state:
    st.session_state.auth = False

with st.sidebar:
    st.markdown("### 🔒 منطقة المسؤول")
    pwd = st.text_input("كلمة المرور", type="password")
    if st.button("تسجيل الدخول"):
        if pwd == "EDA2026":
            st.session_state.auth = True
            st.success("تم الدخول بنجاح")
            st.rerun()
        else:
            st.error("كلمة المرور غير صحيحة")
    
    if st.session_state.auth:
        if st.button("تسجيل الخروج"):
            st.session_state.auth = False
            st.rerun()

# 7. عرض البيانات (تبويبات)
tab1, tab2 = st.tabs(["👥 سجل المفتشين", "📊 سجل الإنجازات"])

with tab1:
    try:
        df_ins = pd.read_csv(READ_LINK_INS)
        st.dataframe(df_ins, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")

with tab2:
    try:
        df_ach = pd.read_csv(READ_LINK_ACH)
        st.dataframe(df_ach, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"خطأ في الاتصال: {e}")

# 8. لوحة الإدارة (تظهر فقط بعد تسجيل الدخول)
if st.session_state.auth:
    st.divider()
    st.markdown("### ⚙️ إدارة البيانات")
    
    choice = st.radio("الجدول المراد تعديله:", ["المفتشين", "الإنجازات"], horizontal=True)
    target_url = LINK_INSPECTORS if choice == "المفتشين" else LINK_ACHIEVEMENTS
    target_read = READ_LINK_INS if choice == "المفتشين" else READ_LINK_ACH

    try:
        df_active = pd.read_csv(target_read)
        
        col1, col2, col3 = st.columns(3)
        if col1.button("➕ إضافة"): st.session_state.action = "add"
        if col2.button("📝 تعديل"): st.session_state.action = "edit"
        if col3.button("🗑️ حذف"): st.session_state.action = "delete"

        # العمليات (إضافة/تعديل/حذف)
        if st.session_state.get('action') == "add":
            with st.form("add_form"):
                new_row = {}
                cols = st.columns(2)
                for i, c_name in enumerate(df_active.columns):
                    with cols[i % 2]:
                        new_row[c_name] = st.text_input(c_name)
                if st.form_submit_button("إرسال البيانات"):
                    updated_df = pd.concat([df_active, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(spreadsheet=target_url, data=updated_df)
                    st.success("تمت الإضافة بنجاح!")
                    st.rerun()

        elif st.session_state.get('action') == "edit":
            idx = st.selectbox("اختر السجل للتعديل:", df_active.index)
            with st.form("edit_form"):
                updated_row = {}
                cols = st.columns(2)
                for i, c_name in enumerate(df_active.columns):
                    with cols[i % 2]:
                        updated_row[c_name] = st.text_input(c_name, value=str(df_active.at[idx, c_name]))
                if st.form_submit_button("تحديث"):
                    for c in df_active.columns: df_active.at[idx, c] = updated_row[c]
                    conn.update(spreadsheet=target_url, data=df_active)
                    st.success("تم التحديث!")
                    st.rerun()

        elif st.session_state.get('action') == "delete":
            idx_del = st.selectbox("اختر السجل للحذف:", df_active.index)
            if st.button("تأكيد الحذف"):
                df_active = df_active.drop(idx_del)
                conn.update(spreadsheet=target_url, data=df_active)
                st.success("تم الحذف!")
                st.rerun()

    except Exception as e:
        st.warning("تأكد من إعطاء صلاحية 'Editor' للرابط في جوجل شيت.")
else:
    st.info("💡 لتعديل البيانات، يرجى تسجيل الدخول من القائمة الجانبية.")