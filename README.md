# VQA Voyager 🚀
Multimodal Visual Question Answering System for Cultural Heritage Exploration

## 🧠 Overview
VQA Voyager is an intelligent system that enables users to ask voice-based questions about cultural heritage artifacts and receive contextual answers, using image and speech processing.

## 🔍 Features
- 📸 **Image Capture & Object Detection** using YOLOv8
- 🎙️ **Voice-Based Interaction** with Whisper (Speech-to-Text) & TTS (Text-to-Speech)
- 🤖 **BART-based Question Answering** using multimodal input (image + text)
- 💬 **Chatbot Interface** for natural interaction
- 🌐 **Responsive Web Interface** using Django, Jinja2, W3.CSS
- 🧾 **Conversation Session Management** with MySQL
- 📦 MVC Architecture and Clean Modular Code

## 🛠️ Tech Stack
- **Frontend**: HTML, CSS (W3.CSS), Jinja Templates
- **Backend**: Django, Python
- **AI Models**: YOLOv8 (Object Detection), Whisper (Speech-to-Text), BART (Text Generation)
- **Database**: MySQL
- **Deployment**:locally deployed

## 🖼️ Workflow
1. User captures image of a heritage site/object.
2. Object is detected via YOLOv8 and visualized.
3. User asks a question via voice input.
4. Speech is transcribed using Whisper and passed to the BART model.
5. BART generates a relevant response using the question and object context.
6. Response is shown on web interface and also read out using TTS.


# 1️⃣ Clone the repository
```bash
git@github.com:Guche02/VQA-Voyager.git
cd VQA-Voyager

# 2️⃣ Create and activate a virtual environment
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# 3️⃣ Install all required dependencies
pip install -r requirements.txt

# 4️⃣ Run database migrations (if needed)
python manage.py migrate

# 5️⃣ Start the Django development server
python manage.py runserver

