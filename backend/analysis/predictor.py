import torch
import threading
from transformers import AudioFlamingo3ForConditionalGeneration, AutoProcessor

class MusicAnalyzer:
    _instance = None
    _lock = threading.Lock() # 线程锁

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                print("🚀 [System] Starting to load Music-Flamingo to GPU...")
                model_id = "nvidia/music-flamingo-hf"
                cls._instance = super(MusicAnalyzer, cls).__new__(cls)
                
                cls.processor = AutoProcessor.from_pretrained(model_id)
                cls.model = AudioFlamingo3ForConditionalGeneration.from_pretrained(
                    model_id, 
                    device_map="cuda:0", 
                    trust_remote_code=True
                ).eval()
                print("✅ [System] Music-Flamingo loaded successfully.")
        return cls._instance

    def analyze(self, audio_path):
        # 确保推断过程也是线程安全的（同一时间只处理一个请求，防止显存崩溃）
        with self._lock:
            conversation = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this track in full detail - tell me the genre, tempo, and key, then dive into the instruments, production style, and overall mood it creates."},
                        {"type": "audio", "path": audio_path},
                    ],
                }
            ]

            inputs = self.processor.apply_chat_template(
                conversation,
                tokenize=True,
                add_generation_prompt=True,
                return_dict=True,
            ).to(self.model.device)
            
            inputs["input_features"] = inputs["input_features"].to(self.model.dtype)

            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_new_tokens=512)
            
            decoded = self.processor.batch_decode(
                outputs[:, inputs.input_ids.shape[1]:], 
                skip_special_tokens=True
            )
            return decoded[0]

# 供外部调用的接口
def get_analyzer():
    return MusicAnalyzer()