<template>
    <nav class="sidebar">
      <ul class="sidebar__menu">
        
        <div 
          class="sidebar__active-indicator" 
          :style="{ 
            opacity: activeIndex === -1 ? 0 : 1,
            transform: `translateY(${activeIndex * 100}%)` 
          }"
        ></div>
  
        <li 
          v-for="(item, index) in menuItems" 
          :key="index"
          class="sidebar__item"
        >
          <router-link 
            :to="item.path" 
            custom 
            v-slot="{ navigate }"
          >
            <a 
              href="#" 
              class="sidebar__link" 
              :class="{ 'active': activeIndex === index }"
              @click="navigate"
            >
              <span class="icon-wrapper">
                <i :class="item.icon"></i>
              </span>
              
              <span class="tooltip">{{ item.name }}</span>
            </a>
          </router-link>
        </li>
      </ul>
    </nav>
</template>

<script setup>
  import { computed } from 'vue';
  import { useRoute } from 'vue-router';
  
  const route = useRoute();
  
  const activeIndex = computed(() => {
    return menuItems.findIndex(item => item.path === route.path);
  });
  
  // ✅ 修改点：使用 Bootstrap Icons 类名
  const menuItems = [
    { 
      name: 'Home', 
      path: '/', 
      icon: 'bi bi-house' // 首页
    },
    { 
      name: 'environmentPanel', 
      path: '/environmentPanel', 
      icon: 'bi bi-chat-square-text' // 消息
    },
    { 
      name: 'Video', 
      path: '/finger',
      icon: 'bi bi-people' // 用户/客户
    },
    // { 
    //   name: 'Chat', 
    //   path: '/chat',
    //   icon: 'bi bi-star-half' // 项目/文件夹
    // },
    { 
      name: 'chat2', 
      path: '/chat2',
      icon: 'bi bi-camera-reels' // 电影/幻灯片 (或者用 bi-images, bi-magic)
    },
  ];
</script>

<style scoped>
  .sidebar {
    --item-height: 3.5rem;
    --sidebar-width: 5.5rem;
    --bg-color: #fff;
    
    /* 颜色定义 */
    --text-default: #6a778e;   /* 默认浅灰 */
    --text-hover: #2c3e50;     /* 悬浮深灰 */
    --text-active: #ffffff;    /* 激活纯白 */
    --indicator-color: #406ff3;/* 蓝色圆圈 */
    
    position: fixed;
    top: 1rem;
    left: 1rem;
    height: calc(100vh - 2rem);
    width: var(--sidebar-width);
    background: var(--bg-color);
    border-radius: 1rem;
    box-shadow: 0 0 40px rgba(0, 0, 0, 0.05);
    padding: 1rem 0;
    box-sizing: border-box;
    z-index: 1000;
  }
  
  .sidebar__menu {
    position: relative;
    list-style: none;
    padding: 0;
    margin: 0;
    display: flex;
    flex-direction: column;
  }
  
  /* 蓝色圆圈 */
  .sidebar__active-indicator {
    position: absolute;
    top: 0;
    left: 50%;
    width: 3.5rem;
    height: 3.5rem;
    background: var(--indicator-color);
    border-radius: 16px;
    margin-left: -1.75rem; 
    z-index: 0; /* 在底部 */
    pointer-events: none;
    transition: transform 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55), opacity 0.2s;
  }
  
  .sidebar__item {
    position: relative;
    z-index: 1; /* 在圆圈之上 */
    height: 3.5rem;
    display: flex;
    justify-content: center;
    align-items: center;
  }
  
  .sidebar__link {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 100%;
    height: 100%;
    text-decoration: none;
    
    /* === 1. 默认状态颜色 === */
    color: var(--text-default);
    
    transition: color 0.3s ease;
  }
  
  /* 图标容器 */
  .sidebar__link .icon-wrapper {
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  }
  
  /* ✅ 新增：控制 Bootstrap Icon 的大小 */
  .sidebar__link i {
    font-size: 1.5rem; /* 设置图标大小 */
    line-height: 1;    /* 防止行高影响布局 */
  }
  
  /* ============================
     核心颜色/交互逻辑
     ============================ */
  
  /* 2. 激活状态 (Active) - 强制变白 */
  /* Bootstrap Icon 是字体，会自动继承这里的 color */
  .sidebar__link.active {
    color: var(--text-active) !important;
  }
  
  /* 3. 悬浮状态 (Hover) - 未激活时 */
  /* 变深灰色 */
  .sidebar__link:not(.active):hover {
    color: var(--text-hover);
    background-color: transparent !important;

  }
  
  /* 4. 激活状态下的悬浮 */
  /* 保持白色 */
  .sidebar__link.active:hover {
    color: var(--text-active) !important;
    background-color: transparent !important;
  }
  
  /* 5. 任何状态下的悬浮 - 图标放大 */
  .sidebar__link:hover .icon-wrapper {
    transform: scale(1.25);
  }
  
  /* === Tooltip === */
  .sidebar__link .tooltip {
    position: absolute;
    left: 100%;
    top: 50%;
    transform: translateY(-50%) translateX(-20px);
    margin-left: 1rem;
    background: #fff;
    color: var(--indicator-color);
    padding: 0.5rem 1rem;
    border-radius: 0.5rem;
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
    white-space: nowrap;
    font-weight: 600;
    transition: all 0.3s ease;
  }
  
  .sidebar__link:hover .tooltip {
    opacity: 1;
    visibility: visible;
    transform: translateY(-50%) translateX(0);
  }
</style>