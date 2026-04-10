<template>
  <aside class="panel studio-panel">
    <div class="panel-header">
      <h3 class="panel-title">Studio</h3>
      <i class="bi bi-layout-sidebar-reverse"></i>
    </div>

    <div class="tool-grid">
      <div 
        v-for="(tool, index) in tools" 
        :key="index" 
        :class="['tool-card', tool.colorClass]" 
        @click="openGenerator(tool.action)"
      >
        <div class="card-content">
          <i :class="tool.icon"></i>
          <span>{{ tool.label }}</span>
        </div>
        <i class="bi bi-chevron-right arrow-icon"></i>
      </div>
    </div>

    <hr class="section-divider" />

    <div class="records-area">
      <div class="records-list">
        <div v-for="record in store.genRecords" :key="record.id" class="record-row">
          <div class="record-main">
            <div class="record-icon-bg">
              <i :class="record.icon || 'bi bi-file-earmark-bar-graph'"></i>
            </div>
            <div class="record-meta">
              <p class="r-title">{{ record.title }}</p>
              <p class="r-date">{{ record.date }}</p>
            </div>
          </div>

          <div class="record-actions">
            <div v-if="record.status === 'loading'" class="loading-state">
              <i class="bi bi-arrow-repeat spin"></i>
            </div>
            <button v-else-if="record.status === 'ready'" class="view-btn" @click="handleView(record)">
              View
            </button>
            <button v-else class="more-btn">
              <i class="bi bi-three-dots-vertical"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <GenericModal 
      :is-open="isModalOpen" 
      :config="activeConfig"
      @close="isModalOpen = false"
      @confirm="executeTask"
    />

    <Transition name="fade">
      <div v-if="isDetailOpen && selectedRecord" class="detail-overlay" @click.self="isDetailOpen = false">
        <div class="detail-card">
          <div class="detail-header">
            <div class="header-label">
              <i :class="selectedRecord.icon"></i>
              <span>{{ getDetailTitle(selectedRecord) }}</span>
            </div>
            <button class="detail-close" @click="isDetailOpen = false"><i class="bi bi-x-lg"></i></button>
          </div>

          <div class="detail-body">
            <div v-if="selectedRecord.type === 'gen-music' && selectedRecord.resultUrl" class="player-wrapper">
              <audio controls :src="selectedRecord.resultUrl"></audio>
            </div>

            <div v-if="selectedRecord.type === 'gen-image' && selectedRecord.resultUrl" class="image-result-wrapper">
              <img :src="selectedRecord.resultUrl" class="res-image" alt="Generated visual" />
            </div>

            <div v-if="selectedRecord.type === 'analyze-music'" class="analysis-res-content">
              <div class="source-tag">
                <i class="bi bi-file-earmark-music"></i>
                Analyzed: <strong>{{ selectedRecord.details.fileName }}</strong>
              </div>
              <div class="text-results">{{ selectedRecord.analysisResult }}</div>
            </div>

            <div class="detail-info-group">
              <label>Configuration</label>
              <div class="tags-row">
                <span v-for="(v, k) in selectedRecord.details.options" :key="k" class="config-tag">
                  <strong>{{ k }}:</strong> {{ v }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <div class="studio-footer">
      <button class="add-note-btn">
        <i class="bi bi-journal-plus"></i>
        <span>Add note</span>
      </button>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useAnalysisStore } from '@/stores/analysisStore';
import { MODAL_CONFIGS } from '@/stores/modalConfigs'; 
import GenericModal from './GenericModal.vue';

const store = useAnalysisStore();

const isModalOpen = ref(false);
const activeConfig = ref(null);
const currentType = ref('');
const isDetailOpen = ref(false);
const selectedRecord = ref(null);

const currentSelectedSource = computed(() => {
  return store.musicSources.find(s => store.selectedMusicIds.includes(s.id));
});

