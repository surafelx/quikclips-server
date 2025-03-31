import openai
import re
import logging
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set your OpenAI API key
openai.api_key = OPENAI_API_KEY

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def segment_transcript(transcript_path, timestamps_path, min_duration=30.0, refine_with_ai=False, prompt=""):
    logging.info(transcript_path, "hello")
    """
    Segments the transcript using timestamps and optionally refines with OpenAI.

    Args:
        transcript_path (str): File path to transcript.txt.
        timestamps_path (str): File path to timestamps.txt.
        min_duration (float): Minimum duration for each segment.
        refine_with_ai (bool): Whether to refine segments using OpenAI.
        prompt (str): Prompt for AI refinement.

    Returns:
        dict: Dictionary with segmented text or an error message.
    """
    try:
        
        # Read transcript and timestamps files
        if not os.path.exists(transcript_path) or not os.path.exists(timestamps_path):
            raise FileNotFoundError("Transcript or timestamps file not found.")

        with open(transcript_path, "r", encoding="utf-8") as transcript_file:
            transcript_text = transcript_file.read()

        with open(timestamps_path, "r", encoding="utf-8") as timestamps_file:
            timestamps_text = timestamps_file.read()

        print(transcript_path, transcript_text)
        def parse_timestamps(text):
            """Parses timestamps from text input."""
            timestamps = []
            try:
                lines = text.strip().split("\n")
                for line in lines:
                    if "Word:" in line and "Start:" in line and "End:" in line:
                        parts = line.split(", ")
                        word = parts[0].split(": ")[1]
                        start_time = float(parts[1].split(": ")[1].replace("s", ""))
                        end_time = float(parts[2].split(": ")[1].replace("s", ""))
                        timestamps.append((word, start_time, end_time))
                logging.info(f"Parsed {len(timestamps)} word-level timestamps.")
            except Exception as e:
                logging.error(f"Error parsing timestamps: {e}")
                raise ValueError(f"Timestamp parsing error: {e}")
            return timestamps

        def parse_transcript(text):
            """Parses the transcript text into chunks."""
            try:
                chunks = re.split(r"-{10,}", text)  # Splitting on '----------'
                transcripts = []

                for chunk in chunks:
                    lines = chunk.strip().split("\n")
                    if len(lines) > 1:
                        chunk_name = lines[0].strip()
                        text = " ".join(lines[1:]).strip()
                        transcripts.append((chunk_name, text))
                logging.info(f"Parsed {len(transcripts)} transcript chunks.")
            except Exception as e:
                logging.error(f"Error parsing transcript: {e}")
                raise ValueError(f"Transcript parsing error: {e}")
            return transcripts

        def align_timestamps_with_transcript(transcripts, timestamps):
            """Aligns timestamps with transcript text and creates segments."""
            try:
                logging.info("Aligning timestamps with transcript...")
                aligned_segments = []
                start_time = None
                end_time = None
                segment_text = ""

                for chunk_name, transcript in transcripts:
                    words = transcript.split()
                    for word, word_start, word_end in timestamps:
                        if word.lower() in [w.lower() for w in words]:
                            if start_time is None:
                                start_time = word_start
                            end_time = word_end
                            segment_text += f"{word} "

                            if end_time - start_time >= min_duration:
                                aligned_segments.append((segment_text.strip(), start_time, end_time))
                                segment_text = ""
                                start_time = None

                if segment_text and start_time is not None and end_time is not None:
                    aligned_segments.append((segment_text.strip(), start_time, end_time))

                logging.info(f"Aligned {len(aligned_segments)} segments.")
            except Exception as e:
                logging.error(f"Error aligning timestamps: {e}")
                raise ValueError(f"Alignment error: {e}")
            return aligned_segments

        def refine_segments_with_openai(segments):
            """Refines segmented text using OpenAI."""
            try:
                if not segments:
                    raise ValueError("No segments to refine.")

                logging.info("Refining segments with OpenAI GPT-4...")
                full_prompt = f"{prompt}\n\n"
                for text, start, end in segments:
                    full_prompt += f"Segment: {text}\nStart: {start}s, End: {end}s\n\n"

                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": full_prompt}
                    ],
                    max_tokens=1500,
                    temperature=0.7,
                )

                refined_output = response["choices"][0]["message"]["content"].strip()
                logging.info("Refinement complete.")
                return refined_output

            except Exception as e:
                logging.error(f"Error with OpenAI API: {e}")
                raise ValueError(f"OpenAI API error: {e}")

        # Process inputs
        timestamps = parse_timestamps(timestamps_text)
        transcripts = parse_transcript(transcript_text)

        if not timestamps or not transcripts:
            raise ValueError("Failed to process timestamps or transcript.")

        # Align and segment transcript
        aligned_segments = align_timestamps_with_transcript(transcripts, timestamps)

        # Optionally refine with OpenAI
        if refine_with_ai:
            refined_segments = refine_segments_with_openai(aligned_segments)
        else:
            refined_segments = aligned_segments

        return {"segments": refined_segments}

    except FileNotFoundError as fnf_error:
        logging.error(f"File error: {fnf_error}")
        return {"error": str(fnf_error)}

    except Exception as e:
        logging.error(f"Error in segment_transcript: {e}")
        return {"error": str(e)}
