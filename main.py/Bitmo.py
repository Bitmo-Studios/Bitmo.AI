import datetime
import re
import threading
import customtkinter as ctk
import pyttsx3
from google import genai
from google.genai import types

# Initialize Text-To-Speech Engine
tts_engine = pyttsx3.init()


def speak_text(text):
    def run_tts():
        try:
            # Clean text for speech output
            clean_speech = re.sub(r"\*\*|\*", "", text)
            tts_engine.say(clean_speech)
            tts_engine.runAndWait()
        except Exception as e:
            print("TTS Error:", e)

    threading.Thread(target=run_tts, daemon=True).start()


# Configure App Appearance
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# API KEY PRESERVED FROM YOUR FILE:
API_KEY = "AQ.Ab8RN6IW5S6tcH7ueDYzMPuEDsVleWISwXWHLoNrSSmczo6QrA"
client = genai.Client(api_key=API_KEY)

# Main Application Window Setup
app = ctk.CTk()
app.title("Bitmo AI")
app.geometry("950x650")
app.configure(fg_color="#131314")

# Global Chat History State
chat_sessions = []
current_chat_history = []

# --- 1. LEFT SIDEBAR ---
sidebar = ctk.CTkFrame(app, width=220, fg_color="#1E1F20", corner_radius=0)
sidebar.pack(side="left", fill="y")

logo_label = ctk.CTkLabel(
    sidebar,
    text="✨ Bitmo AI",
    font=("Segoe UI Emoji", 22, "bold"),
    text_color="#A8C7FA",
)
logo_label.pack(padx=20, pady=(25, 15), anchor="w")


def start_new_chat():
    global current_chat_history
    current_chat_history = []
    for widget in chat_scroll.winfo_children():
        widget.destroy()
    render_bubble("Bitmo", "Hello! 👋 I'm Bitmo. Ask me anything!")


new_chat_btn = ctk.CTkButton(
    sidebar,
    text="➕  New Chat",
    fg_color="#2B2C2E",
    hover_color="#37393B",
    text_color="#FFFFFF",
    font=("Segoe UI Emoji", 13, "bold"),
    corner_radius=20,
    height=40,
    command=start_new_chat,
)
new_chat_btn.pack(padx=15, pady=10, fill="x")

history_title = ctk.CTkLabel(
    sidebar,
    text="Recent Chats",
    font=("Segoe UI", 11, "bold"),
    text_color="#8E918F",
)
history_title.pack(padx=20, pady=(15, 5), anchor="w")

history_scroll = ctk.CTkScrollableFrame(
    sidebar, fg_color="transparent", label_text=""
)
history_scroll.pack(fill="both", expand=True, padx=5, pady=5)

# --- 2. MAIN CHAT DISPLAY AREA ---
chat_container = ctk.CTkFrame(app, fg_color="transparent")
chat_container.pack(side="right", fill="both", expand=True, padx=20, pady=15)

chat_scroll = ctk.CTkScrollableFrame(
    chat_container, fg_color="transparent", label_text=""
)
chat_scroll.pack(fill="both", expand=True, pady=(0, 15))


def render_bubble(sender, text):
    is_user = sender == "You"
    bg_color = "#2B2C2E" if is_user else "#1E1F20"
    align = "e" if is_user else "w"

    msg_frame = ctk.CTkFrame(chat_scroll, fg_color=bg_color, corner_radius=16)
    msg_frame.pack(anchor=align, pady=6, padx=10, fill="x")

    sender_lbl = ctk.CTkLabel(
        msg_frame,
        text=sender,
        font=("Segoe UI Emoji", 11, "bold"),
        text_color="#8E918F",
    )
    sender_lbl.pack(anchor="w", padx=12, pady=(6, 0))

    # Strip raw Markdown asterisks for clean rendering
    cleaned_text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)

    msg_lbl = ctk.CTkLabel(
        msg_frame,
        text=cleaned_text,
        font=("Segoe UI Emoji", 13),
        text_color="#FFFFFF",
        wraplength=550,
        justify="left",
    )
    msg_lbl.pack(anchor="w", padx=12, pady=(2, 6))

    # Speak button under AI responses
    if not is_user:
        speak_btn = ctk.CTkButton(
            msg_frame,
            text="🔊 Speak",
            width=70,
            height=26,
            corner_radius=12,
            fg_color="#2B2C2E",
            hover_color="#37393B",
            text_color="#A8C7FA",
            font=("Segoe UI Emoji", 11, "bold"),
            command=lambda: speak_text(cleaned_text),
        )
        speak_btn.pack(anchor="w", padx=12, pady=(0, 8))