const tools = [
  { label: 'Generate Music', icon: 'bi bi-music-note-beamed', action: 'gen-music', colorClass: 'color-1' },
  { label: 'Analyze Music', icon: 'bi bi-graph-up-arrow', action: 'analyze-music', colorClass: 'color-2' },
  { label: 'Generate Image', icon: 'bi bi-palette', action: 'gen-image', colorClass: 'color-3' },
  { label: 'Generate Report', icon: 'bi bi-file-earmark-text', action: 'gen-report', colorClass: 'color-4' }
];

const getDetailTitle = (record) => {
  if (record.type === 'analyze-music') return 'Music Analysis';
  if (record.type === 'gen-image') return 'Generated Image';
  return 'Result';
};

const openGenerator = (action) => {
  if (action === 'analyze-music') {
    if (!currentSelectedSource.value) {
      alert("Please select a completed music source from the left panel first.");
      return;
    }
  }
  
  const config = MODAL_CONFIGS[action];
  if (config) {
    activeConfig.value = config;
    currentType.value = action;
    isModalOpen.value = true;
  }
};

const executeTask = async (formData) => {
  const config = activeConfig.value;
  const type = currentType.value;
  isModalOpen.value = false;

  const tempId = Date.now();
  
  const newRecord = {
    id: tempId,
    title: type === 'analyze-music' ? `Report: ${currentSelectedSource.value.name}` : (formData.prompt?.substring(0, 15) || 'New Task'),
    date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    icon: config.icon,
    status: 'loading',
    type: type,
    details: { 
      prompt: formData.prompt || '', 
      options: { ...formData },
      fileName: type === 'analyze-music' ? currentSelectedSource.value.name : null 
    },
    resultUrl: null,
    analysisResult: null
  };
  
  store.genRecords.unshift(newRecord);

  try {
    if (type === 'analyze-music') {
      setTimeout(() => {
        const target = store.genRecords.find(r => r.id === tempId);
        if (target) {
          target.analysisResult = currentSelectedSource.value.analysis || "No analysis content found.";
          target.status = 'ready';
        }
      }, 800);
    } 
    else if (type === 'gen-music') {
      const params = new URLSearchParams({ prompt: formData.prompt });
      const response = await fetch(`http://106.13.186.155:9100/api/tango?${params.toString()}`);
      if (!response.ok) throw new Error();
      const blob = await response.blob();
      const target = store.genRecords.find(r => r.id === tempId);
      if (target) {
        target.resultUrl = URL.createObjectURL(blob);
        target.status = 'ready';
      }
    }
    // 新增图片生成逻辑
    else if (type === 'gen-image') {
      // 注意：这里需要根据你的实际 API 调整，以下为通用示例
      const response = await fetch('http://106.13.186.155:9100/api/generate-image', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });
      if (!response.ok) throw new Error();
      const blob = await response.blob();
      const target = store.genRecords.find(r => r.id === tempId);
      if (target) {
        target.resultUrl = URL.createObjectURL(blob);
        target.status = 'ready';
      }
    }
  } catch (e) {
    console.error("Task failed", e);
    const target = store.genRecords.find(r => r.id === tempId);
    if (target) target.status = 'error';
  }
};

const handleView = (record) => {
  selectedRecord.value = record;
  isDetailOpen.value = true;
};
</script>

