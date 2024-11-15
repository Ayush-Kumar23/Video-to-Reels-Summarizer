import streamlit as st
import hashlib
import whisper
import ffmpeg
from textblob import TextBlob
import os
from dotenv import load_dotenv

# Helper function for password hashing
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Apply CSS styles for a dynamic, dark-themed interface with gradients and background image
def apply_custom_styles():
    st.markdown("""
        <style>
            /* Background gradient and background image */
            .stApp {
                background: linear-gradient(135deg, #1e3c72, #2a5298);
                background-size: cover;
                font-family: 'Roboto', sans-serif;
                color: #ffffff;
            }
            
            /* Centered titles with white text */
            h1, h2 {
                color: #f5f5f5;
                text-align: center;
                font-weight: 700;
            }
            
            /* Form card styling */
            .form-container {
                background-color: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0px 4px 15px rgba(0, 0, 0, 0.2);
                max-width: 450px;
                margin: auto;
            }
            
            /* Buttons with gradient styling */
            .stButton > button {
                background: linear-gradient(to right, #ff7e5f, #feb47b);
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                cursor: pointer;
                transition: transform 0.3s, background 0.3s ease;
            }
            
            /* Hover effect for buttons */
            .stButton > button:hover {
                background: linear-gradient(to right, #feb47b, #ff7e5f);
                transform: scale(1.05);
            }
            
            /* Input field styling */
            .stTextInput, .stPasswordInput, .stFileUploader {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 10px;
                color: #ffffff;
            }
            
            /* Sidebar styling */
            .sidebar .sidebar-content {
                background: rgba(30, 60, 114, 0.8);
                color: #f5f5f5;
            }
            
            /* Navigation sidebar options */
            .stRadio > div > label {
                color: #f5f5f5;
                font-size: 16px;
                font-weight: bold;
            }
            
            /* Styling for video uploader */
            .stFileUploader {
                background: rgba(0, 0, 0, 0.3);
                color: #ffffff;
            }
            
            /* Logout button styling */
            .logout-button {
                background: #ff5c5c;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                padding: 10px;
                margin-top: 10px;
            }
            
            .logout-button:hover {
                background: #ff3d3d;
            }
        </style>
    """, unsafe_allow_html=True)

# Initialize Streamlit session state
if 'users' not in st.session_state:
    st.session_state['users'] = {}
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'current_user' not in st.session_state:
    st.session_state['current_user'] = None
if 'page' not in st.session_state:
    st.session_state['page'] = "home"

