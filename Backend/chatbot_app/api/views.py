from django.shortcuts import render, redirect
from .inferenceBart import ask_question
from django.http import JsonResponse
import os
from .inferenceYolo import run_inference

from datetime import datetime
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def ClearChathistory(request):
    request.session.clear()
    return redirect('chatbot')

import os
from datetime import datetime
from django.shortcuts import render, redirect
import whisper
import torchaudio
from django.http import HttpResponse

# Set the backend for torchaudio (try using 'soundfile' instead of 'sox_io')
try:
    torchaudio.set_audio_backend("soundfile")  # Switch to 'soundfile' backend
except Exception as e:
    print(f"Error setting torchaudio backend: {e}")

# Load the Whisper model
model_name = "base"  # Use the model that fits your needs (tiny, base, small, etc.)
model = whisper.load_model(model_name)


from django.http import HttpResponse
from gtts import gTTS
import os


def generate_audio(request):
    """
    Generate an audio file from text using gTTS and serve it.
    """
    text = request.GET.get('text', '').strip()  # Get and sanitize the bot's message
    if not text:
        return HttpResponse("No text provided.", status=400)

    try:
        # Generate audio from the text
        tts = gTTS(text=text, lang='en')  # Specify language
        audio_path = "bot_audio.mp3"  # Temporary file
        tts.save(audio_path)

        # Serve the audio file
        with open(audio_path, 'rb') as audio_file:
            response = HttpResponse(audio_file.read(), content_type='audio/mpeg')
            response['Content-Disposition'] = 'inline; filename="bot_audio.mp3"'
        os.remove(audio_path)  # Clean up temporary file
        return response

    except Exception as e:
        return HttpResponse(f"Error generating audio: {str(e)}", status=500)
    

def preprocess_and_resample_audio(input_path, output_path, target_sr=16000):
    print(torchaudio.info(input_path))
    input_path = os.path.normpath(input_path)
    output_path = os.path.normpath(output_path)
    
    # Load the audio file
    print("Reached Here")
    print(f"Loading audio from: {input_path}")

    # Set the backend explicitly to 'sox_io'
    torchaudio.set_audio_backend("sox_io")
        
    # Check if the backend was set properly
    print(f"Backend set to: {torchaudio.get_audio_backend()}")
    
    waveform, sr = torchaudio.load(input_path)

    # Resample if necessary
    if sr != target_sr:
        print(f"Resampling audio from {sr} Hz to {target_sr} Hz...")
        resampler = torchaudio.transforms.Resample(orig_freq=sr, new_freq=target_sr)
        waveform = resampler(waveform)
    else:
        print("No resampling needed.")

    # Save the resampled audio for later use
    os.makedirs(os.path.dirname(output_path), exist_ok=True)  # Ensure the output directory exists
    torchaudio.save(output_path, waveform, target_sr)
    
    print(f"Resampled audio saved to: {output_path}")
    return output_path



def transcribe_audio(audio_path, custom_context=""):
    try:
        # Check if the file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"Transcribing audio from: {audio_path}")
        result = model.transcribe(audio_path, initial_prompt=custom_context)
        return result["text"]
    except Exception as e:
        print(f"Error transcribing audio: {e}")
        return "Error during transcription"



def save_uploaded_audio(audio_file):
    """Save the uploaded audio file to the media/audio directory."""
    audio_file_path = os.path.join('media', 'audio', audio_file.name)
    os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)
    with open(audio_file_path, 'wb') as f:
        for chunk in audio_file.chunks():
            f.write(chunk)
    return audio_file_path



def format_transcription_as_question(transcription):
    """Convert the transcription into a question format."""
    transcription = transcription.strip()
    if not transcription.endswith("?"):
        transcription += "?"
    return transcription


def generate_answer(question, object_name):
    """Generate an appropriate answer based on the question and detected object."""
    try:
        if any(phrase in question.lower() for phrase in ["thanks", "thank you", "thanks a lot", "thank you so much", "thanks for all your efforts"]):
            return f"You are welcome 😊. Feel free to ask more about {object_name}."
        else:
            return ask_question(question, object_name)  # Implement this function as needed
    except Exception as e:
        return f"An error occurred: {e}"



def handle_text_input(question, chat_history, detected_objects, timestamp):
    """Process text-based questions."""
    chat_history.append({"role": "user", "content": question, "timestamp": timestamp})
    if detected_objects:
        object_name = detected_objects[0]['label']
        answer = generate_answer(question, object_name)
    else:
        answer = "No objects detected to inquire about. Please upload an image"
    chat_history.append({"role": "bot", "content": answer, "timestamp": timestamp})


