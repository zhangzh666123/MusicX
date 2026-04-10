<template>
  <aside class="panel sources-panel">
    <div class="panel-header">
      <h3 class="panel-title">Sources</h3>
    </div>
    
    <div class="scroll-content">
      <div class="action-section">
        <button class="btn-add-source" @click="triggerFileUpload">
          <i class="bi bi-plus-lg"></i> Add sources
        </button>
        <input type="file" ref="fileInput" hidden multiple @change="handleFileChange" />

        <div class="web-search-box" :class="{ 'is-active': webSearchQuery }">
          <div class="search-input-row">
            <i class="bi bi-search"></i>
            <input type="text" v-model="webSearchQuery" placeholder="Search the web for new sources" @keydown.enter="handleWebSearch"/>
          </div>
          <div class="search-controls">
            <div :class="['pill-tag', { 'active-blue': store.isWebSearchEnabled }]" @click="store.isWebSearchEnabled = !store.isWebSearchEnabled">
              <i class="bi bi-globe"></i> Web 
            </div>
            <div :class="['pill-tag', { 'active-purple': store.researchMode === 'think' }]" @click="toggleResearchMode">
              <i :class="store.researchMode === 'fast' ? 'bi bi-stars' : 'bi bi-cpu'"></i> 
              {{ store.researchMode === 'fast' ? 'Fast' : 'Deep' }} 
            </div>
            <button class="search-go-btn" :class="{ 'can-send': webSearchQuery }" @click="handleWebSearch">
              <i class="bi bi-arrow-right"></i>
            </button>
          </div>
        </div>

        <transition name="slide-fade">
          <div v-if="store.isPlanning" class="planning-status-bar">
            <div class="planning-left">
              <div class="loading-spinner-purple"></div>
              <span class="planning-text">Planning...</span>
            </div>
            <button class="stop-planning-btn" @click="store.isPlanning = false">
              <i class="bi bi-stop-fill"></i>
            </button>
          </div>
        </transition>
      </div>

      <div class="selection-bar">
        <span class="selection-text">Select all sources</span>
        <label class="custom-cb">
          <input type="checkbox" @change="store.toggleSelectAll" :checked="store.isAllSelected" />
          <span class="checkmark"></span>
        </label>
      </div>

      <div class="music-list">
        <div 
          v-for="track in store.musicSources" :key="track.id" 
          class="source-item"
          :class="{ 'is-clickable': track.status === 'completed' }"
          @click="openDetails(track)"
        >
          <div class="source-info">
            <i v-if="track.type === 'file'" class="bi bi-file-earmark-music-fill file-icon"></i>
            <i v-else class="bi bi-globe2 web-icon"></i>
            <span class="file-name">{{ track.name }}</span>
          </div>

          <div class="status-action" @click.stop> 
            <div v-if="track.status === 'analyzing'" class="loading-spinner"></div>
            <label v-else-if="track.status === 'completed'" class="custom-cb">
              <input type="checkbox" v-model="store.selectedMusicIds" :value="track.id" />
              <span class="checkmark"></span>
            </label>
            <i v-else class="bi bi-exclamation-triangle text-danger"></i>
          </div>
        </div>
      </div>
    </div>

    <transition name="fade">
      <div v-if="activeDetail" class="detail-overlay" @click="closeDetails">
        <div class="detail-card" @click.stop>
          <div class="detail-header">
            <div class="header-title-row">
              <i v-if="activeDetail.type === 'file'" class="bi bi-music-note-list mr-2"></i>
              <h4>{{ activeDetail.name }}</h4>
            </div>
            <button class="close-btn" @click="closeDetails">
              <i class="bi bi-x-lg"></i>
            </button>
          </div>
          
          <div class="detail-body">
            <div v-if="activeDetail.type === 'file'" class="player-container">
              <div class="album-art-wrapper">
                <div class="album-art" :class="{ 'is-playing': isPlaying }">
                  <i class="bi bi-disc-fill disc-icon"></i>
                </div>
              </div>
              
              <div class="player-controls-ui">
                <div class="progress-area">
                  <span class="time-label">{{ formatTime(currentTime) }}</span>
                  <div class="progress-bar-container" @click="seekAudio">
                    <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
                  </div>
                  <span class="time-label">{{ formatTime(duration) }}</span>
                </div>
                
                <div class="btn-group">
                  <button class="sub-btn"><i class="bi bi-shuffle"></i></button>
                  <button class="main-btn"><i class="bi bi-skip-start-fill"></i></button>
                  <button class="play-btn-circle" @click="togglePlay">
                    <i :class="isPlaying ? 'bi bi-pause-fill' : 'bi bi-play-fill'"></i>
                  </button>
                  <button class="main-btn"><i class="bi bi-skip-end-fill"></i></button>
                  <button class="sub-btn"><i class="bi bi-repeat"></i></button>
                </div>
              </div>

              <audio 
                ref="audioTag" 
                :src="activeDetail.url"
                @timeupdate="onTimeUpdate"
                @loadedmetadata="onLoadedMetadata"
                @ended="isPlaying = false"
              ></audio>
            </div>

            <div v-else class="web-content-view">
              <div class="meta-tag">
                <span class="badge-purple">Web Research Results</span>
              </div>
              <div class="analysis-content">{{ activeDetail.analysis }}</div>
            </div>
          </div>
        </div>
      </div>
    </transition>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysisStore';

