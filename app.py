import streamlit as st
import google.generativeai as genai
import smtplib
import ssl
import datetime
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
from PIL import Image

# --- 1. SETTINGS & AI SETUP ---
st.set_page_config(page_title="COOL FINDS | ADVOCATE ELITE", layout="wide")

# API Configuration
API_KEY = "AIzaSyCplbGXPyL2AVysUQDrY_rHI9JZne6TrAM"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 2. HELPER FUNCTIONS ---

def generate_pdf(content, title="Legal_Document"):
    """Generates PDF and fixes the Unicode Rupee Error"""
    safe_content = content.replace("₹", "Rs.")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12) 
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title.upper(), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 10, txt=safe_content)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

def send_real_email_smtp(sender_mail, app_password, receiver_emails, subject, body):
    """Sends real emails using Gmail SMTP SSL (Port 465)"""
    smtp_server = "smtp.gmail.com"
    port = 465  
    
    message = MIMEMultipart()
    message["From"] = sender_mail
    message["To"] = receiver_emails 
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))
    
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_mail, app_password)
            dest_list = [email.strip() for email in receiver_emails.split(",")]
            server.sendmail(sender_mail, dest_list, message.as_string())
        return True, "Success"
    except Exception as e:
        return False, str(e)

# --- 3. SESSION STATE ---
if 'page' not in st.session_state: st.session_state.page = 1
if 'chat_history' not in st.session_state: st.session_state.chat_history = []
if 'doc_content' not in st.session_state: st.session_state.doc_content = ""
if 'hearings' not in st.session_state: st.session_state.hearings = []

