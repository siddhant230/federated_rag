import gradio as gr
import json
import os
import psutil
from datetime import datetime
from pathlib import Path
import PyPDF2
from main import (
    create_context,
    BgeSmallEmbedModel,
    T5LLM, OllamaLLM, GeminiLLM,
    network_participants,
    make_index,
    perform_query,
    scrape_save_data
)
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter
from syftbox.lib import Client, SyftPermission
import shutil

embed_model = BgeSmallEmbedModel()
# model_name = "qwen2.5:1.5b"
model_name = "qwen2.5:0.5b"
# model_name = "qwen2.5:1.5b-instruct"
# model_name = "smollm2:135m"
# model_name = "smollm2:360m"
# model_name = "tinyllama"
# model_name = "tinydolphin"
# model_name = "granite3-moe"

llm = OllamaLLM(model_name=model_name)  # T5LLM() #local setup
client = Client.load()
global_context = create_context()
pipeline = IngestionPipeline(
    transformations=[SentenceSplitter(
        chunk_size=30, chunk_overlap=10), embed_model.embedding_model])

class SessionState:
    def __init__(self):
        self.chat_history = []
        self.current_model = "HuggingFace"
        self.gemini_key = None
        self.datasite_path = Path(os.path.expanduser(
            "~")) / ".federated_rag" / "data"
        # for testing uncomment the line below
        # self.datasite_path = Path("extra_test/scraping_test")
        self.participants = []
        self.session_name = "Untitled Session"
        self.query_count = 0

session = SessionState()

def store_indices_locally(participants, datasite_path, target):
    index_path_dict = {}
    for user_folder in participants:
        index_path: Path = Path(datasite_path) / \
            user_folder / "public" / "vector_index"
        index_path_dict[user_folder] = index_path

    for user, index_path in index_path_dict.items():
        path = target / f"vector_index_{user}"
        shutil.copytree(index_path, path, dirs_exist_ok=True)
        print(f"Index copied for {user} at {path}")
              
def initialize_backend():
    try:
        if not session.datasite_path.exists():
            session.datasite_path.mkdir(parents=True, exist_ok=True)

        session.participants = network_participants(client.datasite_path.parent) # SyftBox/datasites
        scrape_save_data(session.participants, client.datasite_path.parent) # SyftBox/datasites

        active_participants = make_index(
            session.participants,
            client.datasite_path.parent,
            global_context,
            pipeline=pipeline
        )
        
        print(f"Active participants: {active_participants}")
        print(f"Storing indices locally..")

        store_indices_locally(
            participants=active_participants,
            datasite_path=client.datasite_path.parent,
            target=session.datasite_path,
        )
    except Exception as e:
        print("Error occurred during initialization:", str(e))


def process_message(message, history, model_choice, gemini_key=None, file=None):
    try:
        if model_choice == "Gemini" and not gemini_key:
            return "", history, session.session_name
        if model_choice == "HuggingFace":
            try:
                response_obj = perform_query(
                    query=message,
                    source=session.datasite_path, # ~/ ".federated_rag" / "data"
                    embed_model=embed_model,
                    llm=llm,
                    context=global_context
                )
                response = response_obj
            except Exception as e:
                print(f"Error processing query: {str(e)}")
        else:
            response = f"Processing with Gemini: {message}"
            gemini_llm = GeminiLLM(api_key_path=gemini_key)
            response_obj = perform_query(
                query=message,
                source=session.datasite_path, # ~/ ".federated_rag" / "data"
                embed_model=embed_model,
                llm=gemini_llm,
                context=global_context
            )
            response = response_obj
        if file:
            try:
                pdf_reader = PyPDF2.PdfReader(file.name)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text()
                response += f"\n\nProcessed PDF content: {pdf_text[:500]}..."
            except Exception as e:
                response += f"\n\nError processing PDF: {str(e)}"

        history.append((message, response))

        session.query_count += 1
        if session.query_count <= 2:
            session.session_name = update_session_name(message)

        return "", history, session.session_name
    except Exception as e:
        return "", history, session.session_name


def get_metrics():
    cpu_percent = psutil.cpu_percent()
    memory_percent = psutil.virtual_memory().percent
    return f"CPU: {cpu_percent:.1f}% | Memory: {memory_percent:.1f}%"


def handle_model_selection(model_choice):
    session.current_model = model_choice
    return gr.update(visible=model_choice == "Gemini")


