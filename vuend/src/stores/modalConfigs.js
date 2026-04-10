export const MODAL_CONFIGS = {
    'gen-music': {
      title: 'Generate Music',
      icon: 'bi bi-music-note-beamed',
      api: '/api/tango',
      fields: [
        { key: 'prompt', label: 'Music Topic', type: 'textarea', placeholder: 'Describe the vibe...' },
        { key: 'style', label: 'Genre', type: 'select', options: ['Jazz', 'Lo-Fi', 'Pop', 'Techno'] }
      ]
    },
    'analyze-music': {
      title: 'Analyze Music',
      icon: 'bi bi-graph-up-arrow',
      api: '/api/analyze', // 你的分析接口地址
      fields: [
        { key: 'analysis_type', label: 'Analysis Type', type: 'select', options: ['Full Report', 'Tempo & Beat', 'Melody Analysis'] },
        { key: 'note', label: 'Additional Note', type: 'input', placeholder: 'Optional...' }
      ]
    },
    'gen-image': {
      title: 'Generate Image',
      icon: 'bi bi-palette',
      api: '/api/generate-image',
      fields: [
        { key: 'prompt', label: 'Visual Prompt', type: 'textarea', placeholder: 'What do you want to see?' },
        { key: 'size', label: 'Resolution', type: 'select', options: ['1024x1024', '1920x1080'] }
      ]
    },
    'gen-report': {
      title: 'Analyze & Report',
      icon: 'bi bi-file-earmark-text',
      api: '/api/report',
      fields: [
        { key: 'topic', label: 'Analysis Subject', type: 'input', placeholder: 'Report title...' }
      ]
    }
  };