# Sign-up page logic
def signup():
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)
    st.title("Sign Up")
    with st.form(key="signup_form"):
        username = st.text_input("Create a Username")
        password = st.text_input("Create a Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        
        submitted = st.form_submit_button("Sign Up")
        
        if submitted:
            if username in st.session_state['users']:
                st.error("Username already exists! Please choose a different username.")
            elif password != confirm_password:
                st.error("Passwords do not match!")
            else:
                st.session_state['users'][username] = hash_password(password)
                st.success("Successfully signed up! Please login.")
                st.session_state['page'] = "login"
    st.markdown("</div>", unsafe_allow_html=True)

# Login page logic
def login():
    st.markdown("<div class='form-container'>", unsafe_allow_html=True)
    st.title("Login")
    with st.form(key="login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        
        submitted = st.form_submit_button("Login")
        
        if submitted:
            hashed_password = hash_password(password)
            if username in st.session_state['users'] and st.session_state['users'][username] == hashed_password:
                st.session_state['authenticated'] = True
                st.session_state['current_user'] = username
                st.success(f"Welcome {username}!")
                st.session_state['page'] = "main_app"
            else:
                st.error("Invalid username or password!")
    st.markdown("</div>", unsafe_allow_html=True)

# Logout function
def logout():
    st.session_state['authenticated'] = False
    st.session_state['current_user'] = None
    st.session_state['page'] = "home"
    st.success("Logged out successfully!")

# Profile page
def profile():
    st.title("User Profile")
    st.write("View and update your profile details.")

    # Display current username
    st.write(f"**Username:** {st.session_state['current_user']}")

    # Allow user to update their password
    with st.form(key="update_password_form"):
        new_password = st.text_input("New Password", type="password")
        confirm_new_password = st.text_input("Confirm New Password", type="password")
        
        submitted = st.form_submit_button("Update Password")
        
        if submitted:
            if new_password != confirm_new_password:
                st.error("Passwords do not match!")
            else:
                st.session_state['users'][st.session_state['current_user']] = hash_password(new_password)
                st.success("Password updated successfully!")

# Video processing functions
def configure():
    load_dotenv()

def extract_audio(video_path, output_audio_path):
    try:
        ffmpeg.input(video_path).output(output_audio_path).run(overwrite_output=True)
        return True
    except Exception as e:
        st.error(f"Error extracting audio: {e}")
        return False

def transcribe_audio(audio_path):
    model = whisper.load_model("base")
    result = model.transcribe(audio_path)
    return result['text'], result['segments']

def analyze_text_importance(segments):
    important_segments = []
    for segment in segments:
        text = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity
        word_count = len(text.split())
        importance_score = sentiment_score * word_count
        if importance_score > 1.0:
            important_segments.append({
                'text': text,
                'start_time': start_time,
                'end_time': end_time,
                'importance_score': importance_score
            })
    return important_segments

def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = int(seconds % 60)
    return f"{hours:02}:{minutes:02}:{seconds:02}"

def extract_video_segment(video_path, start_time, end_time, output_path):
    try:
        duration = end_time - start_time
        if duration > 0:
            ffmpeg.input(video_path, ss=start_time, t=duration).output(output_path).run(overwrite_output=True)
            return True
        else:
            st.error(f"Invalid segment duration: {duration} seconds.")
            return False
    except Exception as e:
        st.error(f"Error extracting video segment: {e}")
        return False

def compile_video_segments(segment_paths, output_video_path):
    with open('file_list.txt', 'w') as f:
        for segment in segment_paths:
            f.write(f"file '{segment}'\n")
    try:
        ffmpeg.input('file_list.txt', format='concat', safe=0).output(output_video_path, c='copy').run(overwrite_output=True)
        os.remove('file_list.txt')
        return True
    except Exception as e:
        st.error(f"Error compiling videos: {e}")
        return False

def generate_reel_from_important_segments(video_path, top_n=5, reel_count=3):
    audio_path = 'output_audio.wav'
    
    st.info("Extracting audio...")
    if not extract_audio(video_path, audio_path):
        return

    st.info("Transcribing audio...")
    _, segments = transcribe_audio(audio_path)
    st.success("Transcription and timestamp extraction completed.")

    st.info("Analyzing segments...")
    important_segments = analyze_text_importance(segments)
    important_segments.sort(key=lambda x: x['importance_score'], reverse=True)

    # Generate multiple reels with different segments
    for reel_num in range(1, reel_count + 1):
        st.info(f"Generating video segments for Reel {reel_num}...")
        top_segments = important_segments[(reel_num - 1) * top_n : reel_num * top_n]
        
        segment_paths = []
        for i, segment in enumerate(top_segments):
            output_segment_path = f"segment_reel{reel_num}_{i+1}.mp4"
            if extract_video_segment(video_path, segment['start_time'], segment['end_time'], output_segment_path):
                segment_paths.append(output_segment_path)
            else:
                st.error(f"Error generating segment {i+1} for Reel {reel_num}")


        output_reel_path = f'final_reel_{reel_num}.mp4'
        st.info(f"Compiling Reel {reel_num}...")
        if compile_video_segments(segment_paths, output_reel_path):
            st.success(f"Reel {reel_num} compilation successful!")
            st.video(output_reel_path)

# Updated main_app to accommodate the new function
def main_app():
    st.title("Video to Reel Summarizer")
    st.write(f"Hello, {st.session_state['current_user']}!")
    
    uploaded_file = st.file_uploader("Upload a video file", type=["mp4", "mov", "avi"])
    if uploaded_file is not None:
        with open("uploaded_video.mp4", "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.info("Generating multiple reels from the uploaded video...")
        generate_reel_from_important_segments("uploaded_video.mp4")
    
    if st.button("Logout", key="logout_button", on_click=logout):
        logout()


# Main interface logic
apply_custom_styles()
if not st.session_state['authenticated']:
    st.title("Welcome to the Video to Reel Summarizer!")
    st.write("Please choose an option below:")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            st.session_state['page'] = "login"
    with col2:
        if st.button("Sign Up"):
            st.session_state['page'] = "signup"

    if st.session_state['page'] == "login":
        login()
    elif st.session_state['page'] == "signup":
        signup()
else:
    option = st.sidebar.radio("Navigation", ["Main App", "Profile"])

    if option == "Main App":
        main_app()
    elif option == "Profile":
        profile()
