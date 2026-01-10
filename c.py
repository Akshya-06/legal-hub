import streamlit as st
import google.generativeai as genai
import smtplib
import ssl
import datetime
import sqlite3
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fpdf import FPDF
from PIL import Image

# --- 1. SETTINGS & SECRETS ---
st.set_page_config(page_title="COOL FINDS | ADVOCATE ELITE", layout="wide")

# Initialize session state variables
if 'auth' not in st.session_state: st.session_state.auth = False
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_name' not in st.session_state: st.session_state.user_name = ""
if 'enroll_id' not in st.session_state: st.session_state.enroll_id = ""
if 'app_pass' not in st.session_state: st.session_state.app_pass = ""
if 'editor' not in st.session_state: st.session_state.editor = "" 

try:
    # Ensure GEMINI_API_KEY is in your .streamlit/secrets.toml
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash') # Updated to current stable version
except Exception as e:
    st.error("Setup Error: Please check your GEMINI_API_KEY in secrets.")
    st.stop()

# --- 2. DATABASE SYSTEM ---
def init_db():
    conn = sqlite3.connect('advocate_elite.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, name TEXT, enroll_id TEXT, app_password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS hearings 
                 (id INTEGER PRIMARY KEY, email TEXT, case_name TEXT, category TEXT, hearing_date TEXT)''')
    conn.commit()
    conn.close()

def make_hashes(password): return hashlib.sha256(str.encode(password)).hexdigest()
def check_hashes(password, hashed_text): return make_hashes(password) == hashed_text

init_db()

# --- 3. HELPER FUNCTIONS ---
def safe_unicode(text):
    replacements = {"₹": "Rs.", "—": "-", "‘": "'", "’": "'", "“": '"', "”": '"', "…": "...", "–": "-"}
    for k, v in replacements.items(): text = text.replace(k, v)
    return text.encode('latin-1', 'replace').decode('latin-1')

def generate_pdf(content, title="Legal_Document"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=title.upper(), ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=11)
    clean_text = safe_unicode(content)
    pdf.multi_cell(0, 10, txt=clean_text)
    output = pdf.output(dest='S')
    return bytes(output) if not isinstance(output, str) else output.encode('latin-1')

def send_text_email(sender_email, sender_password, receiver_input, subject, body_text):
    """Sends email using the logged-in user's SMTP credentials"""
    smtp_server = "smtp.gmail.com"
    port = 465  
    recipient_list = [email.strip() for email in receiver_input.split(",") if email.strip()]
    
    if not sender_password:
        return False, "Gmail App Password missing in your profile."

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = ", ".join(recipient_list)
    message["Subject"] = subject
    message.attach(MIMEText(body_text, "plain"))

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_list, message.as_string())
        return True, "Success"
    except Exception as e: 
        return False, str(e)

# --- 4. STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Montserrat:wght@400;700&display=swap');
    .stApp { background: linear-gradient(rgba(0,0,0,0.9), rgba(0,0,0,0.9)), url('https://images.unsplash.com/photo-1589829545856-d10d557cf95f?q=80&w=1920'); background-size: cover; background-attachment: fixed; }
    .title-text { color: #D4AF37; font-family: 'Playfair Display', serif; font-size: 55px; font-weight: bold; text-align: center; margin-bottom: 0px; }
    .glass-card { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(15px); border: 1px solid #D4AF37; padding: 25px; border-radius: 15px; color: white; margin-bottom: 20px; }
    .section-header { color: #D4AF37 !important; font-family: 'Playfair Display', serif; font-size: 24px; font-weight: bold; border-bottom: 1px solid #D4AF37; margin-bottom: 15px; }
    label { color: #D4AF37 !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<p class="title-text">COOL FINDS</p>', unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#D4AF37; font-family:Montserrat; font-size:0.9rem; letter-spacing: 4px;'>LEGAL INTELLIGENCE HUB</p><hr>", unsafe_allow_html=True)

# --- 5. AUTHENTICATION LOGIC ---
if not st.session_state.auth:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        tab_login, tab_reg = st.tabs(["🔒 Login", "📝 Register"])
        
        with tab_login:
            with st.form("login"):
                email_in = st.text_input("Email")
                pass_in = st.text_input("Password", type="password")
                if st.form_submit_button("Access Portal", use_container_width=True):
                    conn = sqlite3.connect('advocate_elite.db'); c = conn.cursor()
                    c.execute('SELECT password, name, enroll_id, app_password FROM users WHERE email=?', (email_in,))
                    res = c.fetchone(); conn.close()
                    if res and check_hashes(pass_in, res[0]):
                        st.session_state.auth = True
                        st.session_state.user_email = email_in
                        st.session_state.user_name = res[1]
                        st.session_state.enroll_id = res[2]
                        st.session_state.app_pass = res[3]
                        st.rerun()
                    else: st.error("Invalid Email or Password")
        
        with tab_reg:
            st.info("💡 To send emails, generate a 'Gmail App Password' in your Google Security settings.")
            with st.form("register"):
                r_email = st.text_input("Professional Email")
                r_name = st.text_input("Full Name")
                r_bar = st.text_input("Bar Council Enrollment ID")
                r_app_pass = st.text_input("Gmail App Password", type="password")
                r_pass = st.text_input("Portal Password", type="password")
                if st.form_submit_button("Create Account"):
                    if r_email and r_pass:
                        conn = sqlite3.connect('advocate_elite.db'); c = conn.cursor()
                        try:
                            c.execute('INSERT INTO users VALUES (?,?,?,?,?)', 
                                     (r_email, make_hashes(r_pass), r_name, r_bar, r_app_pass))
                            conn.commit(); st.success("Account created! Go to Login.")
                        except: st.error("User already exists with this email.")
                        finally: conn.close()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    # --- MAIN APPLICATION UI ---
    with st.sidebar:
        st.markdown(f'<p style="color:#D4AF37; font-size:20px;">👤 Adv. {st.session_state.user_name}</p>', unsafe_allow_html=True)
        st.write("---")
        h_case, h_date = st.text_input("Case Name"), st.date_input("Hearing Date")
        if st.button("Save to Docket"):
            conn = sqlite3.connect('advocate_elite.db'); c = conn.cursor()
            # Fixed column name from username to email to match init_db
            c.execute('INSERT INTO hearings (email, case_name, category, hearing_date) VALUES (?,?,?,?)', 
                      (st.session_state.user_email, h_case, "General", str(h_date)))
            conn.commit(); conn.close(); st.toast("Saved!")
        if st.button("🚪 Logout"): 
            st.session_state.auth = False
            st.rerun()

    t1, t2, t3, t4 = st.tabs(["🖋️ Drafting Room", "🔍 Evidence OCR", "📚 AI Research", "💰 Billing"])

    with t1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown('<p class="section-header">🖋️ Classified Drafting Room</p>', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        with c1:
            draft_cat = st.radio("Matter Category", ["Civil", "Criminal"], horizontal=True, key="draft_cat")
            if draft_cat == "Civil":
                dtype = st.selectbox("Document Type", ["Property Notice", "Rent Agreement", "Divorce Petition", "Civil Suit"])
                court_header = "IN THE COURT OF THE CIVIL JUDGE, SENIOR DIVISION"
            else:
                dtype = st.selectbox("Document Type", ["Regular Bail Application", "Anticipatory Bail", "Criminal FIR", "Section 138 Notice"])
                court_header = "IN THE COURT OF THE HON'BLE SESSIONS JUDGE"
            
            # --- UPDATED: Professional Template Formatting ---
            if st.button("✨ Load Template"):
                st.session_state.editor = f"""{court_header}
                Date: {datetime.date.today()}
Advocate: {st.session_state.user_name}
Enrollment: {st.session_state.enroll_id}

SUBJECT: {dtype.upper()} IN THE MATTER OF {draft_cat.upper()} LITIGATION

TO,
[RECIPIENT NAME/OFFICE]
[ADDRESS LINE 1]

Sir/Madam,
Under the instructions from my client, I hereby serve you with the following {dtype}:

1. That my client is...
2. That the cause of action arose on...
3. Therefore, you are hereby requested to...

Regards,
Adv. {st.session_state.user_name}
({st.session_state.enroll_id})"""
                st.rerun()
            
            text = st.text_area("Live Editor", height=400, key="editor")            
        with c2:
            st.markdown('<p class="ai-analysis-text">📋 AI Analysis</p>', unsafe_allow_html=True)
            if st.button("Predict Probability", use_container_width=True):
                with st.spinner("Analyzing..."):
                    res = model.generate_content(f"Predict success probability for: {text}")
                    st.warning(res.text)
            st.write("---")
            pdf = generate_pdf(text, dtype)
            st.download_button("📥 Download PDF (Local)", pdf, f"{dtype}.pdf", mime="application/pdf", use_container_width=True)
            
            dest = st.text_input("Recipient Email(s)", placeholder="Separate with commas")
            
            if st.button("📧 Send as Email Body", type="primary", use_container_width=True):
                if dest:
                    with st.spinner("Transmitting Mail..."):
                        # FIXED: Changed function name and added missing credential arguments
                        ok, msg = send_text_email(
                            st.session_state.user_email, 
                            st.session_state.app_pass, 
                            dest, 
                            f"Legal Notice: {dtype}", 
                            text
                        )
                        if ok: st.success("Email sent as body text!")
                        else: st.error(msg)
                else: st.error("Recipient required!")
        st.markdown('</div>', unsafe_allow_html=True)

    with t2:
        st.markdown('<div class="glass-card">🔍 Document Intelligence</div>', unsafe_allow_html=True)
        up_file = st.file_uploader("Upload Document Image", type=['png', 'jpg', 'jpeg'])
        if up_file:
            img = Image.open(up_file)
            st.image(img, width=300)
            if st.button("Analyze Document"):
                res = model.generate_content(["Summarize this legal document and extract dates:", img])
                st.info(res.text)

    with t3:
        st.markdown('<div class="glass-card">📚 Case Law Search</div>', unsafe_allow_html=True)
        query = st.text_input("Enter Legal Query (e.g., Section 302 IPC Bail grounds)")
        if st.button("Research AI"):
            with st.spinner("Searching Database..."):
                res = model.generate_content(f"Provide 3 relevant Indian case law citations for: {query}")
                st.markdown(f'<div style="background:rgba(212,175,55,0.1); padding:15px; border-radius:10px; border-left:5px solid #D4AF37;">{res.text}</div>', unsafe_allow_html=True)

    with t4:
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

st.markdown('<p style="text-align:center; color:#777; font-size:12px; margin-top:50px;">ADVOCATE ELITE | SECURE LEGAL PORTAL</p>', unsafe_allow_html=True)