const store = useAnalysisStore();
const fileInput = ref(null);
const webSearchQuery = ref('');

// 播放器相关状态
const activeDetail = ref(null); 
const audioTag = ref(null);
const isPlaying = ref(false);
const currentTime = ref(0);
const duration = ref(0);

const progressPercent = computed(() => {
  return duration.value ? (currentTime.value / duration.value) * 100 : 0;
});

// 播放/暂停切换
const togglePlay = () => {
  if (!audioTag.value) return;
  if (isPlaying.value) {
    audioTag.value.pause();
  } else {
    audioTag.value.play();
  }
  isPlaying.value = !isPlaying.value;
};

// 格式化时间 00:00
const formatTime = (time) => {
  const min = Math.floor(time / 60);
  const sec = Math.floor(time % 60);
  return `${min}:${sec.toString().padStart(2, '0')}`;
};

// 音频进度更新
const onTimeUpdate = () => {
  currentTime.value = audioTag.value.currentTime;
};

// 音频元数据加载（获取总时长）
const onLoadedMetadata = () => {
  duration.value = audioTag.value.duration;
};

// 点击进度条跳转
const seekAudio = (e) => {
  const rect = e.target.getBoundingClientRect();
  const pos = (e.clientX - rect.left) / rect.width;
  audioTag.value.currentTime = pos * duration.value;
};

const openDetails = (item) => {
  if (item.status === 'completed') {
    activeDetail.value = item;
    isPlaying.value = false;
    currentTime.value = 0;
  }
};

const closeDetails = () => {
  if (audioTag.value) audioTag.value.pause();
  activeDetail.value = null;
  isPlaying.value = false;
};

const triggerFileUpload = () => { fileInput.value.click(); };
const handleFileChange = (e) => {
  const files = e.target.files;
  if (!files.length) return;
  Array.from(files).forEach(file => store.uploadAndAnalyze(file));
  e.target.value = ''; 
};
const toggleResearchMode = () => { store.researchMode = store.researchMode === 'fast' ? 'think' : 'fast'; };
const handleWebSearch = () => {
  const query = webSearchQuery.value.trim();
  if (!query) return;
  store.startResearch(query);
  webSearchQuery.value = ''; 
};
</script>

