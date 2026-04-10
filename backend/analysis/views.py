

import json
import io
import torch
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from diffusers import DiffusionPipeline
from django.conf import settings
# --- 1. 全局初始化模型 (服务器启动时加载一次) ---
print("Loading SDXL model to GPU... Please wait.")
try:
    pipe = DiffusionPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0", 
        torch_dtype=torch.float16, 
        use_safetensors=True, 
        variant="fp16"
    )
    pipe.to("cuda")
    # 如果你的显存小于 8GB，建议开启以下优化：
    # pipe.enable_model_cpu_offload() 
    print("Model loaded successfully!")
except Exception as e:
    print(f"Failed to load model: {e}")
    pipe = None

@csrf_exempt
def generate_image(request):
    """
    处理本地图片生成请求
    """
    if request.method != "POST":
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    if pipe is None:
        return JsonResponse({"error": "Model not loaded on server"}, status=500)

    try:
        # 2. 解析前端 Prompt
        body = json.loads(request.body)
        user_prompt = body.get("prompt", "")
        # 前端传来的 resolution 可以在这里处理，SDXL 推荐 1024x1024
        size_str = body.get("size", "1024x1024") 
        width, height = map(int, size_str.split('x'))

        if not user_prompt:
            return JsonResponse({"error": "Prompt is required"}, status=400)

        # 3. 执行本地推理
        # 使用 torch.inference_mode() 节省内存并提速
        with torch.inference_mode():
            result = pipe(
                prompt=user_prompt, 
                width=width, 
                height=height,
                num_inference_steps=30 # 默认 50，30步通常效果也不错且更快
            )
            image = result.images[0]

        # 4. 将 PIL 图像转换为二进制流返回给前端
        buffer = io.BytesIO()
        image.save(buffer, format="PNG") # 保存为 PNG 格式
        
        return HttpResponse(buffer.getvalue(), content_type="image/png")

    except Exception as e:
        print(f"Inference error: {e}")
        return JsonResponse({"error": str(e)}, status=500)

from django.shortcuts import render

# Create your views here.
import torch
import numpy as np
import io
from django.http import HttpResponse, JsonResponse
from tangoflux import TangoFluxInference
from scipy.io import wavfile
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from .predictor import get_analyzer
import os
import logging
from django.utils.translation import gettext as _
import json
import requests
from openai import OpenAI
import re
import traceback
import dashscope # ✅ 使用原生 SDK
from dashscope import Generation

# 初始化客户端 (指向 DashScope 的 OpenAI 兼容接口)
MY_DASHSCOPE_API_KEY = "YOUR DashScope OpenAI"


# --- 配置 TensorRT-LLM 客户端 ---
# 这里的 8000 是你 Docker 映射出来的端口
TRT_LLM_BASE_URL = "http://127.0.0.1:8000/v1"
client = OpenAI(base_url=TRT_LLM_BASE_URL, api_key="tensorrt_llm")



# 全局加载模型（仅加载一次）
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"--- 模型初始化中 ({device})... ---")
model = TangoFluxInference(name='declare-lab/TangoFlux', device=device)

def generate_audio(request):
    prompt = request.GET.get('prompt', 'Wind blowing through trees')
    
    try:
        # 推理逻辑
        with torch.no_grad():
            audio = model.generate(prompt, steps=25, duration=10)
        
        # 格式转换
        audio_data = audio.detach().cpu().numpy().flatten()
        audio_data = np.clip(audio_data, -1.0, 1.0)
        audio_int16 = (audio_data * 32767).astype(np.int16)

        # 写入内存流
        buffer = io.BytesIO()
        wavfile.write(buffer, 44100, audio_int16)
        buffer.seek(0)

        return HttpResponse(buffer.read(), content_type="audio/wav")
    except Exception as e:
        return JsonResponse({"error": str(e)})
    



# 设置日志，方便在控制台看到推理进度
logger = logging.getLogger(__name__)

@csrf_exempt
def upload_and_analyze(request):
    """
    接收上传的音乐文件，并调用预加载的 Music-Flamingo 模型进行分析
    """
    if request.method == 'POST' and request.FILES.get('file'):
        audio_file = request.FILES['file']
        
        # 1. 保存文件
        # default_storage.save 会自动处理重名问题（如果重名会自动加后缀）
        try:
            file_name = default_storage.save(f'uploads/{audio_file.name}', audio_file)
            # 获取文件在服务器上的绝对路径
            full_path = default_storage.path(file_name)
            
            logger.info(f"--- File saved at: {full_path} ---")
            logger.info(f"--- Starting Analysis for {audio_file.name} ---")

            # 2. 获取已经加载好的模型单例并进行分析
            # 注意：这里的 get_analyzer() 不会重新加载模型，只是返回引用
            analyzer = get_analyzer()
            
            # 调用分析方法（内部已有线程锁，支持排队分析）
            analysis_result = analyzer.analyze(full_path)
            
            logger.info(f"--- Analysis Completed ---")

            return JsonResponse({
                'status': 'success',
                'file_name': audio_file.name,
                'analysis': analysis_result,
                'path': full_path
            })

        except Exception as e:
            logger.error(f"Analysis Error: {str(e)}")
            return JsonResponse({
                'status': 'error', 
                'message': f"Model inference failed: {str(e)}"
            }, status=500)
        finally:
            # 可选：如果不需要保留原始文件，可以在分析完后删除以节省服务器空间
            # if os.path.exists(full_path):
            #     os.remove(full_path)
            pass

    return JsonResponse({
        'status': 'failed', 
        'message': 'Please upload a valid audio file using POST.'
    }, status=400)



