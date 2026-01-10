import streamlit as st
import google.generativeai as genai

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="EduGenie - Course Creator", layout="wide")

# Custom CSS for Pink & White Textured Background
st.markdown("""
    <style>
    .stApp {
        background-color: #ffffff;
        background-image:  radial-gradient(#ffebf0 2px, transparent 2px);
        background-size: 32px 32px;
    }
    .main-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #d63384;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. GEMINI API SETUP ---
# Replace with your actual API Key or use streamlit secrets
API_KEY = "AIzaSyBlNOgcpfBxoxedoMetjtRMxLWzoy2UidE" 
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. SIDEBAR INPUTS ---
with st.sidebar:
    st.title("🎓 Course Settings")
    course_name = st.text_input("Course Name", placeholder="e.g., Python for Data Science")
    course_level = st.selectbox("Course Level", ["Beginner", "Moderate", "Advanced"])
    week_no = st.number_input("Week Number", min_value=1, max_value=52, value=1)
    
    generate_btn = st.button("Generate Course Content")
    st.divider()
    st.info("This app uses Gemini AI to generate professional study materials.")

# --- 4. MAIN INTERFACE ---
st.title("🌸 EduGenie Course Architect")

# Initialize Session State for Chatbot
if "messages" not in st.session_state:
    st.session_state.messages = []

# Layout: Left side for content, Right side for Chatbot
col1, col2 = st.columns([2, 1])

with col1:
    if generate_btn and course_name:
        with st.spinner("Crafting your professional curriculum..."):
            prompt = f"""
            Create professional course content for: {course_name}.
            Level: {course_level}.
            Week: {week_no}.
            
            Please provide the output in the following structure:
            1. # Professional Notes: Detailed educational content.
            2. # Mindmap: Provide a Mermaid.js code block for a mindmap visualizing this content.
            3. # Quiz: 3 Multiple Choice Questions with answers at the end.
            """
            
            response = model.generate_content(prompt)
            st.markdown(response.text)
    else:
        st.write("Enter course details in the sidebar to start learning!")

# --- 5. SIMPLE CHATBOT INTERFACE ---
with col2:
    st.subheader("💬 Study Assistant")
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Ask me anything about the course..."):
        # Add user message to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate AI response
        with st.chat_message("assistant"):
            full_prompt = f"You are a professional tutor for the course {course_name}. Question: {prompt}"
            response = model.generate_content(full_prompt)
            st.markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})