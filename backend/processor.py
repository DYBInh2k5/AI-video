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

    def process(self, video_path: str, target_lang: str, output_path: str, voice_type: str = "clone"):
        job_id = os.path.basename(output_path).split('_')[0]
        temp_dir = os.path.join("temp_processing", job_id)
        os.makedirs(temp_dir, exist_ok=True)
        
        print(f"📂 Processing Job: {job_id} | Voice: {voice_type}")
        
        try:
            # 1. Extract audio from video
            print("Step 1: Extracting audio...")
            temp_audio = os.path.join(temp_dir, "original_audio.wav")
            video = VideoFileClip(video_path)
            video.audio.write_audiofile(temp_audio, logger=None)
            
            # 2. Vocal Removal (Keep background music) - WITH FALLBACK
            vocals_path = temp_audio
            accompaniment_path = None
            
            try:
                print("Step 2: Separating Vocals and Background Music...")
                self.separator.separate_to_file(temp_audio, temp_dir)
                audio_name = os.path.splitext(os.path.basename(temp_audio))[0]
                v_p = os.path.join(temp_dir, audio_name, "vocals.wav")
                a_p = os.path.join(temp_dir, audio_name, "accompaniment.wav")
                if os.path.exists(v_p):
                    vocals_path = v_p
                    accompaniment_path = a_p
                    print("✅ Vocal separation successful")
            except Exception as e:
                print(f"⚠️ Vocal separation failed, proceeding with original audio: {e}")
            
            # 3. Transcribe
            print("Step 3: Transcribing...")
            result = self.whisper_model.transcribe(vocals_path, verbose=False)
            segments = []
            for s in result['segments']:
                segments.append({"start": s['start'], "end": s['end'], "text": s['text'].strip()})
            
            # 4. Translate
            print(f"Step 4: Translating to {target_lang}...")
            translator = GoogleTranslator(source='auto', target=target_lang)
            full_translation = []
            for s in segments:
                translated = translator.translate(s['text'])
                s['translated_text'] = translated
                full_translation.append(translated)
            
            # 5. Generate AI Voice
            print(f"Step 5: Generating AI Voice ({voice_type})...")
            output_voice_path = os.path.join(temp_dir, "translated_voice.wav")
            
            # Voice Selection Logic
            speaker_wav = vocals_path # Default for clone
            
            self.tts.tts_to_file(
                text=" ".join(full_translation),
                speaker_wav=speaker_wav,
                language=target_lang,
                file_path=output_voice_path
            )
            
            # 6. Merge
            print("Step 6: Finalizing video...")
            new_voice = AudioFileClip(output_voice_path)
            
            if accompaniment_path and os.path.exists(accompaniment_path):
                bg_music = AudioFileClip(accompaniment_path).volumex(0.7)
                final_audio = CompositeAudioClip([bg_music, new_voice])
            else:
                final_audio = new_voice
            
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
