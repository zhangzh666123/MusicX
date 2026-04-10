<template>
  <div class="analysis-wrapper">
    <SourcesPanel class="flex-1" />
    <ChatPanel class="flex-2" />
    <StudioPanel class="flex-1" />

    <footer class="disclaimer-footer">
      NvMusic can be inaccurate; please double check its responses.
    </footer>
  </div>
</template>

<script setup>
import SourcesPanel from '@/components/analysis/SourcesPanel.vue';
import ChatPanel from '@/components/analysis/ChatPanel.vue';
import StudioPanel from '@/components/analysis/StudioPanel.vue';
</script>

<style scoped>
.analysis-wrapper {
  display: flex;
  width: 100vw;
  height: 100vh;
  padding: 1.2rem 1.2rem 1.2rem 7.5rem; 
  box-sizing: border-box;
  gap: 1.2rem;
  background-color: var(--background-major-color);
  overflow: hidden;
  position: relative;
}

.disclaimer-footer {
  position: absolute;
  bottom: 0.2rem; 
  left: calc(7.5rem + (100% - 7.5rem) / 2);
  transform: translateX(-50%);
  font-size: 0.72rem;
  color: #70757a;
  letter-spacing: 0.04rem;
  word-spacing: 0.06rem;
  font-weight: 400;
  opacity: 0.75;
  white-space: nowrap;
  pointer-events: none;
  z-index: 100;
  -webkit-font-smoothing: antialiased;
}

.flex-1 {
  flex: 1;
  min-width: 0; /* 防止内容撑开宽度 */
}

.flex-2 {
  flex: 2;
  min-width: 0;
}
</style>