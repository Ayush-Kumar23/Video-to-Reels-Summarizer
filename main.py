import whisper
import ffmpeg
from textblob import TextBlob
import os
import openai  # Make sure to install the OpenAI Python package
from dotenv import load_dotenv

def configure():
    load_dotenv()

# Step 1: Extract Audio from Video using FFmpeg
def extract_audio(video_path, output_audio_path):
    try:
        ffmpeg.input(video_path).output(output_audio_path).run(overwrite_output=True)
        print(f"Audio extracted successfully to {output_audio_path}")
    except Exception as e:
        print(f"Error extracting audio: {e}")

# Step 2: Transcribe Audio to Text using OpenAI Whisper
def transcribe_audio(audio_path):
    model = whisper.load_model("base")  # You can choose a different model size if needed
    result = model.transcribe(audio_path)
    return result['text'], result['segments']

# Step 3: Analyze Text Segments for Importance
def analyze_text_importance(segments):
    important_segments = []
    for segment in segments:
        text = segment['text']
        start_time = segment['start']
        end_time = segment['end']
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity
        word_count = len(text.split())
        importance_score = sentiment_score * word_count
        if importance_score > 1.0:
            important_segments.append({
                'text': text,
                'start_time': start_time,
                'end_time': end_time,
                'importance_score': importance_score
            })
    return important_segments

# Step 4: Extract Video Segment Based on Timestamps
def extract_video_segment(video_path, start_time, end_time, output_path):
    try:
        duration = end_time - start_time
        if duration > 0:
            ffmpeg.input(video_path, ss=start_time, t=duration).output(output_path).run(overwrite_output=True)
            print(f"Segment extracted: {output_path}")
        else:
            print(f"Invalid segment duration: {duration} seconds.")
    except Exception as e:
        print(f"Error extracting video segment: {e}")

# Step 5: Compile Extracted Segments into 30-Second Reel
def compile_video_segments(segment_paths, output_video_path):
    with open('file_list.txt', 'w') as f:
        for segment in segment_paths:
            f.write(f"file '{segment}'\n")
    try:
        ffmpeg.input('file_list.txt', format='concat', safe=0).output(output_video_path, c='copy').run(overwrite_output=True)
        print(f"Compiled reel created: {output_video_path}")
        os.remove('file_list.txt')
    except Exception as e:
        print(f"Error compiling videos: {e}")

# Step 6: Validate Content Accuracy
def validate_video_content(segment_paths):
    for segment in segment_paths:
        if not os.path.exists(segment):
            print(f"Missing segment: {segment}")
        else:
            print(f"Segment {segment} exists and is valid.")

# Full Process: Generate Reel from Important Segments
def generate_reel_from_important_segments(video_path, top_n=5):
    audio_path = 'output_audio.wav'
    extract_audio(video_path, audio_path)
    _, segments = transcribe_audio(audio_path)
    print("Transcription and timestamp extraction completed.")
    important_segments = analyze_text_importance(segments)
    important_segments.sort(key=lambda x: x['importance_score'], reverse=True)
    top_segments = important_segments[:top_n]
    
    segment_paths = []
    for i, segment in enumerate(top_segments):
        start_time = segment['start_time']
        end_time = segment['end_time']
        output_path = f'segment_{i + 1}.mp4'
        extract_video_segment(video_path, start_time, end_time, output_path)
        segment_paths.append(output_path)

    compiled_video_path = 'compiled_reel.mp4'
    compile_video_segments(segment_paths, compiled_video_path)
    validate_video_content(segment_paths)

    # Cleanup
    if os.path.exists(audio_path):
        os.remove(audio_path)

# Example Usage
video_path = 'input2.mp4'
generate_reel_from_important_segments(video_path, top_n=5)
