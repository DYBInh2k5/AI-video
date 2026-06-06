import os
import time
import torch
import whisper
import shutil
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from TTS.api import TTS
from deep_translator import GoogleTranslator

class VideoProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"🚀 Initializing AI Models on {self.device}...")
        
        try:
            # Load Whisper model
            self.whisper_model = whisper.load_model("base")
            print("✅ Whisper Loaded")
            
            # Load XTTS model for voice cloning
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            print("✅ XTTS v2 Loaded")
        except Exception as e:
            print(f"❌ Error loading models: {e}")

    def process(self, video_path: str, target_lang: str, output_path: str):
        job_id = os.path.basename(output_path).split('_')[0]
        temp_dir = os.path.join("temp_processing", job_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        print(f"📂 Processing Job: {job_id}")
        
        try:
            # 1. Extract audio from video
            print("Step 1: Extracting audio...")
            temp_audio = os.path.join(temp_dir, "original_audio.wav")
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(temp_audio, logger=None)
            
            # 2. Transcribe
            print("Step 2: Transcribing...")
            result = self.whisper_model.transcribe(temp_audio, verbose=False)
            full_text = result['text']
            print(f"📝 Transcribed: {full_text[:50]}...")
            
            # 3. Translate
            print(f"Step 3: Translating to {target_lang}...")
            translated_text = GoogleTranslator(source='auto', target=target_lang).translate(full_text)
            print(f"🌐 Translated: {translated_text[:50]}...")
            
            # 4. Generate cloned voice audio
            print("Step 4: Generating AI Voice Clone...")
            output_audio_only = os.path.join(temp_dir, "translated_voice.wav")
            self.tts.tts_to_file(
                text=translated_text,
                speaker_wav=temp_audio,
                language=target_lang,
                file_path=output_audio_only
            )
            
            # 5. Merge back
            print("Step 5: Merging audio and video...")
            new_voice = AudioFileClip(output_audio_only)
            
            # Simple merge (Enhancement: Keep original video's audio at lower volume if requested)
            final_video = video.set_audio(new_voice)
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            
            # Cleanup
            video.close()
            new_voice.close()
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            print(f"🎉 Job {job_id} completed successfully!")
            return {
                "status": "success",
                "transcription": full_text,
                "translation": translated_text
            }
            
        except Exception as e:
            print(f"❌ Error in process: {str(e)}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
