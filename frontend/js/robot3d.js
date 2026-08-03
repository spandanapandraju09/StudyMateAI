/**
 * StudyMate AI — Futuristic 3D Mascot Robot System (Three.js r128 Compatible)
 * Replaces the center 3D AI Cube with an interactive, animated 3D AI Robot.
 * Features:
 * - PBR Teal, Cyan, and Glossy Purple metallic materials with realistic specular lighting
 * - Smooth 60 FPS animation loop: Idle floating, gentle breathing, mouse head tracking, eye blinking, body sway, hand waving
 * - Thinking, talking, and happy state triggers
 * - Dynamic ground shadow mapping
 */

(function () {
  document.addEventListener('DOMContentLoaded', () => {
    // Delay initialization slightly to guarantee Three.js DOM readiness
    setTimeout(initRobotMascot, 50);
  });

  function initRobotMascot() {
    if (typeof THREE === 'undefined') {
      console.warn('[Robot3D] Three.js library not detected');
      return;
    }

    const cubeEl = document.getElementById('ai-cube');
    if (!cubeEl) return;

    // Check if robot container already exists to avoid duplicate instantiation
    if (document.getElementById('robot-3d-showcase')) return;

    const parent = cubeEl.parentElement;

    // Create 3D Robot container sitting precisely at the 50% 50% center of the pedestal platform
    const robotContainer = document.createElement('div');
    robotContainer.id = 'robot-3d-showcase';
    robotContainer.style.position = 'absolute';
    robotContainer.style.top = '50%';
    robotContainer.style.left = '50%';
    robotContainer.style.transform = 'translate(-50%, -50%)';
    robotContainer.style.width = '360px';
    robotContainer.style.height = '360px';
    robotContainer.style.zIndex = '5';
    robotContainer.style.cursor = 'pointer';

    // Hide cubeEl so the 3D Robot Mascot takes its exact place
    cubeEl.style.display = 'none';
    parent.appendChild(robotContainer);

    // Setup Three.js Scene for Robot
    const width = 360;
    const height = 360;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 0.35, 4.5);

    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true, powerPreference: 'high-performance' });
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      renderer.shadowMap.enabled = true;
      renderer.shadowMap.type = THREE.PCFSoftShadowMap;
      if (renderer.toneMapping !== undefined) {
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.2;
      }
      robotContainer.appendChild(renderer.domElement);
    } catch (e) {
      console.error('[Robot3D] WebGL initialization failed:', e);
      cubeEl.style.display = 'block';
      return;
    }

    // ── Lighting System ──
    const ambientLight = new THREE.AmbientLight(0x0f172a, 1.8);
    scene.add(ambientLight);

    const mainSpot = new THREE.DirectionalLight(0x00F0FF, 3.5);
    mainSpot.position.set(3, 5, 4);
    mainSpot.castShadow = true;
    mainSpot.shadow.mapSize.width = 1024;
    mainSpot.shadow.mapSize.height = 1024;
    scene.add(mainSpot);

    const purpleFill = new THREE.PointLight(0xA855F7, 4.0, 10);
    purpleFill.position.set(-3, -1, 3);
    scene.add(purpleFill);

    const pinkRim = new THREE.PointLight(0xFF5CE5, 3.0, 8);
    pinkRim.position.set(0, 3, -3);
    scene.add(pinkRim);

    // ── Materials ──
    const metallicTealMat = new THREE.MeshStandardMaterial({
      color: 0x06B6D4,
      metalness: 0.85,
      roughness: 0.2,
    });

    const glossyPurpleMat = new THREE.MeshStandardMaterial({
      color: 0x7C3AED,
      metalness: 0.7,
      roughness: 0.25,
    });

    const whiteArmourMat = new THREE.MeshStandardMaterial({
      color: 0xF8FAFC,
      metalness: 0.1,
      roughness: 0.3,
    });

    const cyanGlowMat = new THREE.MeshStandardMaterial({
      color: 0x00F0FF,
      emissive: 0x00F0FF,
      emissiveIntensity: 2.5,
      roughness: 0.1,
    });

    const eyeVisorMat = new THREE.MeshStandardMaterial({
      color: 0x030712,
      metalness: 0.9,
      roughness: 0.1,
      transparent: true,
      opacity: 0.9,
    });

    // ── Helper: Soft Radial Shadow Texture ──
    function createShadowCanvasTexture() {
      const canvas = document.createElement('canvas');
      canvas.width = 128;
      canvas.height = 128;
      const ctx = canvas.getContext('2d');
      const grad = ctx.createRadialGradient(64, 64, 0, 64, 64, 64);
      grad.addColorStop(0, 'rgba(0, 240, 255, 0.75)');
      grad.addColorStop(0.4, 'rgba(168, 85, 247, 0.35)');
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 128, 128);
      return new THREE.CanvasTexture(canvas);
    }

    // ── Robot Construction Group ──
    const robotGroup = new THREE.Group();
    scene.add(robotGroup);

    // 1. Robot Head & Helmet
    const headGroup = new THREE.Group();
    headGroup.position.set(0, 0.7, 0);

    // Head Base Outer Shell
    const headGeo = new THREE.SphereGeometry(0.5, 32, 32);
    headGeo.scale(1.1, 0.95, 1.0);
    const headMesh = new THREE.Mesh(headGeo, metallicTealMat);
    headMesh.castShadow = true;
    headGroup.add(headMesh);

    // Head Top Crest Plate
    const crestGeo = new THREE.BoxGeometry(0.3, 0.12, 0.6);
    const crestMesh = new THREE.Mesh(crestGeo, glossyPurpleMat);
    crestMesh.position.set(0, 0.46, -0.05);
    headGroup.add(crestMesh);

    // Antenna & Glowing Orb Tip
    const antennaStemGeo = new THREE.CylinderGeometry(0.02, 0.03, 0.3, 16);
    const antennaStem = new THREE.Mesh(antennaStemGeo, whiteArmourMat);
    antennaStem.position.set(0, 0.62, -0.05);
    headGroup.add(antennaStem);

    const antennaTipGeo = new THREE.SphereGeometry(0.08, 16, 16);
    const antennaTip = new THREE.Mesh(antennaTipGeo, cyanGlowMat);
    antennaTip.position.set(0, 0.78, -0.05);
    headGroup.add(antennaTip);

    const tipLight = new THREE.PointLight(0x00F0FF, 1.5, 2);
    tipLight.position.set(0, 0.78, -0.05);
    headGroup.add(tipLight);

    // Glass Visor
    const visorGeo = new THREE.SphereGeometry(0.44, 32, 16, 0, Math.PI * 2, 0, Math.PI * 0.45);
    visorGeo.rotateX(Math.PI / 2);
    const visorMesh = new THREE.Mesh(visorGeo, eyeVisorMat);
    visorMesh.position.set(0, 0.05, 0.08);
    headGroup.add(visorMesh);

    // Glowing Eyes (Three.js r128 Compatible: Cylinder Capsule)
    const eyeGroup = new THREE.Group();
    eyeGroup.position.set(0, 0.05, 0.42);

    const eyeGeo = new THREE.CylinderGeometry(0.05, 0.05, 0.14, 16);
    eyeGeo.rotateZ(Math.PI / 2);

    const leftEye = new THREE.Mesh(eyeGeo, cyanGlowMat);
    leftEye.position.set(-0.16, 0, 0);
    eyeGroup.add(leftEye);

    const rightEye = new THREE.Mesh(eyeGeo, cyanGlowMat);
    rightEye.position.set(0.16, 0, 0);
    eyeGroup.add(rightEye);

    headGroup.add(eyeGroup);

    // Headphones / Ears
    const earGeo = new THREE.CylinderGeometry(0.12, 0.12, 0.1, 32);
    earGeo.rotateZ(Math.PI / 2);

    const leftEar = new THREE.Mesh(earGeo, glossyPurpleMat);
    leftEar.position.set(-0.55, 0, 0);
    headGroup.add(leftEar);

    const rightEar = new THREE.Mesh(earGeo, glossyPurpleMat);
    rightEar.position.set(0.55, 0, 0);
    headGroup.add(rightEar);

    robotGroup.add(headGroup);

    // 2. Neck
    const neckGeo = new THREE.CylinderGeometry(0.15, 0.18, 0.15, 16);
    const neckMesh = new THREE.Mesh(neckGeo, whiteArmourMat);
    neckMesh.position.set(0, 0.28, 0);
    robotGroup.add(neckMesh);

    // 3. Torso / Body Chest
    const torsoGroup = new THREE.Group();
    torsoGroup.position.set(0, -0.2, 0);

    const chestGeo = new THREE.CylinderGeometry(0.48, 0.38, 0.75, 32);
    const chestMesh = new THREE.Mesh(chestGeo, metallicTealMat);
    chestMesh.castShadow = true;
    torsoGroup.add(chestMesh);

    // White Chest Armour Plate
    const armorGeo = new THREE.BoxGeometry(0.65, 0.45, 0.35);
    const armorMesh = new THREE.Mesh(armorGeo, whiteArmourMat);
    armorMesh.position.set(0, 0.08, 0.15);
    torsoGroup.add(armorMesh);

    // Glowing Arc Reactor Core (Chest Center)
    const coreRingGeo = new THREE.TorusGeometry(0.12, 0.03, 16, 32);
    const coreRing = new THREE.Mesh(coreRingGeo, glossyPurpleMat);
    coreRing.position.set(0, 0.08, 0.34);
    torsoGroup.add(coreRing);

    const coreLightGeo = new THREE.SphereGeometry(0.09, 16, 16);
    const coreLightMesh = new THREE.Mesh(coreLightGeo, cyanGlowMat);
    coreLightMesh.position.set(0, 0.08, 0.33);
    torsoGroup.add(coreLightMesh);

    const chestLight = new THREE.PointLight(0x00F0FF, 2.5, 3);
    chestLight.position.set(0, 0.08, 0.4);
    torsoGroup.add(chestLight);

    robotGroup.add(torsoGroup);

    // 4. Arms & Hands
    // Left Arm
    const leftArmGroup = new THREE.Group();
    leftArmGroup.position.set(-0.55, 0.05, 0);

    const shoulderGeo = new THREE.SphereGeometry(0.16, 16, 16);
    const leftShoulder = new THREE.Mesh(shoulderGeo, glossyPurpleMat);
    leftArmGroup.add(leftShoulder);

    const bicepGeo = new THREE.CylinderGeometry(0.09, 0.08, 0.35, 16);
    const leftBicep = new THREE.Mesh(bicepGeo, metallicTealMat);
    leftBicep.position.set(-0.08, -0.2, 0);
    leftArmGroup.add(leftBicep);

    const leftHandGeo = new THREE.SphereGeometry(0.11, 16, 16);
    const leftHand = new THREE.Mesh(leftHandGeo, whiteArmourMat);
    leftHand.position.set(-0.1, -0.42, 0);
    leftArmGroup.add(leftHand);

    robotGroup.add(leftArmGroup);

    // Right Arm (Waving / Pointing Arm)
    const rightArmGroup = new THREE.Group();
    rightArmGroup.position.set(0.55, 0.05, 0);

    const rightShoulder = new THREE.Mesh(shoulderGeo, glossyPurpleMat);
    rightArmGroup.add(rightShoulder);

    const rightBicep = new THREE.Mesh(bicepGeo, metallicTealMat);
    rightBicep.position.set(0.08, -0.2, 0);
    rightArmGroup.add(rightBicep);

    const rightHandGeo = new THREE.SphereGeometry(0.11, 16, 16);
    const rightHand = new THREE.Mesh(rightHandGeo, whiteArmourMat);
    rightHand.position.set(0.1, -0.42, 0);
    rightArmGroup.add(rightHand);

    robotGroup.add(rightArmGroup);

    // 5. Lower Body Floating Thruster Ring
    const thrusterGeo = new THREE.CylinderGeometry(0.35, 0.1, 0.3, 32);
    const thruster = new THREE.Mesh(thrusterGeo, glossyPurpleMat);
    thruster.position.set(0, -0.7, 0);
    robotGroup.add(thruster);

    const flameGeo = new THREE.ConeGeometry(0.2, 0.4, 32);
    flameGeo.rotateX(Math.PI);
    const flameMesh = new THREE.Mesh(flameGeo, cyanGlowMat);
    flameMesh.position.set(0, -0.95, 0);
    robotGroup.add(flameMesh);

    // 6. Ground Shadow Plane
    const shadowGeo = new THREE.PlaneGeometry(1.6, 1.6);
    const shadowTexture = createShadowCanvasTexture();
    const shadowMat = new THREE.MeshBasicMaterial({
      map: shadowTexture,
      transparent: true,
      opacity: 0.6,
      depthWrite: false,
    });
    const shadowPlane = new THREE.Mesh(shadowGeo, shadowMat);
    shadowPlane.rotation.x = -Math.PI / 2;
    shadowPlane.position.set(0, -1.3, 0);
    scene.add(shadowPlane);

    // ── Animation Variables ──
    let clock = new THREE.Clock();
    let mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    let blinkTimer = 0;
    let isBlinking = false;
    let waveTimer = 0;
    let isHovered = false;
    let robotState = 'idle';

    // Mouse Tracking Listener
    window.addEventListener('mousemove', (e) => {
      const rect = robotContainer.getBoundingClientRect();
      const cx = rect.left + rect.width / 2;
      const cy = rect.top + rect.height / 2;
      mouse.targetX = (e.clientX - cx) / (window.innerWidth / 2);
      mouse.targetY = (e.clientY - cy) / (window.innerHeight / 2);
    });

    // Hover Interaction
    robotContainer.addEventListener('mouseenter', () => { isHovered = true; });
    robotContainer.addEventListener('mouseleave', () => { isHovered = false; });

    // Custom Animation Triggers
    window.addEventListener('robot:thinking', () => { robotState = 'thinking'; setTimeout(() => robotState = 'idle', 3000); });
    window.addEventListener('robot:talking', () => { robotState = 'talking'; setTimeout(() => robotState = 'idle', 4000); });
    window.addEventListener('robot:happy', () => { robotState = 'happy'; setTimeout(() => robotState = 'idle', 2500); });

    // ── Main 60 FPS Render Loop ──
    function animate() {
      requestAnimationFrame(animate);

      const elapsedTime = clock.getElapsedTime();

      // Smooth mouse tracking interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.05;
      mouse.y += (mouse.targetY - mouse.y) * 0.05;

      // 1. Idle Floating (Smooth vertical sine wave)
      const floatOffsetY = Math.sin(elapsedTime * 1.8) * 0.12;
      robotGroup.position.y = floatOffsetY;

      // 2. Gentle Breathing (Torso scale pulse)
      const breathScale = 1 + Math.sin(elapsedTime * 2.5) * 0.02;
      torsoGroup.scale.set(breathScale, breathScale, breathScale);

      // 3. Body Sway
      robotGroup.rotation.z = Math.sin(elapsedTime * 1.2) * 0.04;
      robotGroup.rotation.y = Math.sin(elapsedTime * 0.8) * 0.08;

      // 4. Head Mouse Tracking
      headGroup.rotation.y = mouse.x * 0.6;
      headGroup.rotation.x = mouse.y * 0.4;

      // 5. Eye Blinking (Every 3.5 seconds)
      blinkTimer += 0.016;
      if (blinkTimer > 3.5) {
        isBlinking = true;
        blinkTimer = 0;
      }
      if (isBlinking) {
        eyeGroup.scale.y -= 0.2;
        if (eyeGroup.scale.y <= 0.1) {
          eyeGroup.scale.y = 0.1;
          isBlinking = false;
        }
      } else {
        eyeGroup.scale.y += (1 - eyeGroup.scale.y) * 0.2;
      }

      // 6. Glow Pulsing
      const glowPulse = 2.0 + Math.sin(elapsedTime * 4.0) * 0.8;
      cyanGlowMat.emissiveIntensity = glowPulse;
      tipLight.intensity = 1.2 + Math.sin(elapsedTime * 3) * 0.5;
      chestLight.intensity = 2.0 + Math.sin(elapsedTime * 5) * 0.8;

      // 7. Hand Waving & Action Gestures
      waveTimer += 0.016;
      if (waveTimer > 6.0 && robotState === 'idle') {
        rightArmGroup.rotation.z = Math.sin((elapsedTime - waveTimer) * 8) * 0.4 + 0.8;
        rightArmGroup.rotation.x = -0.4;
        if (waveTimer > 8.5) waveTimer = 0;
      } else if (robotState === 'thinking') {
        rightArmGroup.rotation.z = 1.4;
        rightArmGroup.rotation.x = 0.8;
        headGroup.rotation.z = -0.15;
      } else if (robotState === 'talking') {
        rightArmGroup.rotation.z = Math.sin(elapsedTime * 10) * 0.25 + 0.4;
        leftArmGroup.rotation.z = -Math.sin(elapsedTime * 10) * 0.25 - 0.4;
      } else if (robotState === 'happy') {
        robotGroup.position.y += Math.abs(Math.sin(elapsedTime * 12)) * 0.15;
        rightArmGroup.rotation.z = 1.2;
        leftArmGroup.rotation.z = -1.2;
      } else {
        rightArmGroup.rotation.z += (0 - rightArmGroup.rotation.z) * 0.05;
        rightArmGroup.rotation.x += (0 - rightArmGroup.rotation.x) * 0.05;
        leftArmGroup.rotation.z += (0 - leftArmGroup.rotation.z) * 0.05;
      }

      // 8. Ground Shadow Dynamics
      const shadowScale = 1 - floatOffsetY * 0.8;
      shadowPlane.scale.set(shadowScale, shadowScale, shadowScale);
      shadowMat.opacity = 0.6 - floatOffsetY * 0.3;

      // 9. Hover Interaction Scale
      const targetGroupScale = isHovered ? 1.12 : 1.0;
      robotGroup.scale.x += (targetGroupScale - robotGroup.scale.x) * 0.1;
      robotGroup.scale.y += (targetGroupScale - robotGroup.scale.y) * 0.1;
      robotGroup.scale.z += (targetGroupScale - robotGroup.scale.z) * 0.1;

      renderer.render(scene, camera);
    }

    animate();
  }
})();
