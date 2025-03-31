import os
import logging
from google.cloud import speech
from pydub import AudioSegment
import ffmpeg
import tempfile
import shutil
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Setup logging
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'https://raw.githubusercontent.com/surafelx/quikclips-server/refs/heads/main/angular-argon-452914-f1-3f22392d66ed.json'
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Script started.")

def video_to_audio(video_file, audio_file):
    """Convert video to audio file."""
    try:
        logging.info(f"Converting video {video_file} to audio...")
        ffmpeg.input(video_file).output(audio_file).run()
        logging.info(f"Conversion successful! Audio saved as {audio_file}.")
    except Exception as e:
        logging.error(f"Error converting video to audio: {e}")
        exit(1)

def convert_to_mono(input_audio, output_audio):
    """Convert stereo audio to mono."""
    try:
        logging.info(f"Converting {input_audio} to mono...")
        audio = AudioSegment.from_wav(input_audio)
        audio = audio.set_channels(1)
        audio.export(output_audio, format="wav")
        logging.info(f"Audio converted to mono and saved as {output_audio}")
    except Exception as e:
        logging.error(f"Error converting to mono: {e}")
        exit(1)

def split_audio(audio_file, output_folder, chunk_duration_ms=50000):
    """Splits the audio file into smaller chunks."""
    logging.info("Loading audio file...")
    audio = AudioSegment.from_wav(audio_file)
    duration = len(audio)
    logging.info(f"Audio duration: {duration} ms")
    
    os.makedirs(output_folder, exist_ok=True)
    chunks = []
    
    for i in range(0, duration, chunk_duration_ms):
        chunk = audio[i:i + chunk_duration_ms]
        chunk_name = os.path.join(output_folder, f"chunk_{i // chunk_duration_ms}.wav")
        chunk.export(chunk_name, format="wav")
        logging.info(f"Exported {chunk_name}")
        chunks.append(chunk_name)
    
    return chunks

def transcribe_audio_chunk(chunk_file, transcript_file, timestamp_file):
    """Transcribes a chunk of audio and saves transcript and timestamps."""
    client = speech.SpeechClient()
    with open(chunk_file, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,
        language_code="en-US",
        enable_word_time_offsets=True,
    )

    try:
        logging.info(f"Transcribing {chunk_file}...")
        response = client.recognize(config=config, audio=audio)
        
        with open(transcript_file, 'a') as transcript:
            transcript.write(f"Transcription for {chunk_file}:\n")
            for result in response.results:
                transcript.write(result.alternatives[0].transcript + "\n")
            transcript.write("\n" + "-"*40 + "\n")

        with open(timestamp_file, 'a') as timestamps:
            timestamps.write(f"Timestamps for {chunk_file}:\n")
            for result in response.results:
                for word_info in result.alternatives[0].words:
                    start_time = word_info.start_time.total_seconds()
                    end_time = word_info.end_time.total_seconds()
                    word = word_info.word
                    timestamps.write(f"Word: {word}, Start: {start_time}s, End: {end_time}s\n")
            timestamps.write("\n" + "-"*40 + "\n")
    
        logging.info(f"Completed transcribing {chunk_file}.")
    except Exception as e:
        logging.error(f"An error occurred during transcription: {e}")

def transcribe_video(video_file, output_folder):
    """Converts video to audio, processes it, and transcribes it."""
    # Create a temporary directory in the root folder
   
    
    # Ensure the temp directory exists
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    audio_file = os.path.join(output_folder, "audio.wav")
    mono_audio_file = os.path.join(output_folder, "mono_audio.wav")
    transcript_file = os.path.join(output_folder, "transcription.txt")
    timestamp_file = os.path.join(output_folder, "timestamps.txt")
    
    # Clear the transcription and timestamp files before starting
    open(transcript_file, 'w').close()
    open(timestamp_file, 'w').close()

    # Convert video to audio
    video_to_audio(video_file, audio_file)

    # Convert audio to mono
    convert_to_mono(audio_file, mono_audio_file)

    # Split the audio into chunks
    chunks = split_audio(mono_audio_file, output_folder)
    
    # Transcribe each chunk
    for chunk in chunks:
        transcribe_audio_chunk(chunk, transcript_file, timestamp_file)
    
    logging.info("All chunks have been transcribed successfully!")
    return transcript_file, timestamp_file

