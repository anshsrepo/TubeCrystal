TubeCrystal: AI-Powered YouTube Insights App

![Image](https://github.com/user-attachments/assets/79923ff3-5b87-4823-83d1-0f9e7f516a46)

![Image](https://github.com/user-attachments/assets/537466dd-886a-4fcf-a6a8-e9bd3d78999a)

![Image](https://github.com/user-attachments/assets/b063740e-8675-4103-aef3-69f560b65658)

![Image](https://github.com/user-attachments/assets/802e9324-5e25-4166-a7b0-e9647c034373)

![Image](https://github.com/user-attachments/assets/06ecebd3-2281-40e9-a082-a756292b9bf0)

![Image](https://github.com/user-attachments/assets/8092116d-9ca7-44e7-b382-caf564d84379)


TubeCrystal is a sophisticated web application that leverages artificial intelligence to process YouTube videos, providing transcription, summarization, and question-answering capabilities. Built with a focus on usability and performance, it features a dynamic user interface with modern animations and a responsive design.
Features

Transcription: Converts YouTube video audio to text using OpenAI's Whisper (small.en) model, supporting up to 20 minutes of content.
Summarization: Generates concise summaries of video transcripts with BART (facebook/bart-large-cnn).
Question-Answering: Answers user queries about video content using RoBERTa (deepset/roberta-base-squad2), e.g., identifying Python's print() function in tutorials.
Dynamic UI: Offers a sleek interface with GSAP animations, dark/light mode toggle, and floating crystal effects.

Installation
Prerequisites

Python 3.12
FFmpeg (for audio processing with yt-dlp)
Git

Steps

Clone the repository:git clone https://github.com/anshsrepo/TubeCrystal.git
cd TubeCrystal


Set up a virtual environment:py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1  # On Windows


Install dependencies:pip install --upgrade pip
pip install -r requirements.txt


Install FFmpeg:
Download from ffmpeg.org and add to PATH, or place in the project folder.
Verify with ffmpeg -version.



Usage

Run the application:python app.py


Open your browser and navigate to http://127.0.0.1:5000/.
Explore the homepage to access transcription, summarization, or question-answering options.
Transcription: Enter a YouTube URL on /transcribe to get the full transcript.
Summarization: Use /summarize for a concise summary.
Question-Answering: Go to /question, input a URL and question (e.g., "What is the first Python concept?"), and receive an answer.



Technologies

Backend: Flask
AI Models: Whisper (small.en), BART (facebook/bart-large-cnn), RoBERTa (deepset/roberta-base-squad2)
Video Processing: yt-dlp
Frontend: JavaScript, GSAP, CSS
Python: 3.12

Contributing
Contributions are welcome! Please fork the repository, create a feature branch, and submit a pull request with your changes. Ensure to update the requirements.txt if new dependencies are added.
License
This project is open-source under the MIT License. See the LICENSE file for details (add a LICENSE file if not present).
Contact
For questions or feedback, reach out to [your email or LinkedIn] (replace with your details).
