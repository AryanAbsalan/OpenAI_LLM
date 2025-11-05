import streamlit as st
from openai import OpenAI
from config import OPENAI_API_KEY
import json

# --- Initialize OpenAI client ---
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Define functions the AI can call ---
def create_calendar_event(title, date, time, attendee):
    return f"[Action] Creating Calendar Event: {title} on {date} at {time} with {attendee}"

def send_email(to, subject, body):
    return f"[Action] Sending Email to {to} with subject '{subject}'"

# --- Define tool schemas ---
tools = [
    {
        "type": "function",
        "name": "create_event",
        "description": "Create a calendar event with title, date, time, and attendee.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "date": {"type": "string"},
                "time": {"type": "string"},
                "attendee": {"type": "string"}
            },
            "required": ["title", "date", "time", "attendee"]
        }
    },
    {
        "type": "function",
        "name": "send_email",
        "description": "Send an email with a recipient, subject, and body.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {"type": "string"},
                "subject": {"type": "string"},
                "body": {"type": "string"}
            },
            "required": ["to", "subject", "body"]
        }
    }
]

# --- Streamlit UI ---
st.title("AI Assistant with Streamlit")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful assistant that can create calendar events and send emails."}
    ]

user_input = st.text_input("Type your message:")

if st.button("Send") and user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    response_container = st.empty()  # Placeholder for streaming text
    full_response = ""

    stream = client.responses.create(
        model="gpt-4o-mini",
        input=st.session_state.messages,  # must be 'input', not 'messages'
        tools=tools,
        temperature=0.7,
        stream=True                     # enable streaming
    )


    for event in stream:
        if event.type == "response.output_text.delta":
            full_response += event.delta
            st.text(full_response)
        elif event.type == "response.completed":
            # Check for function calls
            if event.response.output and event.response.output[0].type in ["function_call", "tool_call"]:
                func_args = json.loads(event.response.output[0].arguments)
                func_name = event.response.output[0].name
                if func_name == "create_event":
                    result = create_calendar_event(**func_args)
                elif func_name == "send_email":
                    result = send_email(**func_args)
                else:
                    result = "[Action] Unknown function"
                    
                st.success(result)

    # Append assistant message to conversation history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
