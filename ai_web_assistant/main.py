
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from openai import OpenAI
import json

from config import OPENAI_API_KEY

# --- Initialize OpenAI client ---
client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()

# Mount static folder for JS/CSS if needed
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# --- Functions the assistant can call ---
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

# --- Home page ---
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# --- Streaming chat endpoint ---
@app.get("/chat")
async def chat(user_input: str):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": user_input}
    ]

    def event_stream():
        try:
            stream = client.responses.create(
                model="gpt-4o-mini",
                input=messages,
                tools=tools,
                temperature=0.7,
                stream=True  # enable streaming
            )
        except Exception as e:
            yield f"data:[Error] Failed to contact OpenAI API: {str(e)}\n\n"
            return

        for event in stream:
            try:
                # Stream partial text output
                if event.type == "response.output_text.delta":
                    content = event.delta.get("content")
                    if content:
                        yield f"data:{content}\n\n"

                # Handle completed event
                elif event.type == "response.completed":
                    if event.response.output and event.response.output[0].type in ["function_call", "tool_call"]:
                        func_args = json.loads(event.response.output[0].arguments)
                        func_name = event.response.output[0].name

                        if func_name == "create_event":
                            result = create_calendar_event(**func_args)
                        elif func_name == "send_email":
                            result = send_email(**func_args)
                        else:
                            result = "[Action] Unknown function"

                        yield f"data:{result}\n\n"

            except Exception as e_inner:
                # Catch errors during streaming or function execution
                yield f"data:[Error] {str(e_inner)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
