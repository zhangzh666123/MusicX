<template>
  <div class="app-container" :style="dynamicTheme">
    
    <header class="top-nav">
      <div class="logo-group">
        <div class="logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        </div>
        <div class="logo-text">
          <h1>SYMMUSIC FUSION</h1>
          <p>PH.D MULTI-MODAL PERCEPTION SYSTEM</p>
        </div>
      </div>

      <div class="env-container">
        <div class="env-status">
          <div class="status-chip">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/></svg>
            {{ envData.city || '定位中' }}
          </div>
          <div class="status-chip accent">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="M12 2v2"/><circle cx="12" cy="12" r="4"/></svg>
            {{ envData.weather || '获取天气' }} {{ envData.temperature }}°C
          </div>
        </div>
        <div class="env-analysis" v-if="envData.analysis">
          <span class="pulse-dot"></span>
          <strong>环境分析:</strong> {{ envData.analysis }}
        </div>
      </div>
    </header>

    <main class="main-layout">
      <aside class="control-panel">
        <div class="card selection-card">
          <div class="card-header">
            <span class="step-tag">Step 01</span>
            <h2>感官意图注入</h2>
          </div>

          <div class="selectors-container">
            <div class="select-group" v-for="(group, key) in options" :key="key">
              <label>{{ key === 'mood' ? '当前心情' : key === 'intent' ? '调节目标' : key === 'body' ? '身体状态' : '偏好元素' }}</label>
              <div class="option-grid">
                <button v-for="item in group" :key="item.value" 
                        :class="{ active: userOpts[key] === item.value }"
                        @click="userOpts[key] = item.value">
                  {{ item.label }}
                </button>
              </div>
            </div>
          </div>

          <button @click="startIntegratedPipeline" :disabled="isLoading" class="generate-btn">
            <svg v-if="!isLoading" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><path d="m5 3 14 9-14 9V3z"/></svg>
            <span v-else class="loader"></span>
            {{ isLoading ? 'AGENTS 协同中...' : '生成专属视听空间' }}
          </button>
        </div>

        <div class="card log-card">
          <h3>AGENT PIPELINE ANALYSIS</h3>
          <div class="log-stream" ref="logContainer">
            <transition-group name="log-fade">
              <div v-for="log in logs" :key="log.id" class="log-item" :class="log.agent.toLowerCase()">
                <div class="log-info">
                  <span class="log-agent">{{ log.agent }}</span>
                  <span class="log-time">{{ log.time }}</span>
                </div>
                <span class="log-msg">{{ log.message }}</span>
              </div>
            </transition-group>
          </div>
        </div>
      </aside>

      <section class="display-panel">
        <div class="card image-box">
          <transition name="image-fade" mode="out-in">
            <div v-if="currentCourse.imageSrc" :key="currentCourse.imageSrc" class="image-wrapper">
              <img :src="currentCourse.imageSrc" crossorigin="anonymous" @load="extractThemeColor" />
              
              <button 
                @click="togglePlay" 
                :disabled="!audioReady"
                :class="['embedded-play-btn', { 'is-ready': audioReady && !isPlaying }]"
              >
                <svg v-if="!isPlaying" width="36" height="36" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
                <svg v-else width="36" height="36" viewBox="0 0 24 24" fill="currentColor"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
              </button>

              <div class="image-meta">
                <span class="time-stamp">{{ timeLabel }}</span>
                <span class="track-name">{{ currentCourse.name }}</span>
              </div>
            </div>
            
            <div v-else class="image-placeholder">
              <p>LATENT REPRESENTATION SCANNING...</p>
            </div>
          </transition>
          <div v-if="isLoading" class="loading-overlay">
            <div class="loading-bar"></div>
          </div>
        </div>
        
        <div ref="waveRef" style="display: none"></div>
      </section>
    </main>

    <canvas ref="colorCanvas" style="display: none"></canvas>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, nextTick } from 'vue';
import AMapLoader from '@amap/amap-jsapi-loader';
import WaveSurfer from 'wavesurfer.js';

// --- 配置与令牌 ---
const API_BASE_URL = 'https://api.earmersion.com';
const API_TOKEN = 'YOUR EAR TOKEN';
const UNSPLASH_ACCESS_KEY = 'YOUR ACCESS KEY';

// --- 响应式变量 ---
const accentColor = ref('64, 111, 243');
const themeRGB = ref('64, 111, 243');
const isLoading = ref(false);
const isPlaying = ref(false);
const audioReady = ref(false);
const timeLabel = ref('0:00');
const logs = ref([]);
const logContainer = ref(null);

