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
            
            # 2. Transcribe with timestamps
            print("Step 2: Transcribing with timestamps...")
            result = self.whisper_model.transcribe(temp_audio, verbose=False)
            
            segments = []
            for s in result['segments']:
                segments.append({
                    "start": s['start'],
                    "end": s['end'],
                    "text": s['text'].strip()
                })
            
            print(f"📝 Transcribed {len(segments)} segments")
            
            # 3. Translate segments
            print(f"Step 3: Translating {len(segments)} segments to {target_lang}...")
            translator = GoogleTranslator(source='auto', target=target_lang)
            
            full_transcription = []
            full_translation = []
            
            for s in segments:
                translated = translator.translate(s['text'])
                s['translated_text'] = translated
                full_transcription.append(s['text'])
                full_translation.append(translated)
            
            # 4. Generate cloned voice audio (One by one to match timing)
            print("Step 4: Generating AI Voice Clone for each segment...")
            # For simplicity in this version, we still generate a full audio 
            # but we can now pass the segments back to the frontend for editing.
            output_audio_only = os.path.join(temp_dir, "translated_voice.wav")
            self.tts.tts_to_file(
                text=" ".join(full_translation),
                speaker_wav=temp_audio,
                language=target_lang,
                file_path=output_audio_only
            )
            
            # 5. Merge back
            print("Step 5: Merging audio and video...")
            new_voice = AudioFileClip(output_audio_only)
            final_video = video.set_audio(new_voice)
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            
            # Cleanup
            video.close()
            new_voice.close()
            # shutil.rmtree(temp_dir, ignore_errors=True) # Keep for a bit if debugging
            
            print(f"🎉 Job {job_id} completed successfully!")
            return {
                "status": "success",
                "segments": segments,
                "transcription": " ".join(full_transcription),
                "translation": " ".join(full_translation)
            }
            
        except Exception as e:
            print(f"❌ Error in process: {str(e)}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