def handle_audio_input(audio_file, chat_history, detected_objects, timestamp):
    """Handle audio input, preprocessing, transcription, and answering."""
    if not audio_file.name.endswith('.wav'):
        return HttpResponse("Error: Only .wav files are allowed.", status=400)

    audio_file_path = save_uploaded_audio(audio_file)
    resampled_audio_path = os.path.join('media', 'audio', 'resampled_' + audio_file.name)
            
    # Ensure the directory exists
    os.makedirs(os.path.dirname(audio_file_path), exist_ok=True)

    # Save the uploaded .wav audio file
    try:
        with open(audio_file_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
        print(f"Saved audio file to: {audio_file_path}")
    except Exception as e:
        print(f"Error saving audio file: {e}")
        return HttpResponse("Error saving audio file.", status=500)
    
    resampled_audio_path = preprocess_and_resample_audio(audio_file_path, resampled_audio_path)

    if not resampled_audio_path:
        return HttpResponse("Error processing audio.", status=500)

    custom_context = "Yali, Garuda, Akhi Jhyal, Prayer Wheel, Boudhanath"
    transcription = transcribe_audio(resampled_audio_path, custom_context)

    question = format_transcription_as_question(transcription)
    chat_history.append({"role": "user", "content": transcription, "timestamp": timestamp})

    if detected_objects:
        object_name = detected_objects[0]['label']
        answer = generate_answer(question, object_name)
    else:
        answer = "No objects detected to inquire about. Please upload an image"
    chat_history.append({"role": "bot", "content": answer, "timestamp": timestamp})


def quick_qa(request):
    if request.method == "POST":
        question = request.POST.get("question", "").strip()
        object_name = request.POST.get("object_name", "").strip()
        timestamp = datetime.now()

        if question and object_name:
            answer = generate_answer(question, object_name)
        else:
            answer = "Please select a class and enter a question."
        return render(request, "chatbot_app/quick_QA.html", {"answer": answer})
    return render(request, "chatbot_app/quick_QA.html", {"answer": ""})




def chatbot_view(request):
    chat_history = request.session.get('chat_history', [])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # result_url = request.session.get('result_url')
    detected_objects = request.session.get('detected_objects', [])
    print(f"Detected Objects are : {detected_objects}")

    if request.method == "POST":
        question = request.POST.get("question")
        if question:
            handle_text_input(question, chat_history, detected_objects, timestamp)

        if request.FILES.get('audio'):
            audio_file = request.FILES['audio']
            handle_audio_input(audio_file, chat_history, detected_objects, timestamp)

        # Save chat history in session
        request.session['chat_history'] = chat_history

    return render(request, "chatbot_app/chat.html", {
        "chat_history": chat_history
    })



def upload_audio(request):
    print("POST request received")
    chat_history = request.session.get('chat_history', [])
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    detected_objects = request.session.get('detected_objects', [])

    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        handle_audio_input(audio_file, chat_history, detected_objects, timestamp)

        # Save chat history in session
        request.session['chat_history'] = chat_history

    return render(request, "chatbot_app/chat.html", {
        "chat_history": chat_history
    })



def handle_multiple_objects(request, detected_objects):
    if len(detected_objects) > 1:

        return detected_objects
    return detected_objects  # Return the single object


def select_object(request):
    pending_objects = request.session.get('pending_objects', [])
    chat_history = request.session.get('chat_history', [])

    if request.method == 'POST':
        selected_object = request.POST.get('selected_object')
        if selected_object:
            request.session['selected_object'] = selected_object  # Store user selection
            structured_objects = [{"label": selected_object, "score": "0.90"}]
            print(f"User selected: {request.session.get('detected_objects', [])}")

            chat_history.append({
                "role": "user",
                "content": f"Selected Object : {selected_object}",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            chat_history.append({
                "role": "bot",
                "content": f"You can now ask questions related to {selected_object}.",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            request.session['chat_history'] = chat_history
            request.session['detected_objects'] = structured_objects
            return redirect('chatbot')  # Redirect to chatbot after selection

    return render(request, "chatbot_app/chat.html", {
        "chat_history": chat_history,
        "objects": pending_objects  # Pass detected objects for selection
    })



def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        uploaded_file = request.FILES['image']
        
        # Save uploaded image
        upload_dir = os.path.join('media/uploads')
        os.makedirs(upload_dir, exist_ok=True)
        upload_path = os.path.join(upload_dir, uploaded_file.name)

        with open(upload_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

        # Perform YOLO inference
        result_dir = os.path.join('media/results')
        result_image_path, detected_objects = run_inference(upload_path, result_dir)

        result_url = f"/media/results/{os.path.basename(result_image_path)}"
        detected_objects_list = [obj['label'] for obj in detected_objects]
        print(f"Detected-object-list: {detected_objects_list}")
        unique_detected_objects_list = list(set(detected_objects_list))  # Remove duplicates
        print(f"Uniques Detected Object List : {unique_detected_objects_list}")

        chat_history = request.session.get('chat_history', [])

        chat_history.append({
            "role": "user",
            "content": f'<img src="{upload_path}" alt="Uploaded Image" style="max-width: 150px; height: auto;"><br>',
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        if unique_detected_objects_list:
            request.session['pending_objects'] = unique_detected_objects_list  # Store detected objects
            print(f"Pending_objects contain : {request.session['pending_objects']}")
            
            chat_history.append({
                "role": "bot",
                "content": (
                    f"Detected objects: <strong>{', '.join(unique_detected_objects_list)}</strong><br>"
                    f'<img src="{result_url}" alt="YOLO Result" style="max-width: 150px; height: auto;"><br>'
                ),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

            # If multiple objects detected, ask user to select one
            if len(unique_detected_objects_list) > 1:
                chat_history.append({
                    "role": "bot",
                    "content": f"Please select an object from: {', '.join(unique_detected_objects_list)}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                request.session['chat_history'] = chat_history
                return redirect('select_object')  # Redirect to selection page

            else:
                selected_object = unique_detected_objects_list[0]
                request.session['detected_objects'] = selected_object

                chat_history.append({
                    "role": "bot",
                    "content": f"You can now ask questions related to: {selected_object}",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        else:
            chat_history.append({
                "role": "bot",
                "content": "No objects detected in the image.<br>",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })

        request.session['chat_history'] = chat_history
        request.session['result_url'] = result_url
        request.session['detected_objects'] = detected_objects
        return redirect('chatbot')  # Redirect to chatbot

    return render(request, 'chatbot_app/chat.html')