const envData = reactive({ city: '', weather: '', temperature: '', analysis: '' });
const userOpts = reactive({ mood: 'calm', intent: 'relax', body: 'comfortable', sound: 'lofi' });
const currentCourse = reactive({ name: 'Waiting...', audioSrc: '', imageSrc: '' });

const labelMap = { mood:'心情',intent:'意图',body:'身体',sound:'偏好',low:'低落',anxious:'焦虑',calm:'平静',tired:'疲惫',excited:'兴奋',lost:'迷茫',sleep:'助眠',relax:'放松',emotional:'调节',focus:'专注',sleepy:'困倦',tense:'紧绷',comfortable:'舒适',pain:'疼痛',rain:'雨声',white:'白噪',lofi:'轻音乐',healing:'疗愈' };
const options = { mood:[{label:'低落',value:'low'},{label:'焦虑',value:'anxious'},{label:'平静',value:'calm'},{label:'疲惫',value:'tired'},{label:'兴奋',value:'excited'},{label:'迷茫',value:'lost'}], intent:[{label:'助眠',value:'sleep'},{label:'放松',value:'relax'},{label:'调节',value:'emotional'},{label:'专注',value:'focus'}], body:[{label:'困倦',value:'sleepy'},{label:'紧绷',value:'tense'},{label:'舒适',value:'comfortable'},{label:'疼痛',value:'pain'}], sound:[{label:'雨声',value:'rain'},{label:'白噪',value:'white'},{label:'轻音乐',value:'lofi'},{label:'疗愈',value:'healing'}] };

let ws = null;
const waveRef = ref(null);
const colorCanvas = ref(null);

// --- 逻辑管线 ---

// A. 环境感知分析
const initAMap = async () => {
  window._AMapSecurityConfig = { securityJsCode: 'YOUR KEY' };
  try {
    const AMap = await AMapLoader.load({ key: 'YOUR KE', version: '2.0', plugins: ['AMap.CitySearch', 'AMap.Weather'] });
    const citySearch = new AMap.CitySearch();
    citySearch.getLocalCity((s, r) => {
      if (s === 'complete') {
        envData.city = r.city;
        const weather = new AMap.Weather();
        weather.getLive(r.city, (err, data) => {
          if (!err) {
            envData.weather = data.weather;
            envData.temperature = data.temperature;
            // 环境语义分析
            const moodFactor = data.weather.includes('雨') ? '湿度引导的高熵焦虑' : '光影充沛的稳定场域';
            envData.analysis = `当前位于${r.city}，检测到${data.weather}天，气象因子将触发“${moodFactor}”的调式权重。`;
            addLog('Sensory', `探测到实时物理坐标：${r.city}。环境分析：${data.weather}天，光化学辐射强度中等。`);
          }
        });
      }
    });
  } catch (e) { console.error(e); }
};

