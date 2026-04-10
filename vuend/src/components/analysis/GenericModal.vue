<template>
  <Transition name="modal-bounce">
    <div v-if="isOpen" class="modal-backdrop" @click.self="closeAll">
      <div class="modal-content">
        <div class="modal-header">
          <div class="header-info">
            <div class="header-icon"><i :class="config?.icon"></i></div>
            <div class="header-text">
              <h3>{{ config?.title }}</h3>
              <p>Customize your generation</p>
            </div>
          </div>
          <button class="close-btn" @click="closeAll"><i class="bi bi-x-lg"></i></button>
        </div>

        <div class="modal-body">
          <div v-for="field in config?.fields" :key="field.key" class="form-group">
            <label>{{ field.label }}</label>
            
            <textarea 
              v-if="field.type === 'textarea'" 
              v-model="formData[field.key]" 
              :placeholder="field.placeholder"
            ></textarea>
            
            <div v-else-if="field.type === 'select'" class="custom-dropdown">
              <div 
                class="dropdown-selected" 
                :class="{ 'is-active': activeDropdown === field.key }"
                @click="toggleDropdown(field.key)"
              >
                <span>{{ formData[field.key] || 'Select an option' }}</span>
                <i class="bi bi-chevron-down arrow-icon"></i>
              </div>
              
              <Transition name="dropdown-fade">
                <div v-if="activeDropdown === field.key" class="dropdown-list">
                  <div 
                    v-for="opt in field.options" 
                    :key="opt" 
                    class="dropdown-item"
                    :class="{ 'is-selected': formData[field.key] === opt }"
                    @click="selectOption(field.key, opt)"
                  >
                    {{ opt }}
                    <i v-if="formData[field.key] === opt" class="bi bi-check2"></i>
                  </div>
                </div>
              </Transition>
            </div>
            
            <input 
              v-else 
              :type="field.type" 
              v-model="formData[field.key]" 
              :placeholder="field.placeholder" 
            />
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn-secondary" @click="closeAll">Cancel</button>
          <button class="btn-primary" @click="handleConfirm">
            <span>Generate</span>
            <i class="bi bi-stars"></i>
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue';

const props = defineProps({ isOpen: Boolean, config: Object });
const emit = defineEmits(['close', 'confirm']);

const formData = ref({});
const activeDropdown = ref(null); // 控制当前哪个下拉框打开

// 初始化数据
watch(() => props.isOpen, (val) => {
  if (val && props.config) {
    const data = {};
    props.config.fields.forEach(f => data[f.key] = f.default || (f.options ? f.options[0] : ''));
    formData.value = data;
  }
});

const toggleDropdown = (key) => {
  activeDropdown.value = activeDropdown.value === key ? null : key;
};

const selectOption = (key, val) => {
  formData.value[key] = val;
  activeDropdown.value = null;
};

const closeAll = () => {
  activeDropdown.value = null;
  emit('close');
};

const handleConfirm = () => emit('confirm', { ...formData.value });

// 全局点击关闭下拉列表
const handleGlobalClick = (e) => {
  if (!e.target.closest('.custom-dropdown')) activeDropdown.value = null;
};
onMounted(() => window.addEventListener('click', handleGlobalClick));
onUnmounted(() => window.removeEventListener('click', handleGlobalClick));
</script>

<style scoped>
/* --- 基础布局 --- */
.modal-backdrop {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(0px); display: flex; align-items: center; justify-content: center; z-index: 9999;
}
.modal-content {
  background: #fff; width: 440px; border-radius: 28px; padding: 2rem;
  box-shadow: 0 25px 70px rgba(0,0,0,0.15); border: 1px solid rgba(255,255,255,0.7);
}