def parse_llm_response(raw_text):
    think_pattern = re.compile(r'(.*?)</think>', re.DOTALL)
    think_content = ""
    
    match = think_pattern.search(raw_text)
    if match:
        think_content = match.group(1).strip()
    
    # 移除思考部分，保留回复
    reply_content = think_pattern.sub('', raw_text).strip()
    
    return think_content, reply_content



@csrf_exempt
def chat_with_analysis(request):
    """
    基于 TensorRT-LLM 的对话接口
    接收参数: query (用户提问), context (由 Music-Flamingo 生成的分析文本)
    """
    if request.method == 'POST':
        try:
            # 1. 解析前端请求数据
            data = json.loads(request.body)
            user_query = data.get('query', '')
            music_context = data.get('context', '') # 这是你在 Pinia 中拼接的分析文本

            # 2. 动态获取当前容器加载的模型 ID (Nemotron-Nano)
            try:
                model_info = requests.get(f"{TRT_LLM_BASE_URL}/models", timeout=5).json()
                current_model = model_info["data"][0]["id"]
            except Exception as e:
                return JsonResponse({
                    'status': 'error', 
                    'message': f'无法连接到 TensorRT-LLM 服务，请检查 Docker 容器: {str(e)}'
                }, status=503)

            # 3. 构造 Prompt 
            # 将音乐分析作为“事实依据”喂给模型
            system_prompt = "你是一个专业的音乐分析助手，请基于提供的音乐分析背景，专业地回答用户的问题。"
            
            # 如果有背景信息，则拼接到 User 消息中
            full_prompt = f"【已知背景：音乐分析报告】\n{music_context}\n\n【用户提问】\n{user_query}" if music_context else user_query

            # 4. 调用本地 TensorRT-LLM 推理
            response = client.chat.completions.create(
                model=current_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.6,
                max_tokens=1024,
            )
            think, reply = parse_llm_response(response.choices[0].message.content)
            # 5. 返回结果给前端
            return JsonResponse({
                'status': 'success',
                'think': think,
                'reply': reply, 
                'model_used': current_model
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error', 
                'message': f'服务器内部错误: {str(e)}'
            }, status=500)

    return JsonResponse({'status': 'failed', 'message': '仅支持 POST 请求'}, status=400)



@csrf_exempt
def chat_research(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            query = data.get('query', '')
            use_web = data.get('use_web', False)
            is_deep = data.get('is_deep', False)

            print(f"🚀 正在调用 Qwen: {query} (Web={use_web}, Deep={is_deep})")

            # 2. ✅ 核心修复：直接在 call 方法里传入 api_key
            response = Generation.call(
                model='qwen-plus',
                messages=[
                    {'role': 'system', 'content': '你是一个专业的研究助手。'},
                    {'role': 'user', 'content': query}
                ],
                api_key=MY_DASHSCOPE_API_KEY, # 👈 显式传入，强制验证
                result_format='message',
                enable_search=use_web,
                enable_thinking=is_deep
            )

            # 3. 处理返回结果
            if response.status_code == 200:
                output = response.output
                msg_obj = output.choices[0].message
    
                # ✅ 修复：使用 .get() 而不是 getattr，这样找不到键时会返回空字符串
                reply = msg_obj.get('content', '')
                think = msg_obj.get('reasoning_content', '') # 如果不是 Deep 模式，这个键就不存在
                
                # 打印一下，看看是不是真的拿到了
                print(f"✅ 成功获取回复，长度: {len(reply)}")
                if think:
                    print(f"🧠 思考过程长度: {len(think)}")

                return JsonResponse({
                    'status': 'success',
                    'think': think,
                    'reply': reply,
                    'title': f"关于 '{query[:10]}' 的研究报告"
                })
            else:
                # 如果 API 返回了错误（比如欠费或流量超限）
                print(f"❌ DashScope API 报错: {response.code} - {response.message}")
                return JsonResponse({
                    'status': 'error',
                    'message': f"API Error: {response.message}"
                }, status=response.status_code)

        except Exception as e:
            print("❌ Django 视图崩溃:")
            traceback.print_exc() # 确保顶部 import traceback 了
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'failed'}, status=400)



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

@csrf_exempt  # 简便起见，跳过 CSRF 验证
def upload_snapshot(request):
    if request.method == 'POST' and request.FILES.get('file'):
        img_file = request.FILES['file']
        
        # 保持文件名（前端生成的随机名）或自定义
        file_path = os.path.join('snapshots', img_file.name)
        
        # 保存到 MEDIA_ROOT/snapshots/
        path = default_storage.save(file_path, ContentFile(img_file.read()))
        
        return JsonResponse({
            'status': 'success',
            'message': f'文件已保存至 {path}',
            'url': f'/media/{path}'
        })
    
    return JsonResponse({'status': 'error', 'message': '仅支持 POST 请求及文件上传'}, status=400)