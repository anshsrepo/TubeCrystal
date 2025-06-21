from flask import Flask, request, jsonify, render_template
import os
import yt_dlp
import logging
import shutil
import whisper
from transformers import BartTokenizer, BartForConditionalGeneration, pipeline

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

TEMP_DIR = "temp"
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Cache BART model and tokenizer for summarization
try:
    logger.info("Loading BART model for summarization")
    BART_MODEL_NAME = "facebook/bart-large-cnn"
    bart_tokenizer = BartTokenizer.from_pretrained(BART_MODEL_NAME, use_fast=True)
    bart_model = BartForConditionalGeneration.from_pretrained(BART_MODEL_NAME)
except Exception as e:
    logger.error(f"Failed to load BART model: {str(e)}")
    raise

# Cache question-answering pipeline
try:
    logger.info("Loading question-answering model")
    qa_pipeline = pipeline("question-answering", model="deepset/roberta-base-squad2")
except Exception as e:
    logger.error(f"Failed to load QA model: {str(e)}")
    raise

def clear_temp_folder():
    """Delete all files and subdirectories in the temp folder."""
    if os.path.exists(TEMP_DIR):
        try:
            shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR)
            logger.info("Cleared and recreated temp folder")
        except Exception as e:
            logger.error(f"Error clearing temp folder: {e}")
    else:
        os.makedirs(TEMP_DIR)
        logger.info("Created temp folder")

def remove_temp_files(*file_paths):
    """Remove specified temporary files."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Removed file: {file_path}")
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")

def get_video_duration(url):
    """Get the duration of the YouTube video in seconds."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'noplaylist': True,
        'retries': 5,
        'fragment_retries': 5,
        'proxy': '',  # Set to 'http://proxy:port' if needed
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            duration = info.get('duration', 0)
            logger.info(f"Video duration: {duration} seconds")
            return duration
    except Exception as e:
        logger.error(f"Error getting video duration: {e}")
        return 0

def transcribe_audio(audio_file):
    """Transcribe audio file using OpenAI Whisper, splitting by pauses."""
    try:
        if not os.path.exists(audio_file):
            logger.error(f"Audio file does not exist: {audio_file}")
            return "Error: Audio file not found"
        file_size = os.path.getsize(audio_file)
        if file_size < 1000:
            logger.error(f"Audio file is too small: {file_size} bytes")
            return "Error: Audio file is empty or corrupted"

        logger.info(f"Loading Whisper model for {audio_file}")
        model = whisper.load_model("small.en")

        logger.info(f"Transcribing {audio_file}")
        result = model.transcribe(audio_file, language="en")
        
        transcription = ""
        for segment in result["segments"]:
            text = segment["text"].strip()
            if text:
                transcription += text + "\n"
        
        if not transcription:
            logger.error("No transcription produced")
            return "Error: No transcription produced"
        
        logger.info("Transcription completed successfully")
        logger.debug(f"Transcription snippet: {transcription[:1000]}...")
        return transcription

    except Exception as e:
        logger.error(f"Unexpected error in transcription: {str(e)}")
        return f"Error: {str(e)}"

def summarize_text(text):
    """Summarize the given text in simple language using BART model."""
    try:
        logger.info("Summarizing text with BART model")
        max_input_length = 1024
        chunks = [text[i:i+max_input_length] for i in range(0, len(text), max_input_length)]
        summary = ""

        for chunk in chunks:
            inputs = bart_tokenizer(
                chunk,
                max_length=1024,
                truncation=True,
                return_tensors="pt"
            )
            summary_ids = bart_model.generate(
                inputs["input_ids"],
                max_length=150,
                min_length=30,
                num_beams=4,
                early_stopping=True,
                length_penalty=1.0
            )
            chunk_summary = bart_tokenizer.decode(summary_ids[0], skip_special_tokens=True)
            summary += chunk_summary + " "
        
        logger.info("Summarization completed successfully")
        return summary.strip()

    except Exception as e:
        logger.error(f"Error in summarization: {str(e)}")
        return f"Error: Summarization failed - {str(e)}"

