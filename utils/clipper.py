import re
import os
import logging
import tempfile
from moviepy.editor import VideoFileClip

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_timestamps_from_text(text):
    """
    Extracts start and end times from the segment text.
    
    Parameters:
    - text: str, content of the segment file with timestamps.
    
    Returns:
    - List of tuples (start_time, end_time) in seconds.
    """
    time_pattern = r"Start:\s*(\d+\.\d+)s,\s*End:\s*(\d+\.\d+)s"
    return [(float(start), float(end)) for start, end in re.findall(time_pattern, text)]


def clip_video(input_video_path, segments, output_folder):
    """
    Clips the video based on segments and saves them.
    
    Parameters:
    - input_video_path: str, path to the video file.
    - segments: list of tuples (start_time, end_time).
    - output_folder: str, where to save clips.
    
    Returns:
    - List of output video file paths.
    """
    saved_files = []

    try:
        # Load video
        video = VideoFileClip(input_video_path)
        logging.info(f"Loaded video: {input_video_path}")

        os.makedirs(output_folder, exist_ok=True)  # Ensure folder exists

        for i, (start, end) in enumerate(segments):
            # Ensure start and end times are valid
            logging.info(f"Timestamps for segment {i+1}: start={start}, end={end}")
            if start is None or end is None:
                logging.error(f"Invalid timestamps for segment {i+1}: start={start}, end={end}")
                continue

            output_file = os.path.join(output_folder, f"segment_{i+1}_{start}-{end}.mp4")

            try: 
                # Create video clip
                logging.info(f"Making sure these exist: start={start}, end={end}")
                clip = video.subclip(start, end)
                clip.write_videofile(output_file, codec="libx264", audio_codec="aac")
            except Exception as e:
                logging.error(f"Error during video clipping: {e}")
            logging.info(f"Saved: {output_file}")
            saved_files.append(output_file)

    except Exception as e:
        logging.error(f"Error during video clipping: {e}")

    return saved_files


def clip_video_from_text(input_video_path, segment_data, output_folder):
    """
    Processes segment data, clips the video, and saves in the specified output folder.
    
    Parameters:
    - input_video_path: str, path to the video file.
    - segment_data: dict, containing a key 'segments' with a list of tuples
                    (segment_text, start_time, end_time).
    - output_folder: str, path to the folder where clips should be saved.
    
    Returns:
    - List of saved video file paths.
    """
    try:
        # Extract segments from the dictionary
        if isinstance(segment_data, dict) and 'segments' in segment_data:
            segments = segment_data['segments']
        else:
            raise ValueError("The dictionary does not contain 'segments' key")

        logging.info(f"Extracted {len(segments)} segments.")

        # Return the clips and save them to the specified output folder
        return clip_video(input_video_path, [(start, end) for _, start, end in segments], output_folder)

    except Exception as e:
        logging.error(f"Error processing segment data: {e}")
        return []
