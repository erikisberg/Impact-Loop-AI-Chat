import streamlit as st
import openai
import os
import time
import datetime
import re
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
openai_api_key = st.secrets["OPENAI_API_KEY"]
client = openai.OpenAI(api_key=openai.api_key)


# Assistant ID
ASSISTANT_ID = "asst_tk9nMU9bDKPWmT5T7uc3L9Jq"  

def remove_source_tags(text):
    # Remove source tags
    pattern = r'【.*?†source】'
    cleaned_text = re.sub(pattern, '', text)
    
    # Remove any remaining square brackets and their contents
    cleaned_text = re.sub(r'\[.*?\]', '', cleaned_text)
    
    # Replace line breaks with spaces
    cleaned_text = cleaned_text.replace('\n', ' ')
    
    return cleaned_text

# Initialize session state
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

# Sidebar reset button
if st.sidebar.button("Reset Conversation"):
    st.session_state.thread_id = None
    st.session_state.messages = []

# Function to create a new thread
def create_thread():
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    # Get the current date
    current_date = datetime.date.today().isoformat()
    # Send the current date as the first message
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=current_date,
    )
    # Append the date message to the conversation history
    st.session_state.messages.append({"role": "user", "content": current_date})
    # Optionally, process this message immediately
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
    )
    wait_for_run_completion(run)
    # Get the assistant's response to the date
    assistant_response = get_assistant_response()
    # Append assistant's message to session state
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})

# Function to submit a message and start a run
def submit_message(user_message):
    # Create a message
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=user_message,
    )
    # Start a run
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID,
    )
    return run

# Function to wait for the run to complete
def wait_for_run_completion(run):
    while run.status in ["queued", "in_progress"]:
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id,
        )
    return run

# Function to get the assistant's response
def get_assistant_response():
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id,
        order="asc"
    )
    # Find the last assistant message
    for message in reversed(messages.data):
        if message.role == "assistant":
            return message.content[0].text.value
    return ""

# Function to simulate streaming the assistant's response
def display_response_stream(response, message_placeholder):
    full_response = ""
    for char in response:
        full_response += char
        message_placeholder.write(full_response)
        time.sleep(0.01)  # Adjust the speed as needed

# Streamlit app layout
st.title("Chat with OpenAI Assistant")

# Display the conversation history using chat elements
if st.session_state.messages:
    for i, message in enumerate(st.session_state.messages):
        # Skip the first message if it's the date
        if i == 0 and message["content"] == datetime.date.today().isoformat():
            continue
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

# Chat input at the bottom
user_input = st.chat_input("Type your message here...")

if user_input:
    if not st.session_state.thread_id:
        create_thread()
    # Append user message to session state
    st.session_state.messages.append({"role": "user", "content": user_input})
    # Display user message immediately
    with st.chat_message("user"):
        st.write(user_input)
    # Prepare for simulated streaming
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
    # Submit the message and start a run
    run = submit_message(user_input)
    # Wait for the run to complete
    run = wait_for_run_completion(run)
    # Get the assistant's response
    assistant_response = get_assistant_response()
    # Remove source tags and line breaks from the response
    assistant_response_cleaned = remove_source_tags(assistant_response)
    # Simulate streaming the assistant's response
    display_response_stream(assistant_response_cleaned, message_placeholder)
    # Append assistant message to session state
    st.session_state.messages.append({"role": "assistant", "content": assistant_response_cleaned})