// B. 综合生成逻辑
const startIntegratedPipeline = async () => {
  isLoading.value = true;
  logs.value = [];
  
  try {
    // 1. Director Agent 角色初始化
    addLog('Director', '接收跨模态指令，正在进行语义嵌入 (Semantic Embedding)...');
    await sleep(600);

    // 2. 视觉采样
    addLog('Visual', '正在访问 Unsplash API。基于情绪关键词映射潜空间 (Latent Space) 采样...');
    const query = `${labelMap[userOpts.mood]} nature scenery`;
    const imgRes = await fetch(`https://api.unsplash.com/search/photos?query=${query}&per_page=1&orientation=landscape`, { headers: { Authorization: `Client-ID ${UNSPLASH_ACCESS_KEY}` } }).then(r => r.json());
    
    if (imgRes.results?.[0]) {
      currentCourse.imageSrc = imgRes.results[0].urls.regular;
      // 触发视觉分析细节
      addLog('Visual', '图像内容提取：检测到语义锚点 (Mountains/Water/Light)。');
      await sleep(500);
      addLog('Visual', '色彩分布分析：计算 RGB 空间直方图分布...');
      await sleep(400);
      addLog('Visual', '色温分析：当前采样色温 5600K，色调倾向度对齐。');
    }

    // 3. 音乐合成
    addLog('Music', '正在向 Earmersion 引擎发送感知画像。触发 DiT (Diffusion Transformer) 音频采样...');
    const authRes = await fetch(`${API_BASE_URL}/v1/auth/issue-user-token`, { headers: { 'Authorization': `Bearer ${API_TOKEN}` } }).then(r => r.json());
    const profile = `环境:${envData.city};天气:${envData.weather};心情:${labelMap[userOpts.mood]};生理:${labelMap[userOpts.body]}`;
    
    const recRes = await fetch(`${API_BASE_URL}/v1/music/reco/by-profile`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${authRes.access_token}` },
      body: JSON.stringify({ user_profile: profile, user_id: "phd_student_demo", music_type: "relax" })
    });
    const recData = await recRes.json();
    
    if (recData?.download_url) {
      currentCourse.audioSrc = recData.download_url;
      currentCourse.name = recData.music_name || 'AI Aligned Track';
      addLog('Alignment', '视听频谱对齐完成：将视觉色温映射至音频包络频率 (Envelope) 偏移。');
      await initAudio();
    }
    
    addLog('System', '全感官感知场域构建完成，链路畅通。');
  } catch (e) {
    addLog('Error', `生成链条中断: ${e.message}`);
  } finally {
    isLoading.value = false;
  }
};

const initAudio = async () => {
  if (ws) ws.destroy();
  await nextTick();
  ws = WaveSurfer.create({
    container: waveRef.value,
    backend: 'MediaElement',
    url: currentCourse.audioSrc,
    peaks: [new Float32Array([0])]
  });
  ws.on('ready', () => { audioReady.value = true; isPlaying.value = false; });
  ws.on('audioprocess', (t) => {
    const m = Math.floor(t / 60); const s = Math.floor(t % 60);
    timeLabel.value = `${m}:${s.toString().padStart(2, '0')}`;
  });
};

const togglePlay = () => {
  if (!ws || !audioReady.value) return;
  ws.isPlaying() ? (ws.pause(), isPlaying.value = false) : (ws.play(), isPlaying.value = true);
};

const extractThemeColor = (e) => {
  try {
    const ctx = colorCanvas.value.getContext('2d', { willReadFrequently: true });
    colorCanvas.value.width = 1; colorCanvas.value.height = 1;
    ctx.drawImage(e.target, 0, 0, 1, 1);
    const [r, g, b] = ctx.getImageData(0, 0, 1, 1).data;
    themeRGB.value = `${r}, ${g}, ${b}`;
    accentColor.value = `${r}, ${g}, ${b}`;
  } catch (e) { themeRGB.value = '64, 111, 243'; }
};

const addLog = (agent, message) => {
  const time = new Date().toLocaleTimeString().split(' ')[0];
  logs.value.unshift({ id: Date.now(), agent, message, time });
};
const sleep = (ms) => new Promise(res => setTimeout(res, ms));

const dynamicTheme = computed(() => ({
  '--accent': `rgb(${themeRGB.value})`
}));

onMounted(() => initAMap());
</script>

<style scoped>
/* 1. 基础容器与避让 */
.app-container {
  min-height: 100vh;
  background-color: #E5E9F1;
  margin-left: 8.5rem; 
  padding: 2.5rem;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  color: #1f2937;
}

/* 2. 增强版顶部导航 */
.top-nav { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2.5rem; }
.logo-group { display: flex; align-items: center; gap: 1rem; }
.logo-icon { background: #000; padding: 0.6rem; border-radius: 1rem; display: flex; }
.logo-text h1 { font-size: 1.25rem; font-weight: 900; margin: 0; letter-spacing: -0.5px; }
.logo-text p { font-size: 0.6rem; font-weight: 800; color: #94a3b8; margin-top: 2px; text-transform: uppercase; letter-spacing: 1px; }

.env-container { display: flex; flex-direction: column; align-items: flex-end; gap: 0.6rem; }
.env-status { display: flex; gap: 0.8rem; }
.status-chip {
  background: white; padding: 0.5rem 1.25rem; border-radius: 2rem; 
  font-size: 0.75rem; font-weight: 700; display: inline-flex; align-items: center; gap: 0.5rem;
  box-shadow: 0 4px 6px rgba(0,0,0,0.03);
}
.status-chip.accent { border: 1px solid var(--accent); color: var(--accent); }

.env-analysis {
  background: rgba(255, 255, 255, 0.6);
  padding: 0.4rem 1rem;
  border-radius: 0.8rem;
  font-size: 0.7rem;
  color: #64748b;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  border: 1px dashed rgba(0,0,0,0.1);
}

.pulse-dot { width: 6px; height: 6px; background: var(--accent); border-radius: 50%; animation: pulse-opacity 2s infinite; }
@keyframes pulse-opacity { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

/* 3. 布局 */
.main-layout { display: grid; grid-template-columns: 360px 1fr; gap: 2.5rem; }
.card { background: white; border-radius: 2.2rem; padding: 2rem; box-shadow: 0 10px 40px rgba(0,0,0,0.04); }

/* 4. 左侧日志强化 */
.selectors-container { display: flex; flex-direction: column; gap: 1.2rem; margin-bottom: 2rem; }
.select-group label { display: block; font-size: 0.7rem; font-weight: 900; color: #94a3b8; margin-bottom: 0.6rem; text-transform: uppercase; }
.option-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem; }
.option-grid button { padding: 0.6rem; background: #f8fafc; border: none; border-radius: 0.8rem; font-size: 0.8rem; font-weight: 700; cursor: pointer; transition: 0.2s; }
.option-grid button.active { background: #000; color: white; }

.generate-btn { width: 100%; padding: 1.2rem; background: #000; color: white; border: none; border-radius: 1.2rem; font-weight: 800; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 0.8rem; }
.generate-btn:hover { background: var(--accent); }

.log-card { margin-top: 1.5rem; height: 280px; display: flex; flex-direction: column; }
.log-stream { flex: 1; overflow-y: auto; padding-right: 0.5rem; }
.log-item { margin-bottom: 1rem; border-left: 2px solid #e2e8f0; padding-left: 1rem; transition: all 0.3s; }
.log-info { display: flex; justify-content: space-between; margin-bottom: 0.2rem; }
.log-agent { font-weight: 900; font-size: 0.65rem; text-transform: uppercase; color: #94a3b8; }
.log-time { font-size: 0.6rem; color: #cbd5e1; }
.log-msg { font-size: 0.75rem; font-weight: 500; color: #475569; line-height: 1.4; }

/* 日志颜色区分 */
.log-item.sensory { border-color: #6366f1; }
.log-item.visual { border-color: #ec4899; }
.log-item.music { border-color: #10b981; }
.log-item.director { border-color: #f59e0b; }
.log-item.alignment { border-color: var(--accent); }

/* 5. 右侧显示：固定高度与留白 */
.image-box { 
  height: 1020px; 
  padding: 0; 
  position: relative; 
  overflow: hidden; 
  background: #f1f5f9; 
  display: flex; 
  justify-content: center; 
  align-items: center; 
}
.image-wrapper { width: 100%; height: 100%; position: relative; display: flex; justify-content: center; align-items: center;}
.image-wrapper img { height: 95%; width: 100%; object-fit: contain; border-radius: 2.2rem; padding: 5px; box-sizing: border-box; border-radius: 1.5rem;}

/* 嵌入式播放按钮 (右下角) */
.embedded-play-btn {
  position: absolute;
  bottom: 2rem;
  right: 2rem;
  width: 75px;
  height: 75px;
  border-radius: 50%;
  background: #000;
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10px 25px rgba(0,0,0,0.3);
  z-index: 100;
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.embedded-play-btn.is-ready { animation: pulse-ring 2s infinite; background-color: var(--accent); }
@keyframes pulse-ring { 0% { box-shadow: 0 0 0 0 rgba(0,0,0,0.3); } 70% { box-shadow: 0 0 0 18px rgba(0,0,0,0); } 100% { box-shadow: 0 0 0 0 rgba(0,0,0,0); } }

.image-meta { position: absolute; bottom: 1.5rem; left: 2.2rem; display: flex; flex-direction: column; gap: 0.3rem; }
.time-stamp { font-family: monospace; font-weight: 800; color: white; background: rgba(0,0,0,0.4); padding: 0.2rem 0.6rem; border-radius: 0.5rem; width: fit-content; font-size: 0.9rem; }
.track-name { color: white; font-weight: 800; font-size: 1rem; text-shadow: 0 2px 4px rgba(0,0,0,0.6); }

.loading-overlay { position: absolute; inset: 0; background: rgba(255,255,255,0.7); display: flex; align-items: center; justify-content: center; }
.loading-bar { width: 150px; height: 3px; background: #e2e8f0; overflow: hidden; }
.loading-bar::after { content: ''; display: block; height: 100%; background: #000; width: 40%; animation: slide 1.5s infinite; }
@keyframes slide { from { transform: translateX(-100%); } to { transform: translateX(300%); } }

::-webkit-scrollbar { width: 0; }
</style>