import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import google.generativeai as genai
import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import base64
from youtube_transcript_api import YouTubeTranscriptApi

# Configure Google Generative AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Define the prompt for summarization
prompt = "You are a YouTube video transcribe summarizer. You'll be given the transcript text and summarize the entire text and provide the important parts in points within the specified word limit."

# Function to convert text to PDF using ReportLab
def convert_to_pdf(text):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Define starting position for text
    text_object = c.beginText(40, height - 40)
    text_object.setFont("Helvetica", 12)
    
    # Split the text into lines to fit within page width
    lines = text.split('\n')
    for line in lines:
        text_object.textLine(line)
    
    # Draw the text and save the PDF
    c.drawText(text_object)
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer.getvalue()

# Function to create a download link for PDF
def create_download_link(pdf_data, filename):
    b64 = base64.b64encode(pdf_data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">Download {filename}</a>'

def extract_video_id(youtube_url):
    match = re.search(r"v=([^&]+)|youtu.be/([^?]+)", youtube_url)
    return match.group(1) or match.group(2) if match else None

def extract_transcript_details(youtube_video_url):
    try:
        video_id = youtube_video_url.split("=")[1]
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_para = ""
        for i in transcript_text:
            transcript_para += " " + i["text"]
        return transcript_para
    except Exception as e:
        st.error(f"Error extracting transcript: {e}")
        return None

# Function to generate content summary using Gemini
def generate_gemini_content(transcript_text, prompt, word_limit, summary_type, language, category):
    try:
        model = genai.GenerativeModel("gemini-pro")
        full_prompt = f"{prompt} Limit your response to {word_limit} words. Language: {language}. Category: {category}. "
        if summary_type == 'Detailed':
            full_prompt = f"Provide a detailed summary: {full_prompt}"
        else:
            full_prompt = f"Provide a concise summary: {full_prompt}"
        
        response = model.generate_content(full_prompt + transcript_text)
        return response.text
    except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None

st.title("YouTube Video Transcribe Summarizer")

# Sidebar for options
st.sidebar.header("Options")
language = st.sidebar.selectbox("Select Video Language", ["English", "Spanish", "French", "German", "Other"])
category = st.sidebar.selectbox("Select Video Category", ["Education", "Entertainment", "Technology", "Science", "Other"])
summary_type = st.sidebar.radio("Summary Type", ["Detailed", "Concise"])

col1, col2 = st.columns([3, 2])
with col1:
    youtube_url = st.text_input("Enter the YouTube Video URL")
with col2:
    word_limit = st.slider("Number of words for summary", min_value=50, max_value=500, value=250, step=50)

if youtube_url:
    video_id = extract_video_id(youtube_url)
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg", use_column_width=True)

    if st.button("Get Video Transcript Summarized"):
        with st.spinner('Extracting transcript...'):
            transcript_text = extract_transcript_details(youtube_url)

        if transcript_text:
            with st.spinner("Generating summary..."):
                summary = generate_gemini_content(transcript_text, prompt, word_limit, summary_type, language, category)
            
            if summary:
                st.markdown("## Summary")
                st.write(summary)

                st.markdown("## Full Transcript")
                with st.expander("Show Full Transcript"):
                    st.write(transcript_text)

                # Generate PDFs
                summary_pdf = convert_to_pdf(summary)
                transcript_pdf = convert_to_pdf(transcript_text)

                # Create download links
                st.markdown(create_download_link(summary_pdf, "summary.pdf"), unsafe_allow_html=True)
                st.markdown(create_download_link(transcript_pdf, "transcript.pdf"), unsafe_allow_html=True)

                # Alternative download buttons using Streamlit
                st.download_button(
                    label="Download Summary as PDF",
                    data=summary_pdf,
                    file_name="summary.pdf",
                    mime="application/pdf"
                )
                st.download_button(
                    label="Download Transcript as PDF",
                    data=transcript_pdf,
                    file_name="transcript.pdf",
                    mime="application/pdf"
                )

# Custom CSS for additional styling
st.markdown("""
    <style>
    .reportview-container { 
        background: #f0f0f5;
    }
    .sidebar .sidebar-content {
        background: #e6e6e6;
    }
    .stButton>button {
        background-color: #007bff;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    </style>
    """, unsafe_allow_html=True)