# --- 4. GLOBAL STYLING (Preserving All Fonts and Colors) ---
BG_URL = "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1920"
st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@400;700&display=swap');
    .stApp {{ background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.9)), url('{BG_URL}'); background-size: cover; background-attachment: fixed; }}
    .title-text {{ color: #D4AF37; font-family: 'Playfair Display', serif; font-size: 55px; font-weight: bold; text-align: center; margin-bottom: 0px; }}
    .glass-card {{ background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border: 1px solid #D4AF37; padding: 25px; border-radius: 15px; color: white; }}
    .section-header {{ color: #D4AF37 !important; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: bold; border-bottom: 1px solid #D4AF37; margin-bottom: 15px; }}
    .ai-analysis-text {{ color: #00FFCC !important; font-family: 'Montserrat', sans-serif; font-size: 20px; font-weight: bold; margin-bottom: 10px; }}
    .citation-answer {{ color: #BB86FC !important; background-color: rgba(187, 134, 252, 0.1); border-left: 4px solid #BB86FC; padding: 15px; border-radius: 5px; font-family: 'Montserrat', sans-serif; line-height: 1.6; }}
    label {{ color: #D4AF37 !important; font-family: 'Montserrat'; font-weight: bold; }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(1) p {{ color: #00BFFF !important; font-weight: bold; font-size: 18px; }}
    div[data-testid="stRadio"] div[role="radiogroup"] > label:nth-of-type(2) p {{ color: #FF4B4B !important; font-weight: bold; font-size: 18px; }}
    button[data-baseweb="tab"]:nth-of-type(1) div p {{ color: #D4AF37 !important; font-weight: bold; }}
    button[data-baseweb="tab"]:nth-of-type(2) div p {{ color: #00FFCC !important; font-weight: bold; }}
    button[data-baseweb="tab"]:nth-of-type(3) div p {{ color: #BB86FC !important; font-weight: bold; }}
    button[data-baseweb="tab"]:nth-of-type(4) div p {{ color: #FF9F43 !important; font-weight: bold; }}
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="title-text">COOL FINDS</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#D4AF37; font-family:Montserrat; font-size:0.9rem; letter-spacing: 4px;'>LEGAL INTELLIGENCE HUB</p><hr>", unsafe_allow_html=True)

# --- PAGE 1: LOGIN ---
if st.session_state.page == 1:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p style="color:#D4AF37; font-family:Playfair Display; font-size:28px; text-align:center;">⚖️ Advocate Login</p>', unsafe_allow_html=True)
        with st.form("login"):
            name = st.text_input("Full Name")
            enroll = st.text_input("Bar Enrollment ID")
            if st.form_submit_button("Enter Portal", use_container_width=True):
                if name and enroll:
                    st.session_state.user_name, st.session_state.enroll_id, st.session_state.page = name, enroll, 2
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: DASHBOARD ---
elif st.session_state.page == 2:
    with st.sidebar:
        st.markdown('<p class="section-header">📧 Email Connection</p>', unsafe_allow_html=True)
        s_mail = st.text_input("Your Gmail", placeholder="example@gmail.com")
        s_pass = st.text_input("App Password", type="password", help="16-character code (No spaces)")
        
        if st.button("Verify Connection"):
            if s_mail and s_pass:
                with st.spinner("Testing..."):
                    success, err = send_real_email_smtp(s_mail, s_pass, s_mail, "System Test", "Connection Working!")
                    if success: st.success("✅ Connected to Gmail!")
                    else: st.error(f"❌ Failed: {err}")
            else: st.warning("Enter credentials first")

        st.write("---")
        st.markdown('<p class="section-header">📅 Docket</p>', unsafe_allow_html=True)
        h_case = st.text_input("Case Name")
        h_date = st.date_input("Next Hearing")
        if st.button("Add Hearing"): st.session_state.hearings.append(f"{h_date}: {h_case}")
        for h in st.session_state.hearings[-2:]: st.caption(f"📌 {h}")

    tab1, tab2, tab3, tab4 = st.tabs(["🖋️ Drafting Room", "🔍 Evidence Scanner", "📚 AI Researcher", "💰 Billing"])

    # --- TAB 1: DRAFTING ---
    with tab1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">🖋️ Legal Drafting Room</p>', unsafe_allow_html=True)
        col_draft, col_act = st.columns([2, 1])
        
        with col_draft:
            cat = st.radio("Classification", ["Civil", "Criminal"], horizontal=True)
            opts = ["Property Notice", "Divorce Petition", "Rent Agreement"] if cat == "Civil" else ["Bail Application", "Section 138", "Criminal FIR"]
            sub = st.selectbox("Document Type", opts)
            
            if st.button("✨ Load Template"):
                st.session_state.doc_content = f"Date: {datetime.date.today()}\nAdvocate: {st.session_state.user_name}\nEnrollment: {st.session_state.enroll_id}\n\nSubject: Draft for {sub}\n\n"
            
            draft_area = st.text_area("Live Editor", value=st.session_state.doc_content, height=300)
            st.session_state.doc_content = draft_area

            # WhatsApp Feature
            encoded_draft = urllib.parse.quote(draft_area)
            st.markdown(f'<a href="https://wa.me/?text={encoded_draft}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer;">🟢 Share via WhatsApp</button></a>', unsafe_allow_html=True)

        with col_act:
            st.markdown('<p class="ai-analysis-text">📋 AI Analysis</p>', unsafe_allow_html=True)
            if st.button("Predict Probability", use_container_width=True):
                with st.spinner("Analyzing..."):
                    res = model.generate_content(f"Predict legal success probability for: {draft_area}")
                    st.warning(res.text)
            
            st.write("---")
            dest_mail = st.text_input("Recipient Email")
            pdf_file = generate_pdf(draft_area, title=sub)
            st.download_button("📥 Download PDF", pdf_file, f"{sub}.pdf", use_container_width=True)
            
            if st.button("📧 Send Official Email", type="primary", use_container_width=True):
                if not s_mail or not s_pass:
                    st.error("❌ Sidebar configuration missing!")
                elif not dest_mail:
                    st.error("❌ Recipient email is missing!")
                else:
                    with st.spinner("Sending..."):
                        status, msg = send_real_email_smtp(s_mail, s_pass, dest_mail, f"Legal Notice: {sub}", draft_area)
                        if status: st.success("✅ Sent Successfully!")
                        else: st.error(f"❌ Error: {msg}")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 2: SCANNER ---
    with tab2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p style="color:#00FFCC; font-family:Playfair Display; font-size:24px; font-weight:bold;">🔍 Evidence Scanner (OCR)</p>', unsafe_allow_html=True)
        up_img = st.file_uploader("Upload FIR/Notice Image", type=['jpg', 'png', 'jpeg'])
        if up_img:
            img_obj = Image.open(up_img)
            st.image(img_obj, width=300)
            if st.button("Scan Evidence"):
                with st.spinner("Reading..."):
                    res = model.generate_content(["Extract text and summarize from this legal document image.", img_obj])
                    st.success("Extracted Data:")
                    st.write(res.text)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 3: RESEARCH ---
    with tab3:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p style="color:#BB86FC; font-family:Playfair Display; font-size:24px; font-weight:bold;">📚 AI Case Citation Finder</p>', unsafe_allow_html=True)
        legal_q = st.text_input("Enter Query (e.g., 'Anticipatory bail for murder')")
        if st.button("Find Citations"):
            with st.spinner("Consulting..."):
                res = model.generate_content(f"List 3 relevant Supreme Court citations for: {legal_q}")
                st.markdown(f'<div class="citation-answer">{res.text}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # --- TAB 4: BILLING ---
    with tab4:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p style="color:#FF9F43; font-family:Playfair Display; font-size:24px; font-weight:bold;">💰 Professional Invoicing</p>', unsafe_allow_html=True)
        c_name = st.text_input("Client Name")
        f_amt = st.number_input("Fees (Rs.)", value=0)
        e_amt = st.number_input("Expenses (Rs.)", value=0)
        total_bill = f_amt + e_amt
        invoice_body = f"""OFFICIAL INVOICE\nAdvocate: {st.session_state.user_name}\nClient: {c_name}\nDate: {datetime.date.today()}\n\nProfessional Fee: Rs. {f_amt}\nExpenses: Rs. {e_amt}\nTotal: Rs. {total_bill}"""
        st.code(invoice_body)
        inv_pdf = generate_pdf(invoice_body, title="Invoice")
        st.download_button("📥 Download Invoice", inv_pdf, "Invoice.pdf", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    if st.button("Logout"):
        st.session_state.page = 1
        st.rerun()