import os
import torch
import whisper
from moviepy.editor import VideoFileClip, AudioFileClip
from TTS.api import TTS
from deep_translator import GoogleTranslator

class VideoProcessor:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using device: {self.device}")
        
        # Load Whisper model
        self.whisper_model = whisper.load_model("base")
        
        # Load XTTS model for voice cloning
        # This will download about 2GB of model data on first run
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)

    def process(self, video_path: str, target_lang: str, output_path: str):
        # 1. Extract audio from video
        temp_dir = "temp_processing"
        os.makedirs(temp_dir, exist_ok=True)
        job_id = os.path.basename(output_path).split('_')[0]
        
        temp_audio = os.path.join(temp_dir, f"{job_id}_voice_sample.wav")
        video = VideoFileClip(video_path)
        video.audio.write_audiofile(temp_audio)
        
        # 2. Transcribe
        result = self.whisper_model.transcribe(temp_audio)
        
        # 3. Translate
        full_text = result['text']
        translated_text = GoogleTranslator(source='auto', target=target_lang).translate(full_text)
        
        # 4. Generate cloned voice audio
        output_audio = os.path.join(temp_dir, f"{job_id}_translated_audio.wav")
        self.tts.tts_to_file(
            text=translated_text,
            speaker_wav=temp_audio,
            language=target_lang,
            file_path=output_audio
        )
        
        # 5. Merge back
        new_audio = AudioFileClip(output_audio)
        final_video = video.set_audio(new_audio)
        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        
        # Cleanup
        try:
            if os.path.exists(temp_audio): os.remove(temp_audio)
            if os.path.exists(output_audio): os.remove(output_audio)
        except:
            pass
        
        return output_path