/* --- Header --- */
.modal-header { display: flex; justify-content: space-between; margin-bottom: 2rem; }
.header-info { display: flex; gap: 1rem; align-items: center; }
.header-icon { 
  width: 48px; height: 48px; background: #EEF2FF; border-radius: 16px; 
  display: flex; align-items: center; justify-content: center; color: #4338CA; font-size: 1.4rem;
}
.header-text h3 { margin: 0; font-size: 1.2rem; color: #1e293b; }
.header-text p { margin: 2px 0 0; font-size: 0.8rem; color: #94a3b8; }
.close-btn { 
  width: 32px; height: 32px; border-radius: 50%; border: none; background: #F1F5F9; 
  cursor: pointer; color: #64748B; transition: 0.2s;
}
.close-btn:hover { background: #fee2e2; color: #ef4444; transform: rotate(90deg); }

/* --- 表单主体 --- */
.modal-body { display: flex; flex-direction: column; gap: 1.2rem; }
.form-group { display: flex; flex-direction: column; gap: 6px; }
.form-group label { font-size: 0.8rem; font-weight: 600; color: #64748B; margin-left: 4px; }

input, textarea {
  padding: 0.8rem 1rem; border: 1.5px solid #E2E8F0; border-radius: 14px;
  background: #F8FAFC; outline: none; transition: 0.2s; font-size: 0.95rem;
}
input:focus, textarea:focus { border-color: #4338CA; background: #fff; box-shadow: 0 0 0 4px rgba(67, 56, 202, 0.08); }

/* --- 【核心】模拟下拉框样式 --- */
.custom-dropdown { position: relative; }
.dropdown-selected {
  padding: 0.8rem 1rem; border: 1.5px solid #E2E8F0; border-radius: 14px;
  background: #F8FAFC; display: flex; justify-content: space-between; align-items: center;
  cursor: pointer; transition: 0.2s;
}
.dropdown-selected:hover { border-color: #CBD5E1; }
.dropdown-selected.is-active { border-color: #4338CA; background: #fff; box-shadow: 0 0 0 4px rgba(67, 56, 202, 0.08); }
.dropdown-selected .arrow-icon { font-size: 0.75rem; color: #94A3B8; transition: 0.3s; }
.dropdown-selected.is-active .arrow-icon { transform: rotate(180deg); color: #4338CA; }

.dropdown-list {
  position: absolute; top: calc(100% + 8px); left: 0; width: 100%;
  background: #fff; border-radius: 16px; border: 1px solid #E2E8F0;
  box-shadow: 0 10px 25px rgba(0,0,0,0.1); overflow: hidden; z-index: 100;
  padding: 6px;
}
.dropdown-item {
  padding: 10px 12px; border-radius: 10px; cursor: pointer;
  display: flex; justify-content: space-between; align-items: center;
  font-size: 0.9rem; color: #475569; transition: 0.2s;
}
.dropdown-item:hover { background: #F1F5F9; color: #1E293B; }
.dropdown-item.is-selected { background: #EEF2FF; color: #4338CA; font-weight: 600; }

/* --- Footer --- */
.modal-footer { display: flex; justify-content: flex-end; gap: 0.8rem; margin-top: 2rem; }
.btn-secondary { padding: 0.7rem 1.4rem; border: none; border-radius: 14px; background: #F1F5F9; color: #64748B; font-weight: 600; cursor: pointer; }
.btn-primary { 
  padding: 0.7rem 1.8rem; border: none; border-radius: 14px; background: #0F172A; 
  color: #fff; font-weight: 600; cursor: pointer; display: flex; gap: 8px; align-items: center;
}
.btn-primary:hover { background: #1E293B; transform: translateY(-1px); box-shadow: 0 8px 20px rgba(0,0,0,0.15); }

/* --- 动画 --- */
.modal-bounce-enter-active, .modal-bounce-leave-active { transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.modal-bounce-enter-from, .modal-bounce-leave-to { opacity: 0; transform: scale(0.9) translateY(20px); }

.dropdown-fade-enter-active, .dropdown-fade-leave-active { transition: all 0.2s ease; }
.dropdown-fade-enter-from, .dropdown-fade-leave-to { opacity: 0; transform: translateY(-10px); }
</style>