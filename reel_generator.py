import whisper
import ffmpeg
from textblob import TextBlob
import os
import streamlit as st
import openai
import re
from dotenv import load_dotenv

# Load OpenAI API key
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')





# Step 1: Extract Audio from Video using FFmpeg
def extract_audio(video_path, output_audio_path):
    try:
        ffmpeg.input(video_path).output(output_audio_path).run()
        print(f"Audio extracted successfully to {output_audio_path}")
    except Exception as e:
        print(f"Error extracting audio: {e}")


# Step 2: Transcribe Audio to Text using OpenAI Whisper

def transcribe_audio(audio_path):
    try:
        # Load the Whisper model
        model = whisper.load_model("base")

        # Transcribe the audio
        result = model.transcribe(audio_path)

        # Check if there's any text in the transcription
        if not result['text'].strip():
            raise ValueError("The audio contains no recognizable speech, only music or silence.")

        # Create output text file name
        base_name = os.path.splitext(os.path.basename(audio_path))[0]
        output_file = f"{base_name}.txt"

        # Save the extracted text to a text file
        with open(output_file, 'w') as file:
            file.write(result['text'])

        return result['text'], result['segments']

    except FileNotFoundError:
        return "Error: The specified audio file does not exist."
    except ValueError as ve:
        return f"Error: {ve}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
def extract_sentiment_score(content):
    match = re.search(r"Sentiment score:\s*([-]?\d+(\.\d+)?)", content)
    if match:
        return float(match.group(1))
    else:
        raise ValueError("Sentiment score not found in the content")


def sentiment_to_score(sentiment_content):
    if "positive" in sentiment_content.lower():
        return 1.0
    elif "negative" in sentiment_content.lower():
        return -1.0
    elif "mixed" in sentiment_content.lower():
        return 0.0
    return 0.0


import openai

def analyze_text_importance(segments):
    important_segments = []
    buffer_time = 0.5
    importance_threshold = 0.5
    text_batch = []

    for segment in segments:
        text = segment['text']
        start_time = max(0, segment['start'] - buffer_time)
        end_time = segment['end'] + buffer_time
        text_batch.append((text, start_time, end_time))

    if text_batch:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": f"Analyze the sentiment of these texts: {text_batch}"}
                ]
                ,
                temperature=0.1
            )

            for idx, segment in enumerate(text_batch):
                text, start_time, end_time = segment
                sentiment_content = response['choices'][0]['message']['content'].strip()
                sentiment_score = sentiment_to_score(sentiment_content)

                word_count = len(text.split())
                importance_score = sentiment_score * word_count

                if text and importance_score > importance_threshold:
                    important_segments.append({
                        'text': text,
                        'start_time': start_time,
                        'end_time': end_time,
                        'importance_score': importance_score
                    })

        except Exception as e:
            print(f"Error during OpenAI API call: {e}")

    # Save important segments to a file
    with open("important_segments.txt", "w") as file:
        for segment in important_segments:
            file.write(f"Text: {segment['text']}\n")
            file.write(f"Start Time: {segment['start_time']}s\n")
            file.write(f"End Time: {segment['end_time']}s\n")
            file.write(f"Importance Score: {segment['importance_score']}\n")
            file.write("="*40 + "\n")  # Separator for readability

    return important_segments


# Step 4: Extract Video Segments Based on Timestamps

def extract_video_segment(video_path, start_time, end_time, output_path):
    try:
        duration = end_time - start_time
        ffmpeg.input(video_path, ss=start_time, t=duration).output(output_path).run()
        print(f"Segment extracted: {output_path}")
    except Exception as e:
        print(f"Error extracting video segment: {e}")

# Step 5: Compile Extracted Segments into 30-Second Reels
def compile_video_segments(segment_paths, output_video_path):
    # Sort the segment paths based on their timestamps
    segment_paths.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))  # Adjust the key based on how your segment filenames are structured

    with open('file_list.txt', 'w') as f:
        for segment in segment_paths:
            f.write(f"file '{segment}'\n")

    try:
        ffmpeg.input('file_list.txt', format='concat', safe=0).output(output_video_path, c='copy').run()
        print(f"Compiled reel created: {output_video_path}")
    except Exception as e:
        print(f"Error compiling videos: {e}")



# Full Process: Generate Multiple Reels from Important Segments
def generate_reels_from_important_segments(video_path, audio_path, top_n=5):
    extract_audio(video_path, audio_path)
    _, segments = transcribe_audio(audio_path)
    print("Transcription and timestamp extraction completed.")

    important_segments = analyze_text_importance(segments)
    important_segments.sort(key=lambda x: x['importance_score'], reverse=True)

    compiled_video_paths = []  # List to store compiled video paths
    for reel_index in range(3):
        top_segments = important_segments[reel_index * top_n:(reel_index + 1) * top_n]
        top_segments.sort(key=lambda x: x['start_time'])

        segment_paths = []
        for i, segment in enumerate(top_segments):
            start_time = segment['start_time']
            end_time = segment['end_time']
            output_path = f'reel_{reel_index + 1}_segment_{i + 1}.mp4'
            extract_video_segment(video_path, start_time, end_time, output_path)
            segment_paths.append(output_path)

        compiled_video_path = f'reel_{reel_index + 1}.mp4'
        compile_video_segments(segment_paths, compiled_video_path)
        compiled_video_paths.append(compiled_video_path)  # Add compiled path to the list

    return compiled_video_paths  # Return only compiled video paths



# Step 6: Save timestamps to a text file
def save_timestamps_to_file(segments, output_file):
    with open(output_file, 'w') as f:
        for segment in segments:
            f.write(f"Start: {segment['start_time']:.2f}, End: {segment['end_time']:.2f}\n")
    print(f"Timestamps saved to {output_file}")


# Streamlit Interface
def main():
    # Get the current directory
    current_directory = os.getcwd()

    # Loop through the range of segment numbers



    st.title("Video to Reel Summarizer")

    uploaded_file = st.file_uploader("Upload a video", type=["mp4"])

    if uploaded_file is not None:
        video_path = "uploaded_video.mp4"
        with open(video_path, mode="wb") as f:
            f.write(uploaded_file.read())
        st.success("Video uploaded successfully!")

        if st.button("Generate Reels"):


            audio_path = "extracted_audio.wav"
            st.info("Processing the video...")

            reel_segments = generate_reels_from_important_segments(video_path, audio_path)

            st.success("Reels generated!")

            for idx, (top_segments, segment_paths, compiled_video_path) in enumerate(reel_segments):
                with open(compiled_video_path, "rb") as file:
                    st.download_button(label=f"Download Reel {idx + 1}", data=file, file_name=f"reel_{idx + 1}.mp4")

                timestamps_file_path = f"important_timestamps_reel_{idx + 1}.txt"
                save_timestamps_to_file(top_segments, timestamps_file_path)

                with open(timestamps_file_path, "rb") as file:
                    st.download_button(label=f"Download Timestamps for Reel {idx + 1}", data=file,
                                       file_name=timestamps_file_path)

                for segment_path in segment_paths:
                    if os.path.exists(segment_path):
                        os.remove(segment_path)


if __name__ == '__main__':
    main()