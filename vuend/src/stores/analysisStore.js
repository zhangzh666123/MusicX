import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
const BASE_MEDIA_URL = 'http://106.13.186.155:9100/media/';

export const useAnalysisStore = defineStore('analysis', () => {
  // --- 1. Sources 数据与方法 (已适配左侧统一列表) ---
  
  // 统一存储所有来源（音乐文件 + 网页搜索）
  const musicSources = ref([
    { 
      id: 1, 
      type: 'file', // 新增类型标识
      name: '测试音乐.mp3', 
      status: 'completed', 
      timestamp: new Date(), // 新增时间戳
      analysis: 'This track is a melancholic, dreamy indie-pop piece...',
      url: `${BASE_MEDIA_URL}uploads/output.mp3`,
    },
  ])
  
  const selectedMusicIds = ref([]);

  // 文件上传逻辑 (适配版)
  const uploadAndAnalyze = async (file) => {
    const tempId = Date.now() + Math.floor(Math.random() * 1000)
    const newSource = {
      id: tempId,
      type: 'file',
      name: file.name,
      status: 'analyzing',
      analysis: null,
      timestamp: new Date(),
      // --- 新增：保存本地播放地址 ---
      url: URL.createObjectURL(file) 
    }
    // 插入到列表顶部
    musicSources.value.unshift(newSource)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://106.13.186.155:9100/api/analyze/', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()

      if (data.status === 'success') {
        const source = musicSources.value.find(s => s.id === tempId)
        if (source) {
          source.status = 'completed'
          source.analysis = data.analysis
        }
        // 保持你原有的 addMessage 逻辑
        addMessage('assistant', `我已完成对 **${file.name}** 的分析。您可以在左侧列表点击查看详情。`)
      }
    } catch (error) {
      console.error("分析失败:", error)
      const source = musicSources.value.find(s => s.id === tempId)
      if (source) source.status = 'error'
    }
  }

  // Web 搜索逻辑 (核心修改：将结果存入列表)
  const startResearch = async (query) => {
    isPlanning.value = true;
    
    // 1. 创建一个临时的 Web 搜索来源项
    const tempId = Date.now() + Math.floor(Math.random() * 1000)
    const newWebSource = {
      id: tempId,
      type: 'web', // 标记为网页搜索
      name: `搜索: ${query}`,
      status: 'analyzing',
      analysis: null, // 这里存储搜索回来的详细内容
      timestamp: new Date()
    }
    musicSources.value.unshift(newWebSource)

    try {
      const response = await fetch('http://106.13.186.155:9100/api/research/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query,
          use_web: isWebSearchEnabled.value,
          is_deep: researchMode.value === 'think'
        })
      });
      
      const data = await response.json();
      
      if (data.status === 'success') {
        // 2. 更新列表中对应的搜索项
        const source = musicSources.value.find(s => s.id === tempId)
        if (source) {
          source.status = 'completed'
          // 将 AI 的回复存入 analysis，以便在点击详情时查看
          source.analysis = data.reply 
        }
        
        // 3. 同时把简短回复加到聊天框 (可选)
        addMessage('assistant', `针对 "${query}" 的深度研究已完成，已作为新来源加入列表。`, data.think);
      }
    } catch (error) {
      console.error("搜索失败:", error)
      const source = musicSources.value.find(s => s.id === tempId)
      if (source) source.status = 'error'
    } finally {
      isPlanning.value = false;
    }
  };

  const isAllSelected = computed(() => 
    musicSources.value.length > 0 && 
    musicSources.value.filter(s => s.status === 'completed').length === selectedMusicIds.value.length
  )

  const toggleSelectAll = () => {
    const completedIds = musicSources.value.filter(s => s.status === 'completed').map(m => m.id)
    selectedMusicIds.value = isAllSelected.value ? [] : completedIds
  }

  // --- 2. Chat 数据与方法 (保持不变) ---
  const isWebSearchEnabled = ref(false)
  const researchMode = ref('fast') 
  const isPlanning = ref(false)    
  const chatHistory = ref([
    { role: 'assistant', think: '', reply: 'Zihao, I have indexed your music sources. How can I help with your analysis today?', time: '11:45 PM', showThink: false }
  ])

  const suggestedQuestions = ref([
    'Analyze the harmonic structure of these tracks',
    'What is the BPM of the selected sources?',
    'Generate a variation based on the melody',
    'Summarize the musical themes'
  ])

  const addMessage = (role, reply, think = '', time = '') => {
    const now = time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    chatHistory.value.push({ role, reply, think, time: now, showThink: false });
  };

  const askAI = async (userQuery) => {
    const selectedContext = musicSources.value
      .filter(s => selectedMusicIds.value.includes(s.id) && s.analysis)
      .map(s => `[${s.type === 'file' ? '音乐文件' : '搜索结果'}: ${s.name}]\n内容: ${s.analysis}`)
      .join('\n\n');

    addMessage('user', userQuery);

    try {
      const response = await fetch('http://106.13.186.155:9100/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: userQuery,
          context: selectedContext 
        })
      });
      
      const data = await response.json();
      if (data.status === 'success') {
        addMessage('assistant', data.reply, data.think);      
      }
    } catch (error) {
      addMessage('assistant', "抱歉，对话服务器出了点问题。");
    }
  };

  // --- 3. Studio 数据 (保持不变) ---
  // const genRecords = ref([
  //   { id: 1, title: 'PyCharm Chinese Language Configuration Guide', date: '1m ago', icon: 'bi bi-file-earmark-richtext' },
  // ])

  const genRecords = ref([
    { 
      id: 1, 
      title: 'PyCharm Chinese Language Configuration Guide', 
      date: '1m ago', 
      icon: 'bi bi-file-earmark-richtext' 
    },
    // --- 新增音频记录 1: 伴奏 ---
    { 
      id: 1712580001, // 建议使用较长 ID 或 Date.now()
      title: 'Instrumental Track (No Vocals)', 
      date: 'Just now', 
      icon: 'bi bi-music-note-list',
      type: 'gen-music',
      status: 'ready',
      resultUrl: '/no_vocals.mp3', // 对应 public/no_vocals.mp3
      details: { 
        prompt: 'Original track without vocals', 
        options: { "Source": "External", "Format": "MP3" } 
      }
    },
    // --- 新增音频记录 2: 人声 ---
    { 
      id: 1712580002, 
      title: 'Vocal Stem Extraction', 
      date: 'Just now', 
      icon: 'bi bi-mic-fill',
      type: 'gen-music',
      status: 'ready',
      resultUrl: '/vocals.mp3', // 对应 public/vocals.mp3
      details: { 
        prompt: 'Extracted clear vocals', 
        options: { "Isolation": "High", "SampleRate": "44.1kHz" } 
      }
    }
  ]);

  return {
    musicSources, selectedMusicIds, isAllSelected, 
    uploadAndAnalyze, toggleSelectAll,
    chatHistory, addMessage,
    suggestedQuestions,
    genRecords, askAI,
    isWebSearchEnabled, researchMode, isPlanning, startResearch
  }
})