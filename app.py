import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. إعدادات الصفحة والهوية البصرية
st.set_page_config(page_title="EDA Mobile System", layout="wide", initial_sidebar_state="collapsed")

# روابط الجداول (تم تحويلها لصيغة التصدير البرمجي لضمان الاتصال)
LINK_INSPECTORS = "https://docs.google.com/spreadsheets/d/1wfIdnwszEI0_EURhyH-LcFLfwXhJSO15/export?format=csv&gid=919550898"
LINK_ACHIEVEMENTS = "https://docs.google.com/spreadsheets/d/1cgXGh4hp54XNZY7JbgS7ZjiLjPmYeOFz/export?format=csv&gid=250291105"

# رابط التعديل الأصلي (لأغراض المزامنة عبر GSheetsConnection)
URL_INSPECTORS_EDIT = "https://docs.google.com/spreadsheets/d/1wfIdnwszEI0_EURhyH-LcFLfwXhJSO15/edit#gid=919550898"
URL_ACHIEVEMENTS_EDIT = "https://docs.google.com/spreadsheets/d/1cgXGh4hp54XNZY7JbgS7ZjiLjPmYeOFz/edit#gid=250291105"

# تنسيق الواجهة (CSS)
st.markdown("""
    <style>
    .stApp { background-color: #fcfcfc; }
    .main-title { font-size: 32px; color: #1a4a7a; text-align: center; font-weight: bold; margin-bottom: 0px; }
    .sub-title { font-size: 18px; color: #d4a017; text-align: center; margin-bottom: 30px; }
    .stButton>button { width: 100%; border-radius: 15px; height: 3.8em; font-weight: bold; border: 1px solid #1a4a7a; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; justify-content: center; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 10px 10px 0 0; padding: 0 20px; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="main-title">🛡️ هيئة الدواء المصرية</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">نظام الإدارة الميدانية - وحدة الدعم الفني</p>', unsafe_allow_html=True)

# 2. إنشاء الاتصال السحابي
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. نظام الصلاحيات
if 'auth' not in st.session_state: st.session_state.auth = False

with st.sidebar:
    st.image("https://www.edaegypt.gov.eg/media/1001/logo.png", width=100) # شعار افتراضي
    st.header("🔐 الدخول")
    pwd = st.text_input("كلمة مرور المسؤول", type="password", key="login_field")
    if st.button("تسجيل الدخول", key="login_btn"):
        if pwd == "EDA2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("❌ الكلمة غير صحيحة")

    if st.session_state.auth:
        if st.button("🔴 تسجيل الخروج", key="logout_btn"):
            st.session_state.auth = False
            st.rerun()

# 4. التبويبات لعرض البيانات
tab1, tab2 = st.tabs(["👥 جدول المفتشين", "📊 جدول الإنجازات"])

with tab1:
    try:
        df_ins = pd.read_csv(LINK_INSPECTORS)
        st.dataframe(df_ins, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال برابط المفتشين: {e}")

with tab2:
    try:
        df_ach = pd.read_csv(LINK_ACHIEVEMENTS)
        st.dataframe(df_ach, use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"⚠️ فشل الاتصال برابط الإنجازات: {e}")

# 5. لوحة الأيقونات (إضافة - تعديل - حذف)
if st.session_state.auth:
    st.divider()
    st.markdown("### 🛠️ لوحة التحكم في البيانات (سحابي)")
    
    target_table = st.radio("اختر الجدول المطلوب:", ["المفتشين", "الإنجازات"], horizontal=True, key="tbl_selector")
    active_edit_url = URL_INSPECTORS_EDIT if target_table == "المفتشين" else URL_ACHIEVEMENTS_EDIT
    
    # قراءة البيانات الحالية للعملية
    try:
        # نقرأ البيانات بصيغة CSV للسرعة في العرض داخل النماذج
        current_csv_link = LINK_INSPECTORS if target_table == "المفتشين" else LINK_ACHIEVEMENTS
        df_active = pd.read_csv(current_csv_link)
        
        col1, col2, col3 = st.columns(3)
        
        if col1.button("➕ إضافة جديد", key="add_nav"): st.session_state.op = "add"
        if col2.button("📝 تعديل سجل", key="edit_nav"): st.session_state.op = "edit"
        if col3.button("🗑️ حذف سجل", key="del_nav"): st.session_state.op = "delete"

        # --- نموذج الإضافة ---
        if st.session_state.get('op') == "add":
            with st.form("add_form", clear_on_submit=True):
                st.info(f"إضافة بيانات إلى: {target_table}")
                new_row = {}
                f_cols = st.columns(2)
                for i, column in enumerate(df_active.columns):
                    with f_cols[i % 2]:
                        new_row[column] = st.text_input(column, key=f"add_inp_{i}")
                
                if st.form_submit_button("🚀 حفظ ومزامنة"):
                    updated_df = pd.concat([df_active, pd.DataFrame([new_row])], ignore_index=True)
                    conn.update(spreadsheet=active_edit_url, data=updated_df)
                    st.success("✅ تمت الإضافة بنجاح في جوجل شيت!")
                    st.rerun()

        # --- نموذج التعديل ---
        elif st.session_state.get('op') == "edit":
            row_idx = st.selectbox("اختر رقم السجل للتعديل:", df_active.index, key="edit_idx_sel")
            with st.form("edit_form"):
                updated_row = {}
                e_cols = st.columns(2)
                for i, column in enumerate(df_active.columns):
                    with e_cols[i % 2]:
                        updated_row[column] = st.text_input(f"تعديل {column}", value=str(df_active.at[row_idx, column]), key=f"edit_inp_{i}")
                
                if st.form_submit_button("🔄 تحديث"):
                    for col in df_active.columns:
                        df_active.at[row_idx, col] = updated_row[col]
                    conn.update(spreadsheet=active_edit_url, data=df_active)
                    st.success("✅ تم التحديث بنجاح!")
                    st.rerun()

        # --- نموذج الحذف ---
        elif st.session_state.get('op') == "delete":
            del_idx = st.selectbox("اختر رقم السجل للحذف:", df_active.index, key="del_idx_sel")
            st.warning(f"⚠️ هل أنت متأكد من حذف السجل رقم {del_idx} من {target_table}؟")
            if st.button("🗑️ تأكيد الحذف النهائي", key="final_del_btn"):
                df_active = df_active.drop(del_idx)
                conn.update(spreadsheet=active_edit_url, data=df_active)
                st.success("✅ تم حذف السجل ومزامنة السحابة!")
                st.rerun()

    except Exception as e:
        st.error(f"تأكد من صلاحيات الـ Editor للرابط: {e}")

else:
    st.info("💡 لمشاهدة أدوات الإضافة والتعديل، يرجى تسجيل الدخول من القائمة الجانبية.")