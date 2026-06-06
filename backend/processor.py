import os
import time
import torch
import whisper
import shutil
import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from TTS.api import TTS
from deep_translator import GoogleTranslator
from spleeter.separator import Separator

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
            
            # Initialize Spleeter for Vocal Removal
            self.separator = Separator('spleeter:2stems')
            print("✅ Spleeter Loaded")
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
            
            # 2. Vocal Removal (Keep background music)
            print("Step 2: Separating Vocals and Background Music...")
            self.separator.separate_to_file(temp_audio, temp_dir)
            # Spleeter creates a folder with the name of the file
            audio_name = os.path.splitext(os.path.basename(temp_audio))[0]
            vocals_path = os.path.join(temp_dir, audio_name, "vocals.wav")
            accompaniment_path = os.path.join(temp_dir, audio_name, "accompaniment.wav")
            
            # 3. Transcribe with timestamps
            print("Step 3: Transcribing with timestamps...")
            # Use vocals only for better transcription accuracy
            result = self.whisper_model.transcribe(vocals_path if os.path.exists(vocals_path) else temp_audio, verbose=False)
            
            segments = []
            for s in result['segments']:
                segments.append({
                    "start": s['start'],
                    "end": s['end'],
                    "text": s['text'].strip()
                })
            
            # 4. Translate segments
            print(f"Step 4: Translating {len(segments)} segments to {target_lang}...")
            translator = GoogleTranslator(source='auto', target=target_lang)
            full_translation = []
            
            for s in segments:
                translated = translator.translate(s['text'])
                s['translated_text'] = translated
                full_translation.append(translated)
            
            # 5. Generate cloned voice audio
            print("Step 5: Generating AI Voice Clone...")
            output_voice_path = os.path.join(temp_dir, "translated_voice.wav")
            self.tts.tts_to_file(
                text=" ".join(full_translation),
                speaker_wav=vocals_path if os.path.exists(vocals_path) else temp_audio,
                language=target_lang,
                file_path=output_voice_path
            )
            
            # 6. Merge Cloned Voice with Original Background Music
            print("Step 6: Merging AI Voice with Background Music...")
            new_voice = AudioFileClip(output_voice_path)
            
            if os.path.exists(accompaniment_path):
                bg_music = AudioFileClip(accompaniment_path).volumex(0.8) # Keep music at 80% volume
                final_audio = CompositeAudioClip([bg_music, new_voice])
            else:
                final_audio = new_voice
            
            # 7. Merge back to Video
            final_video = video.set_audio(final_audio)
            final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            
            # Cleanup
            video.close()
            new_voice.close()
            if 'bg_music' in locals(): bg_music.close()
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            return {
                "status": "success",
                "segments": segments,
                "transcription": result['text'],
                "translation": " ".join(full_translation)
            }
            
        except Exception as e:
            print(f"❌ Error in process: {str(e)}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
