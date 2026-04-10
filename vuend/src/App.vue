<template>
  <router-view :key="$route.fullPath"></router-view>
  <Navbar />
</template>

<script setup>
import Navbar from './components/NavBar.vue'

</script>



<style >

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
  height: 100%;
  overflow: hidden; /* 核心：强制隐藏所有滚动条 */
}

#app {
  width: 100%;
  height: 100%;
  overflow: hidden;
}

:root {
  --background-major-color: #eaeef6;       /* 核心蓝色 (滑块、高亮) */
}
</style>
