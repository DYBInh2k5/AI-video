import os
import time
import torch
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from TTS.api import TTS
from deep_translator import GoogleTranslator

class VideoProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load Whisper model (Upgrade to 'medium' or 'large' for better accuracy)
        self.whisper_model = whisper.load_model("base")
        
        # Load XTTS model for voice cloning
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

    def process(self, video_path: str, target_lang: str, output_path: str):
        # 1. Extract audio from video
        temp_dir = "temp_processing"
        os.makedirs(temp_dir, exist_ok=True)
        job_id = os.path.basename(output_path).split('_')[0]
        
        temp_audio = os.path.join(temp_dir, f"{job_id}_voice_sample.wav")
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(temp_audio)
        
        # 2. Transcribe with timestamps for future subtitle support
        result = self.whisper_model.transcribe(temp_audio, verbose=False)
        full_text = result['text']
        
        # 3. Translate
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(full_text)
        
        # 4. Generate cloned voice audio
        output_audio = os.path.join(temp_dir, f"{job_id}_translated_audio.wav")
        
        # Use XTTS v2 for high-quality cloning
        self.tts.tts_to_file(
            text=translated_text,
            speaker_wav=temp_audio,
            language=target_lang,
            file_path=output_audio
        )
        
        # 5. Merge back (Enhancement: Keep original background music if possible)
        # For now, we replace the whole audio track. 
        # In the next update, we will add Vocal Remover to keep background music.
        new_audio = AudioFileClip(output_audio)
        
        # If audio is shorter/longer, we might need to adjust speed (not implemented yet)
        final_video = video.set_audio(new_audio)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)
        
        # Cleanup
        try:
            video.close()
            new_audio.close()
            if os.path.exists(temp_audio): os.remove(temp_audio)
            if os.path.exists(output_audio): os.remove(output_audio)
        except:
            pass
        
        return {
            "output_path": output_path,
            "transcription": full_text,
            "translation": translated_text
        }
