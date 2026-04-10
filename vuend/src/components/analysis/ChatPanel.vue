<template>
  <section class="panel chat-panel">
    <div class="panel-header">
      <h3 class="panel-title">Chat</h3>
    </div>

    <div class="chat-body" ref="chatScroll">
      <template v-for="(msg, index) in store.chatHistory" :key="index">
        <div class="msg-time">{{ msg.time }}</div>

        <div :class="['msg-row', msg.role]">
          <div class="msg-bubble">
            <div v-if="msg.role === 'assistant' && msg.think" class="thought-container">
              <div class="thought-header" @click="toggleThink(msg)">
                <i :class="['bi', msg.showThink ? 'bi-chevron-down' : 'bi-chevron-right']"></i>
                <span class="thought-label">
                  {{ msg.showThink ? '收起思考过程' : '查看思考过程' }}
                </span>
              </div>
              <transition name="expand">
                <div v-if="msg.showThink" class="thought-content">
                  {{ msg.think }}
                </div>
              </transition>
            </div>

            <div 
              class="message-text" 
              v-html="msg.role === 'assistant' ? renderMarkdown(msg.reply) : msg.reply"
            ></div>
          </div>
        </div>

        <div 
          v-if="index === store.chatHistory.length - 1 && msg.role === 'assistant'" 
          class="suggestions-container"
        >
          <button 
            v-for="(q, qIdx) in store.suggestedQuestions" 
            :key="qIdx" 
            class="suggest-chip"
            @click="askSuggested(q)"
          >
            {{ q }}
          </button>
        </div>
      </template>
    </div>

    <div class="chat-footer">
      <div class="floating-input-card">
        <textarea 
          ref="textInput"
          v-model="userQuery" 
          placeholder="Ask me about the music..." 
          rows="1"
          @input="autoResize"
          @keydown.enter.exact.prevent="sendMessage"
        ></textarea>
        
        <div class="input-actions">
          <span class="source-count">{{ store.selectedMusicIds.length }} source(s) selected</span>
          <button class="circle-send-btn" @click="sendMessage">
            <i class="bi bi-arrow-up-short"></i>
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { ref, nextTick, onMounted, watch } from 'vue';
import { useAnalysisStore } from '@/stores/analysisStore';
import { marked } from 'marked'; // 用于渲染 Markdown

const store = useAnalysisStore();
const chatScroll = ref(null);
const textInput = ref(null);
const userQuery = ref('');

// Markdown 配置
marked.setOptions({ gfm: true, breaks: true });
const renderMarkdown = (text) => marked.parse(text || '');

// 切换思考块的展开状态
const toggleThink = (msg) => {
  // 如果消息里没有这个响应式属性，我们需要手动初始化它
  if (msg.showThink === undefined) {
    msg.showThink = true;
  } else {
    msg.showThink = !msg.showThink;
  }
};

// 自动滚动到底部
const scrollToBottom = async () => {
  await nextTick();
  if (chatScroll.value) {
    chatScroll.value.scrollTop = chatScroll.value.scrollHeight;
  }
};

watch(() => store.chatHistory.length, scrollToBottom, { deep: true });

const autoResize = () => {
  const el = textInput.value;
  if (!el) return;
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
};

const sendMessage = () => {
  const content = userQuery.value.trim();
  if (!content) return;

  store.askAI(content);
  
  userQuery.value = '';
  nextTick(() => { 
    if (textInput.value) textInput.value.style.height = 'auto'; 
  });
};

const askSuggested = (q) => {
  userQuery.value = q;
  sendMessage();
};

onMounted(scrollToBottom);
</script>

<style scoped>
/* 继承原有 Panel 样式 */
.panel { background: #ffffff; border-radius: 1.5rem; display: flex; flex-direction: column; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04); overflow: hidden; height: 100%; position: relative; flex: 2; min-width: 0; }
.panel-header { padding: 1.5rem 1.8rem; border-bottom: 1px solid #f1f3f5; }
.panel-title { margin: 0; font-size: 1.15rem; font-weight: 700; color: #1a1a1a; }

.chat-body { flex: 1; overflow-y: auto; padding: 1rem 3rem; scroll-behavior: smooth; }
.msg-time { font-size: 0.75rem; color: #94a3b8; text-align: center; margin: 2rem 0 0.8rem; }
.msg-row { display: flex; width: 100%; margin-bottom: 1.5rem; }
.msg-row.assistant { justify-content: flex-start; }
.msg-row.user { justify-content: flex-end; }

/* 气泡基础样式 */
.msg-bubble { max-width: 85%; padding: 1rem 1.5rem; border-radius: 1.2rem; font-size: 1rem; line-height: 1.6; position: relative; }
.assistant .msg-bubble { background-color: #ffffff; color: #1e293b; border: 1px solid #edf2f7; border-bottom-left-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.02); }
.user .msg-bubble { background-color: #f1f4ff; color: #2d3748; border-bottom-right-radius: 4px; }

/* ✨ 思维链样式 (Thought Section) */
.thought-container {
  margin-bottom: 0.8rem;
  background: #f8fafc;
  border-radius: 0.8rem;
  border-left: 3px solid #cbd5e1;
  overflow: hidden;
}

.thought-header {
  padding: 0.6rem 1rem;
  font-size: 0.85rem;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  user-select: none;
}
.thought-header:hover { background: #f1f5f9; color: #3b82f6; }

.thought-content {
  padding: 0 1rem 0.8rem 1rem;
  font-size: 0.85rem;
  color: #94a3b8;
  font-style: italic;
  line-height: 1.5;
  white-space: pre-wrap;
}

/* 消息文本正文 */
.message-text {
  word-break: break-word;
}
/* 适配 Markdown 的列表样式 */
.message-text :deep(ul), .message-text :deep(ol) {
  padding-left: 1.2rem;
  margin: 0.5rem 0;
}

/* 动画效果 */
.expand-enter-active, .expand-leave-active { transition: all 0.3s ease; max-height: 500px; }
.expand-enter-from, .expand-leave-to { opacity: 0; max-height: 0; }

/* 底部输入框样式保持不变 */
.suggestions-container { display: flex; flex-direction: column; align-items: flex-start; gap: 0.8rem; margin: 1rem 0 3.5rem 0; }
.suggest-chip { background: #F5F5F5; border: 1px solid #F5F5F5; padding: 0.8rem 1.2rem; border-radius: 1rem; font-size: 0.9rem; color: #475569; cursor: pointer; transition: 0.2s; margin-left: 1.2rem; }
.suggest-chip:hover { background: #EBEBEB; transform: translateX(5px); }

.chat-footer { padding: 1rem 3rem 2.5rem 3rem; flex-shrink: 0; }
.floating-input-card { background: #ffffff; border: 1.5px solid #e2e8f0; border-radius: 1.5rem; padding: 1.2rem; display: flex; flex-direction: column; min-height: 120px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
.floating-input-card textarea { flex: 1; border: none; outline: none; font-size: 1.1rem; padding: 0.5rem; resize: none; font-family: inherit; line-height: 1.6; }
.input-actions { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 0.8rem; }
.circle-send-btn { background: #3b82f6; color: white; border: none; width: 2.8rem; height: 2.8rem; border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center; }
</style>