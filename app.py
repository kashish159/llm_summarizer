import streamlit as st
from dotenv import load_dotenv #to load our env vars
load_dotenv() ##load all environment variables
import google.generativeai as genai
import os
import re ##regular expression
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import base64
genai.configure(api_key = os.getenv("GOOGLE_API_KEY"))



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


### Part1: getting the transcript from our yt video
from youtube_transcript_api import YouTubeTranscriptApi ###only works on public videos when link given
def extract_transcript_details(youtube_video_url):
    try:
        video_id  = youtube_video_url.split("=")[1]  ##https://youtube.com/watch?v=i0DCPOiNK4A out of thi link the id given after v= is the video id
        ##split would divide the url in two parts part0 and part 1 ---part 1 will have our yt id
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id) ## will have lists / dicts
        ## go ahead and append it into a paragraph
        transcript_para = ""
        ##The loop iterates over each dictionary in transcript_text 
        ## eg : i is {"text": "Hello"}  i["text"] is "Hello"
        for i in transcript_text :
            transcript_para += " " + i["text"] ##The expression i["text"] is used to access the value associated with the key "text" in a dictionary i
        return transcript_para

    except Exception as e : ##lets you handle the error
        st.error(f"Error extracting transcript: {e}")
        return None

### Part 2: interacting with our LLM to get the summary using prompt
prompt = "You are a YouTube video transcribe summarizer. You'll be given the transcript text and summarize the entire text and provide the important parts in points within the specified word limit."
def generate_gemini_content(transcript_text,prompt,word_limit,summary_type): ## will give us the summary of our transcript---subject could be ml,physics,etc -- for now remove subject --- prompt is basically telling the model what to do
       try: 
            model = genai.GenerativeModel("gemini-pro")
            full_prompt = f"{prompt} Limit your response to {word_limit} words.  "
            if summary_type == 'Detailed':
                full_prompt = f"Provide a detailed summary: {full_prompt}"
            else:
                 full_prompt = f"Provide a concise summary: {full_prompt}"
            


            
            response=model.generate_content(full_prompt+transcript_text) #both given as input
            return response.text
       except Exception as e:
        st.error(f"Error generating summary: {e}")
        return None



##  Part 3: Creating a streamlit app
st.title("YouTube Video Transcribe Summarizer")


# Sidebar for options
st.sidebar.header("Options")
language = st.sidebar.selectbox("Select Video Language", ["English", "Spanish", "French", "German", "Other"])
category = st.sidebar.selectbox("Select Video Category", ["Education", "Entertainment", "Technology", "Science", "Other"])
summary_type = st.sidebar.radio("Summary Type", ["Detailed", "Concise"])
















col1, col2 = st.columns([3, 2]) #The code creates a two-column layout where col1 is three times wider than col2.
with col1:
    youtube_url = st.text_input("Enter the YouTube Video URL")
    ##a box to get yt link
with col2:
    word_limit = st.slider("Number of words for summary", min_value=50, max_value=500, value=250, step=50)
    ##by deafult - 250

if youtube_url:
    video_id = extract_video_id(youtube_url)
    ## output thumbnail
    st.image(f"http://img.youtube.com/vi/{video_id}/0.jpg",use_column_width= True)
    ##default link when you upload a image as thumbnail on YT is where it is stored with reference to your video id
    ##so we arew retrieving it using this step

    if st.button("Get Video Transcript Summarized") :
        with st.spinner('Extracting transcript...'):
            transcript_text= extract_transcript_details(youtube_url)


        if  transcript_text:
            with st.spinner("Generating summary...."): ##The st.spinner function in Streamlit is used to display a temporary message while running a long computation or process. 
                ##When you use with, it creates a context in which certain operations are performed, and it ensures that necessary cleanup is done when the context is exited. - context management
                summary=generate_gemini_content(transcript_text,prompt,word_limit,summary_type)
            if summary:
                st.markdown("## Summary")##The st.markdown function in Streamlit is used to display text in Markdown format. Markdown is a lightweight markup language that you can use to add formatting elements to plaintext text documents.
                st.write(summary)

                st.markdown("## Full Transcript")
                with st.expander("Show Full Transcript"): ##This creates an expandable/collapsible section titled "Show Full Transcript".
                    st.write(transcript_text)

                st.download_button(
                    label="Download Summary",
                    data=summary,
                    file_name="summary.txt",
                    mime="text/plain"
                )

                st.download_button(
                    label="Download Transcript",
                    data=transcript_text,
                    file_name="transcript.txt",
                    mime="text/plain"
                )
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
                ##mime is  (Multipurpose Internet Mail Extensions) types are a standard way to specify the nature and format of a document, file, or set of bytes. 
                ##Type: The general category of the content (e.g., text, image, audio, video).
                # Subtype: The specific type of content within the general category (e.g., plain, html, png, mp4).
                # For example, text/plain indicates plain text, while image/jpeg refers to a JPEG image.



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
    """, unsafe_allow_html=True) ##can use html & css