<style scoped>
/* --- 原有基础样式保留 --- */
.panel { background: #ffffff; border-radius: 1.5rem; display: flex; flex-direction: column; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04); overflow: hidden; height: 100%; position: relative; }
.panel-header { padding: 1.5rem 1.8rem; border-bottom: 1px solid #f1f3f5; display: flex; justify-content: space-between; align-items: center; }
.panel-title { margin: 0; font-size: 1.15rem; font-weight: 700; color: #1a1a1a; }
.scroll-content { flex: 1; overflow-y: auto; padding: 1.5rem; }
.btn-add-source { width: 100%; padding: 0.75rem; border: 1px solid #e2e8f0; background: #fff; border-radius: 2rem; cursor: pointer; font-weight: 600; display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 1rem;}
.btn-add-source:hover {background-color: #ECF2FC;}
.web-search-box { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 1.2rem; padding: 1rem; margin-bottom: 1.5rem; transition: all 0.3s; }
.web-search-box.is-active { border-color: #3b82f6; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
.search-input-row { display: flex; align-items: center; gap: 10px; margin-bottom: 0.8rem; }
.search-input-row i { color: #94a3b8; }
.search-input-row input { border: none; background: transparent; flex: 1; outline: none; font-size: 0.95rem; }
.search-controls { display: flex; gap: 8px; align-items: center; }
.pill-tag { background: #ffffff; border: 1px solid #e2e8f0; padding: 0.35rem 0.8rem; border-radius: 1rem; font-size: 0.75rem; cursor: pointer; transition: 0.2s; user-select: none; display: flex; align-items: center; gap: 5px; }
.pill-tag.active-blue { border-color: #3b82f6; color: #3b82f6; background: #eff6ff; }
.pill-tag.active-purple { border-color: #8b5cf6; color: #8b5cf6; background: #f5f3ff; }
.search-go-btn { margin-left: auto; background: #e2e8f0; border: none; width: 1.8rem; height: 1.8rem; border-radius: 50%; cursor: pointer; transition: 0.3s; color: #94a3b8; }
.search-go-btn.can-send { background: #3b82f6; color: white; }
.selection-bar { display: flex; justify-content: space-between; padding: 1rem 0; border-bottom: 1px solid #f1f5f9; font-weight: 600; color: #64748b; font-size: 0.9rem; }

/* --- 列表项样式 --- */
.source-item { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.8rem; margin: 0 -0.8rem; transition: 0.2s; border-radius: 0.8rem; }
.source-item.is-clickable { cursor: pointer; }
.source-item.is-clickable:hover { background: #f8fafc; }
.file-icon { color: #ef4444; margin-right: 10px; }
.web-icon { color: #3b82f6; margin-right: 10px; }

/* --- 播放器核心样式 (重头戏) --- */
.player-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0;
}

.album-art-wrapper {
  margin-bottom: 2.5rem;
}

.album-art {
  width: 160px;
  height: 160px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 20px 40px rgba(0,0,0,0.2);
  position: relative;
  border: 8px solid #f1f5f9;
}

/* 播放时的唱片旋转动画 */
.album-art.is-playing {
  animation: rotateDisc 8s linear infinite;
}

@keyframes rotateDisc {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.disc-icon {
  font-size: 4rem;
  color: #8b5cf6;
  opacity: 0.9;
}

.player-controls-ui { width: 100%; }

.progress-area {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 2rem;
}

.time-label { font-size: 0.7rem; color: #94a3b8; font-family: monospace; }

.progress-bar-container {
  flex: 1;
  height: 6px;
  background: #f1f5f9;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #8b5cf6;
  transition: width 0.3s;
}

.btn-group {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 24px;
}

.play-btn-circle {
  width: 54px;
  height: 54px;
  background: #8b5cf6;
  border: none;
  border-radius: 50%;
  color: white;
  font-size: 1.6rem;
  display: flex;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4);
  transition: 0.2s;
}

.play-btn-circle:hover { transform: scale(1.05); background: #7c3aed; }

.main-btn, .sub-btn { background: none; border: none; cursor: pointer; color: #64748b; transition: 0.2s; }
.main-btn { font-size: 1.4rem; color: #1e293b; }
.sub-btn { font-size: 1rem; color: #cbd5e1; }
.sub-btn:hover { color: #8b5cf6; }

/* --- 网页搜索详情样式 --- */
.meta-tag { margin-bottom: 1.2rem; }
.badge-purple { background: #f5f3ff; color: #8b5cf6; padding: 4px 10px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; border: 1px solid #ddd6fe; }
.analysis-content { line-height: 1.8; color: #334155; white-space: pre-wrap; font-size: 0.95rem; }

/* --- 通用 UI 样式 --- */
.detail-overlay {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: flex-end;
}

.detail-card {
  background: white;
  width: 100%;
  max-height: 85%;
  border-radius: 1.5rem 1.5rem 0 0;
  padding: 2rem;
  box-shadow: 0 -10px 40px rgba(0,0,0,0.1);
  display: flex;
  flex-direction: column;
}

.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }
.header-title-row { display: flex; align-items: center; }
.header-title-row h4 { margin: 0; font-size: 1.1rem; color: #1e293b; font-weight: 700; }
.close-btn { border: none; background: #f1f5f9; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; color: #64748b; }
.mr-2 { margin-right: 8px; }

/* --- 状态样式 --- */
.planning-status-bar { background: #f5f3ff; border: 1px solid #ddd6fe; border-radius: 1rem; padding: 0.8rem 1.2rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.loading-spinner-purple { width: 18px; height: 18px; border: 2px solid #ddd6fe; border-top: 2px solid #8b5cf6; border-radius: 50%; animation: spin 1s linear infinite; }
.loading-spinner { width: 18px; height: 18px; border: 2px solid #f3f3f3; border-top: 2px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }

@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.slide-fade-enter-active, .slide-fade-leave-active { transition: all 0.3s ease-out; }
.slide-fade-enter-from, .slide-fade-leave-to { transform: translateY(10px); opacity: 0; }

.custom-cb { position: relative; cursor: pointer; width: 20px; height: 20px; }
.custom-cb input { opacity: 0; width: 0; height: 0; }
.checkmark { position: absolute; top: 0; right: 0; height: 18px; width: 18px; background: #fff; border: 2px solid #000; border-radius: 4px; }
.custom-cb input:checked ~ .checkmark { background: #cbd5e1; border-color: #cbd5e1; }
.custom-cb input:checked ~ .checkmark:after { content: ""; position: absolute; display: block; left: 5px; top: 1px; width: 4px; height: 8px; border: solid #000; border-width: 0 2px 2px 0; transform: rotate(45deg); }
</style>