def update_session_name(query):
    words = query.split()[:2]
    return f"Session_{' '.join(words)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def save_snapshot(history, session_name):
    if not os.path.exists('sessions'):
        os.makedirs('sessions')

    filename = f"sessions/{session_name}.json"
    data = {
        "session_name": session_name,
        "chat_history": history,
        "timestamp": datetime.now().isoformat()
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

    return f"Session saved as {filename}"


def create_ui():
    with gr.Blocks(theme=gr.themes.Soft()) as demo:
        gr.Markdown("<center><h1>🔮 Federated RAG </h1></center>")
        with gr.Tab("FED-RAG-BOT"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Session Info")

                    session_name_display = gr.Textbox(
                        label="Session Name",
                        value=session.session_name,
                        interactive=False
                    )

                    gr.Markdown("### Chat History")
                    session_history = gr.Textbox(
                        label="History",
                        value="",
                        interactive=False,
                        lines=10,
                        show_label=False
                    )

                    clear_btn = gr.Button("Clear History")
                    delete_btn = gr.Button("Delete Session")

                with gr.Column(scale=3):
                    chatbot = gr.Chatbot(height=700)

                    with gr.Row():
                        msg = gr.Textbox(
                            show_label=False,
                            placeholder="Enter your message...",
                            scale=8
                        )
                        send = gr.Button("Send", scale=1)

                with gr.Column(scale=1):
                    gr.Markdown("### Upload PDF")
                    file_upload = gr.File(
                        label="Upload PDF", file_types=[".pdf"])

                    gr.Markdown("### Model Selection")
                    model_dropdown = gr.Dropdown(
                        choices=["Gemini", "HuggingFace"],
                        label="Select Model",
                        value="HuggingFace"
                    )

                    gemini_key_input = gr.Textbox(
                        label="Gemini API Key",
                        visible=False,
                        type="password"
                    )

                    gr.Markdown("### System Metrics")
                    metrics_text = gr.Textbox(
                        label="Metrics",
                        interactive=False
                    )
                    refresh_btn = gr.Button("Refresh Metrics")

                    save_btn = gr.Button("Save Snapshot")

            model_dropdown.change(
                fn=handle_model_selection,
                inputs=model_dropdown,
                outputs=gemini_key_input
            )

            send.click(
                fn=process_message,
                inputs=[msg, chatbot, model_dropdown,
                        gemini_key_input, file_upload],
                outputs=[msg, chatbot, session_name_display]
            )

            msg.submit(
                fn=process_message,
                inputs=[msg, chatbot, model_dropdown,
                        gemini_key_input, file_upload],
                outputs=[msg, chatbot, session_name_display]
            )

            refresh_btn.click(
                fn=get_metrics,
                outputs=metrics_text
            )

            save_btn.click(
                fn=save_snapshot,
                inputs=[chatbot, session_name_display],
            )

            clear_btn.click(
                fn=lambda: clear_session_history(session_history),
                outputs=session_history
            )

            delete_btn.click(
                fn=lambda: delete_session(
                    session_name_display, session_history),
                outputs=[session_name_display, session_history]
            )

            demo.load(get_metrics, outputs=metrics_text, every=10)

            gr.HTML("""
                <script>
                    function saveSessionData() {
                        let sessionData = {
                            chatHistory: window.sessionStorage.getItem('chatHistory') || "[]",
                            sessionName: window.sessionStorage.getItem('sessionName') || "Untitled Session"
                        };
                        localStorage.setItem("sessionData", JSON.stringify(sessionData));
                    }
                    
                    function loadSessionData() {
                        let sessionData = localStorage.getItem("sessionData");
                        if (sessionData) {
                            sessionData = JSON.parse(sessionData);
                            window.sessionStorage.setItem('chatHistory', sessionData.chatHistory);
                            window.sessionStorage.setItem('sessionName', sessionData.sessionName);

                            const chatHistory = JSON.parse(sessionData.chatHistory);
                            const chatWindow = document.querySelector('gr-chatbot');
                            chatHistory.forEach(([user, bot]) => {
                                const message = document.createElement('div');
                                message.classList.add('message');
                                message.innerHTML = `<div class="user">${user}</div><div class="bot">${bot}</div>`;
                                chatWindow.appendChild(message);
                            });
                        }
                    }
                    
                    window.onload = loadSessionData;
                    window.onbeforeunload = saveSessionData;
                </script>
            """)
        with gr.Tab("STATS"):
            gr.Image("imgs/wordcloud.png")
    return demo


def clear_session_history(session_history):
    session.chat_history = []
    return gr.update(value="")


def delete_session(session_name_display, session_history):
    session.chat_history = []
    session.session_name = "Untitled Session"
    session_name_display.update(value=session.session_name)
    return gr.update(value=""), session_name_display


def main():
    initialize_backend()
    demo = create_ui()
    demo.launch(server_port=7861, show_error=True)


if __name__ == "__main__":
    main()