<style scoped>
/* --- 1. 列表操作区样式 --- */
.record-actions { min-width: 45px; display: flex; justify-content: center; }
.view-btn { 
  background: #f1f5f9; border: 1px solid #e2e8f0; padding: 4px 12px; 
  border-radius: 6px; font-size: 0.75rem; font-weight: 600; cursor: pointer; color: #475569;
}
.view-btn:hover { background: #e2e8f0; }

.spin { display: inline-block; animation: rotate 1s linear infinite; color: #4338CA; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* --- 2. 详情预览 Overlay 样式 --- */
.detail-overlay {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(8px); display: flex; align-items: center; justify-content: center; z-index: 10000;
}
.detail-card {
  background: #fff; width: 440px; border-radius: 24px; padding: 2rem;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}
.detail-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.header-label { display: flex; align-items: center; gap: 10px; font-weight: 700; color: #1e293b; }
.header-label i { color: #4338ca; }
.detail-close { background: #f1f5f9; border: none; width: 32px; height: 32px; border-radius: 50%; cursor: pointer; color: #64748b; }

.player-wrapper { background: #f8fafc; padding: 1.5rem; border-radius: 16px; margin-bottom: 1.5rem; display: flex; justify-content: center; }
audio { width: 100%; height: 40px; }

/* 新增：图片结果样式 */
.image-result-wrapper { background: #f8fafc; padding: 1rem; border-radius: 16px; margin-bottom: 1.5rem; display: flex; justify-content: center; }
.res-image { max-width: 100%; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }

.analysis-res-content { background: #f8fafc; padding: 1.2rem; border-radius: 16px; margin-bottom: 1.5rem; border-left: 4px solid #854D0E; }
.source-tag { font-size: 0.8rem; color: #64748b; margin-bottom: 8px; display: flex; gap: 6px; }
.text-results { font-size: 0.95rem; color: #1e293b; line-height: 1.6; white-space: pre-wrap; }

.detail-info-group { margin-top: 1rem; }
.detail-info-group label { font-size: 0.7rem; font-weight: 800; color: #94a3b8; text-transform: uppercase; margin-bottom: 8px; display: block; }
.config-tag { background: #eef2ff; color: #4338ca; padding: 4px 10px; border-radius: 8px; font-size: 0.75rem; margin-right: 5px; margin-bottom: 5px; display: inline-block; }

/* 动画过渡 */
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s, transform 0.3s ease-out; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: scale(0.95); }

/* --- 3. 原有基础 CSS --- */
.panel { background: #ffffff; border-radius: 1.5rem; display: flex; flex-direction: column; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04); overflow: hidden; height: 100%; position: relative; }
.panel-header { padding: 1.5rem 1.8rem; border-bottom: 1px solid #f1f3f5; display: flex; justify-content: space-between; align-items: center; }
.panel-title { margin: 0; font-size: 1.15rem; font-weight: 700; color: #1a1a1a; }
.tool-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; padding: 1.5rem; }
.tool-card { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.2rem; border-radius: 1rem; cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; height: 60px; }
.tool-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
.card-content { display: flex; flex-direction: column; gap: 2px; }
.card-content i { font-size: 1.2rem; margin-bottom: 2px; }
.card-content span { font-size: 0.85rem; font-weight: 600; }
.arrow-icon { font-size: 0.8rem; opacity: 0.7; }
.color-1 { background-color: #EEF2FF; color: #4338CA; } 
.color-2 { background-color: #FEFCE8; color: #854D0E; } 
.color-3 { background-color: #F0FDF4; color: #166534; } 
.color-4 { background-color: #FEF2F2; color: #991B1B; } 
.section-divider { border: none; border-top: 1px solid #f1f3f5; margin: 0 1.5rem 1rem 1.5rem; }
.records-area { flex: 1; overflow-y: auto; padding: 0 1.5rem; }
.record-row { display: flex; justify-content: space-between; align-items: center; padding: 1rem 0.5rem; border-radius: 0.8rem; transition: background 0.2s; }
.record-row:hover { background-color: #f8fafc; }
.record-main { display: flex; align-items: center; gap: 1rem; }
.record-icon-bg { width: 36px; height: 36px; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 1.1rem; }
.record-meta .r-title { margin: 0; font-size: 0.95rem; font-weight: 600; color: #1e293b; line-height: 1.2; }
.record-meta .r-date { margin: 0; font-size: 0.75rem; color: #94a3b8; margin-top: 4px; }
.more-btn { background: none; border: none; color: #94a3b8; cursor: pointer; padding: 5px; }
.studio-footer { padding: 1.5rem; display: flex; justify-content: center; }
.add-note-btn { background: #000; color: #fff; border: none; padding: 0.8rem 1.5rem; border-radius: 2rem; display: flex; align-items: center; gap: 10px; cursor: pointer; font-weight: 600; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
</style>