# Greeting
render_bubble("Bitmo", "Hello! 👋 I'm Bitmo. Ask me anything!")


# --- 3. WORKER FUNCTION WITH ALWAYS-ON SEARCH ---
def fetch_api_response(user_text, loading_frame):
    current_date = datetime.date.today().strftime("%B %d, %Y")

    system_prompt = (
        f"Today's date is {current_date}. The current year is 2026. "
        "Always search the web dynamically to retrieve accurate real-time factual information."
    )

    # Enable Live Google Search Grounding across all requests
    config_with_search = types.GenerateContentConfig(
        system_instruction=system_prompt,
        tools=[{"google_search": {}}],
    )

    models_to_try = [
        "gemini-3.6-flash",
        "gemini-3.6-flash",
    ]

    response_text = None
    last_error = ""

    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=user_text,
                config=config_with_search,
            )
            if response.text:
                response_text = response.text
                break
        except Exception as e:
            last_error = str(e)

    def update_ui():
        loading_frame.destroy()
        if response_text:
            render_bubble("Bitmo", response_text)

            # Add dynamic history item to left sidebar
            if len(current_chat_history) == 1:
                chat_title = (
                    user_text[:18] + "..." if len(user_text) > 18 else user_text
                )
                hist_btn = ctk.CTkButton(
                    history_scroll,
                    text=f"💬 {chat_title}",
                    fg_color="transparent",
                    hover_color="#2B2C2E",
                    text_color="#C4C7C5",
                    anchor="w",
                    font=("Segoe UI Emoji", 12),
                )
                hist_btn.pack(fill="x", pady=2)
        else:
            render_bubble("Bitmo", f"Error: {last_error}")

    app.after(0, update_ui)


def send_message(event=None):
    user_text = prompt_input.get().strip()
    if not user_text:
        return

    current_chat_history.append(user_text)
    render_bubble("You", user_text)
    prompt_input.delete(0, "end")

    loading_frame = ctk.CTkFrame(
        chat_scroll, fg_color="#1E1F20", corner_radius=16
    )
    loading_frame.pack(anchor="w", pady=6, padx=10, fill="x")
    status_lbl = ctk.CTkLabel(
        loading_frame,
        text="Bitmo is searching the web... 🔍",
        font=("Segoe UI Emoji", 12, "italic"),
        text_color="#8E918F",
    )
    status_lbl.pack(anchor="w", padx=12, pady=8)

    threading.Thread(
        target=fetch_api_response,
        args=(user_text, loading_frame),
        daemon=True,
    ).start()


# --- 4. BOTTOM PROMPT BAR ---
input_frame = ctk.CTkFrame(
    chat_container, fg_color="#1E1F20", corner_radius=25, height=50
)
input_frame.pack(fill="x", side="bottom")

prompt_input = ctk.CTkEntry(
    input_frame,
    placeholder_text="Enter a prompt here...",
    fg_color="transparent",
    border_width=0,
    text_color="#FFFFFF",
    font=("Segoe UI Emoji", 13),
)
prompt_input.pack(side="left", fill="both", expand=True, padx=(20, 10))
prompt_input.bind("<Return>", send_message)

send_button = ctk.CTkButton(
    input_frame,
    text="➔",
    width=36,
    height=36,
    corner_radius=18,
    fg_color="#A8C7FA",
    text_color="#003062",
    hover_color="#7CACC5",
    font=("Segoe UI Emoji", 14, "bold"),
    command=send_message,
)
send_button.pack(side="right", padx=(0, 10), pady=7)

app.mainloop()