def answer_question(transcription, question):
    """Answer a question based on the transcription using QA model."""
    try:
        logger.info("Answering question with QA model")
        if not transcription or not question:
            return "Error: Transcription or question is empty"
        
        # Limit context to 3000 characters to include early content
        context = transcription[:3000]
        result = qa_pipeline(question=question, context=context)
        answer = result['answer']
        score = result['score']
        
        logger.info(f"Question answered successfully: {answer}, score: {score}")
        if score < 0.1:
            logger.warning(f"Low confidence score: {score}")
            return f"Answer: {answer} (Note: Low confidence in answer)"
        
        return f"Answer: {answer}"

    except Exception as e:
        logger.error(f"Error in question answering: {str(e)}")
        return f"Error: Question answering failed - {str(e)}"

@app.route('/')
def index():
    logger.info("Accessing index route")
    return render_template('index.html')

@app.route('/transcribe')
def transcribe():
    logger.info("Accessing transcribe route")
    try:
        return render_template('transcribe.html')
    except Exception as e:
        logger.error(f"Error rendering transcribe.html: {e}")
        return f"Error: Could not render template - {str(e)}", 500

@app.route('/summarize')
def summarize():
    logger.info("Accessing summarize route")
    return render_template('summarize.html')

@app.route('/question')
def question():
    logger.info("Accessing question route")
    return render_template('question.html')

@app.route('/get_video_info', methods=['POST'])
def get_video_info():
    logger.info("Accessing get_video_info route")
    data = request.get_json()
    url = data.get('url')
    if not url or 'youtube.com' not in url.lower() and 'youtu.be' not in url.lower():
        logger.warning(f"Invalid URL received: {url}")
        return jsonify({'error': 'Invalid or missing YouTube URL'}), 400
    
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'noplaylist': True,
            'retries': 5,
            'fragment_retries': 5,
            'proxy': '',  # Set to 'http://proxy:port' if needed
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            logger.info(f"Successfully extracted title: {info['title']}")
            return jsonify({'title': info['title']})
    except Exception as e:
        logger.error(f"Error in get_video_info: {str(e)}")
        return jsonify({'error': f"Failed to fetch video info: {str(e)}"}), 500

@app.route('/get_video_duration', methods=['POST'])
def get_video_duration_endpoint():
    logger.info("Accessing get_video_duration route")
    data = request.get_json()
    url = data.get('url')
    if not url or 'youtube.com' not in url.lower() and 'youtu.be' not in url.lower():
        logger.warning(f"Invalid URL received: {url}")
        return jsonify({'error': 'Invalid or missing YouTube URL'}), 400
    
    try:
        duration = get_video_duration(url)
        return jsonify({'duration': duration})
    except Exception as e:
        logger.error(f"Error in get_video_duration: {str(e)}")
        return jsonify({'error': f"Failed to fetch video duration: {str(e)}"}), 500

@app.route('/process', methods=['POST'])
def process_video():
    logger.info("Accessing process_video route")
    data = request.get_json()
    url = data.get('url')
    option = data.get('option', 'transcribe')
    question = data.get('question', '')

    if not url or 'youtube.com' not in url.lower() and 'youtu.be' not in url.lower():
        return jsonify({'output': 'Error: Invalid or missing YouTube URL'}), 400

    if option == 'question' and not question:
        return jsonify({'output': 'Error: Question is required for question-answering'}), 400

    clear_temp_folder()
    temp_mp3 = os.path.join(TEMP_DIR, 'temp_audio.mp3')

    try:
        duration = get_video_duration(url)
        if duration <= 0:
            duration = 1200

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(TEMP_DIR, 'temp_audio.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'postprocessor_args': ['-t', str(min(duration, 1200))],
            'verbose': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'retries': 5,
            'fragment_retries': 5,
            'proxy': '',  # Set to 'http://proxy:port' if needed
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if not os.path.exists(temp_mp3):
            raise Exception("Audio file not downloaded. Expected: " + temp_mp3)
        
        logger.info(f"Downloaded audio file: {temp_mp3}, size: {os.path.getsize(temp_mp3)} bytes")

        transcription = transcribe_audio(temp_mp3)
        if transcription.startswith("Error"):
            raise Exception(transcription)

        if option == 'transcribe':
            output = f"Transcription: {transcription}"
        elif option == 'summarize':
            output = summarize_text(transcription)
        elif option == 'question':
            output = answer_question(transcription, question)
        else:
            output = f"Error: Option '{option}' is not supported yet"

        return jsonify({'output': output})

    except Exception as e:
        logger.error(f"Error in process_video: {str(e)}")
        return jsonify({'output': f"Error: {str(e)}"}), 500

    finally:
        remove_temp_files(temp_mp3)

if __name__ == '__main__':
    app.run(debug=True)