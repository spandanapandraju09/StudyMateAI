/**
 * StudyMate AI — 3D Cosmic AI Environment (Billion-Dollar AI Startup Visual Engine)
 * Features:
 * - Rotating Translucent AI Glass Cube with Internal Glowing Core
 * - Continuous Holographic Floor Rings
 * - 5 Floating Glass Icons Orbiting in Circular Positions:
 *   - Top: AI Chat (💬)
 *   - Left: Notes (📄)
 *   - Right: Quiz (📝)
 *   - Bottom Left: Flashcards (🃏)
 *   - Bottom Right: Progress (📈)
 * - Deep Space Background (#050816), Nebula Clouds, Crystal Shards & Starfield
 * - Smooth Mouse Movement Parallax
 */

class Crystal3DScene {
  constructor() {
    this.canvas = document.getElementById('crystalCanvas');
    if (!this.canvas) {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'crystalCanvas';
      this.canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;';
      document.body.prepend(this.canvas);
    }

    this.mouse = { x: 0, y: 0, targetX: 0, targetY: 0 };
    this.featureNodes = [];
    this.clock = new THREE.Clock();

    this.init();
    this.createLights();
    this.createPedestal();
    this.createCrystalCube();
    this.createOrbBubbles();
    this.createCosmicParticles();
    this.createCrystalShards();
    this.addEvents();
    this.animate();
  }

  init() {
    this.width = window.innerWidth;
    this.height = window.innerHeight;

    this.scene = new THREE.Scene();
    this.scene.fog = new THREE.FogExp2(0x050816, 0.015);

    this.camera = new THREE.PerspectiveCamera(45, this.width / this.height, 0.1, 1000);
    this.updateCameraPosition();

    this.renderer = new THREE.WebGLRenderer({
      canvas: this.canvas,
      antialias: true,
      alpha: true,
      powerPreference: "high-performance"
    });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.35;
  }

  updateCameraPosition() {
    const isMobile = this.width < 992;
    if (isMobile) {
      this.camera.position.set(0, 0.4, 12.5);
      this.centerOffsetX = 0;
    } else {
      this.camera.position.set(2.2, 0.2, 10.0);
      this.centerOffsetX = 2.2;
    }
  }

  createLights() {
    const ambient = new THREE.AmbientLight(0x0d1438, 1.6);
    this.scene.add(ambient);

    // Cyan Glow PointLight
    this.cyanLight = new THREE.PointLight(0x40E8FF, 5, 25);
    this.cyanLight.position.set(this.centerOffsetX - 2.5, -1, 3);
    this.scene.add(this.cyanLight);

    // Purple Glow PointLight
    this.purpleLight = new THREE.PointLight(0x7B3FFF, 5, 25);
    this.purpleLight.position.set(this.centerOffsetX + 2.5, 3, 3);
    this.scene.add(this.purpleLight);

    // Pink Glow PointLight
    this.pinkLight = new THREE.PointLight(0xFF5FD7, 4, 20);
    this.pinkLight.position.set(this.centerOffsetX, 4, -2);
    this.scene.add(this.pinkLight);

    // Pedestal Down Light
    this.spotLight = new THREE.SpotLight(0x40E8FF, 4, 15, Math.PI / 3, 0.4);
    this.spotLight.position.set(this.centerOffsetX, 5, 1);
    this.spotLight.target.position.set(this.centerOffsetX, -2.5, 0);
    this.scene.add(this.spotLight);
    this.scene.add(this.spotLight.target);
  }

  createPedestal() {
    this.pedestalGroup = new THREE.Group();
    this.pedestalGroup.position.set(this.centerOffsetX, -2.1, 0);

    // Tiered Pedestal Base Discs
    const tiers = [
      { radiusTop: 2.2, radiusBottom: 2.5, height: 0.25, color: 0x0D1438 },
      { radiusTop: 1.7, radiusBottom: 1.9, height: 0.22, color: 0x1A2359 },
      { radiusTop: 1.2, radiusBottom: 1.4, height: 0.2, color: 0x242E73 }
    ];

    tiers.forEach((t, idx) => {
      const geo = new THREE.CylinderGeometry(t.radiusTop, t.radiusBottom, t.height, 64);
      const mat = new THREE.MeshStandardMaterial({
        color: t.color,
        roughness: 0.2,
        metalness: 0.8,
        emissive: 0x0D1438,
        emissiveIntensity: 0.3
      });
      const disc = new THREE.Mesh(geo, mat);
      disc.position.y = idx * 0.22;
      this.pedestalGroup.add(disc);
    });

    // Concentric Neon Holographic Floor Rings (Continuous Rotation)
    const ringData = [
      { radius: 3.4, tube: 0.025, color: 0x7B3FFF, speed: 0.006 },
      { radius: 4.3, tube: 0.02, color: 0x40E8FF, speed: -0.005 },
      { radius: 5.2, tube: 0.022, color: 0xFF5FD7, speed: 0.004 },
      { radius: 6.0, tube: 0.015, color: 0x74FF9C, speed: -0.003 }
    ];

    this.rings = [];
    ringData.forEach(data => {
      const geo = new THREE.TorusGeometry(data.radius, data.tube, 16, 120);
      const mat = new THREE.MeshBasicMaterial({
        color: data.color,
        transparent: true,
        opacity: 0.85
      });
      const ring = new THREE.Mesh(geo, mat);
      ring.rotation.x = Math.PI / 2;
      ring.position.y = 0.45;
      ring.userData = { speed: data.speed };
      this.pedestalGroup.add(ring);
      this.rings.push(ring);
    });

    const outerRingGeo = new THREE.RingGeometry(6.4, 6.5, 64);
    const outerRingMat = new THREE.MeshBasicMaterial({
      color: 0x40E8FF,
      transparent: true,
      opacity: 0.4,
      side: THREE.DoubleSide
    });
    const outerRing = new THREE.Mesh(outerRingGeo, outerRingMat);
    outerRing.rotation.x = Math.PI / 2;
    outerRing.position.y = 0.44;
    this.pedestalGroup.add(outerRing);

    this.scene.add(this.pedestalGroup);
  }

  createCrystalCube() {
    this.cubeGroup = new THREE.Group();
    this.cubeGroup.position.set(this.centerOffsetX, 0.1, 0);

    // Outer Glass AI Cube
    const cubeGeo = new THREE.BoxGeometry(2.3, 2.3, 2.3);
    const cubeMat = new THREE.MeshPhysicalMaterial({
      color: 0x7B3FFF,
      emissive: 0x241154,
      emissiveIntensity: 0.5,
      roughness: 0.05,
      metalness: 0.1,
      transmission: 0.88,
      ior: 1.52,
      transparent: true,
      opacity: 0.88,
      clearcoat: 1.0,
      clearcoatRoughness: 0.05,
      side: THREE.DoubleSide
    });
    this.crystalCube = new THREE.Mesh(cubeGeo, cubeMat);
    this.cubeGroup.add(this.crystalCube);

    // Glowing Neon Edges
    const edgesGeo = new THREE.EdgesGeometry(cubeGeo);
    const edgesMat = new THREE.LineBasicMaterial({ color: 0x40E8FF, linewidth: 2 });
    this.cubeEdges = new THREE.LineSegments(edgesGeo, edgesMat);
    this.cubeGroup.add(this.cubeEdges);

    // Inner Core AI Emblem (Glowing Canvas Texture Sprite)
    const aiSprite = this.createAISprite();
    aiSprite.position.set(0, 0, 0);
    this.cubeGroup.add(aiSprite);

    // Inner Wireframe Core Cube
    const innerGeo = new THREE.BoxGeometry(1.3, 1.3, 1.3);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0xFF5FD7,
      wireframe: true,
      transparent: true,
      opacity: 0.6
    });
    this.innerCube = new THREE.Mesh(innerGeo, innerMat);
    this.cubeGroup.add(this.innerCube);

    this.scene.add(this.cubeGroup);
  }

  createAISprite() {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 256;
    const ctx = canvas.getContext('2d');

    ctx.font = '900 120px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFFFFF';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = '#40E8FF';
    ctx.shadowBlur = 30;
    ctx.fillText('AI', 128, 128);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, blending: THREE.AdditiveBlending });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(1.8, 1.8, 1);
    return sprite;
  }

  createOrbBubbles() {
    this.orbitGroup = new THREE.Group();
    this.orbitGroup.position.set(this.centerOffsetX, 0.1, 0);

    // Exact 5 Orbs matching user prompt requirements:
    // Top: AI Chat (💬)
    // Left: Notes (📄)
    // Right: Quiz (📝)
    // Bottom Left: Flashcards (🃏)
    // Bottom Right: Progress (📈)

    const featureData = [
      { icon: '💬', label: 'AI Chat', color: 0x7B3FFF, x: 0.0, y: 2.35, z: 0.1 },
      { icon: '📄', label: 'Notes', color: 0x40E8FF, x: -2.3, y: 1.25, z: 0.3 },
      { icon: '📝', label: 'Quiz', color: 0xFF5FD7, x: 2.3, y: 1.25, z: -0.2 },
      { icon: '🃏', label: 'Flashcards', color: 0x9D4edd, x: -2.0, y: -1.2, z: 0.4 },
      { icon: '📈', label: 'Progress', color: 0x40E8FF, x: 2.1, y: -1.2, z: -0.1 }
    ];

    featureData.forEach((feat, idx) => {
      const orbGroup = new THREE.Group();
      orbGroup.position.set(feat.x, feat.y, feat.z);

      // Translucent Glass Sphere (rgba(255,255,255,0.08) glass style)
      const sphereGeo = new THREE.SphereGeometry(0.55, 32, 32);
      const sphereMat = new THREE.MeshPhysicalMaterial({
        color: feat.color,
        emissive: feat.color,
        emissiveIntensity: 0.45,
        roughness: 0.05,
        transmission: 0.88,
        transparent: true,
        opacity: 0.85,
        clearcoat: 1.0
      });
      const sphere = new THREE.Mesh(sphereGeo, sphereMat);
      orbGroup.add(sphere);

      // Icon INSIDE sphere
      const iconSprite = this.createOrbIconSprite(feat.icon);
      iconSprite.position.set(0, 0, 0);
      orbGroup.add(iconSprite);

      // Pure White Text Label BELOW sphere
      const textSprite = this.createOrbTextSprite(feat.label);
      textSprite.position.set(0, -0.85, 0);
      orbGroup.add(textSprite);

      orbGroup.userData = {
        anchorX: feat.x,
        anchorY: feat.y,
        anchorZ: feat.z,
        offset: idx * 1.25
      };

      this.orbitGroup.add(orbGroup);
      this.featureNodes.push(orbGroup);
    });

    // Orbital Ring Lines
    const ringMat = new THREE.LineBasicMaterial({ color: 0x40E8FF, transparent: true, opacity: 0.35 });
    const orbitRingGeo1 = new THREE.TorusGeometry(3.1, 0.008, 16, 100);
    const orbitRing1 = new THREE.LineSegments(new THREE.WireframeGeometry(orbitRingGeo1), ringMat);
    orbitRing1.rotation.x = Math.PI / 2.3;
    this.orbitGroup.add(orbitRing1);

    const orbitRingGeo2 = new THREE.TorusGeometry(3.5, 0.008, 16, 100);
    const orbitRing2 = new THREE.LineSegments(new THREE.WireframeGeometry(orbitRingGeo2), ringMat);
    orbitRing2.rotation.x = Math.PI / 1.8;
    orbitRing2.rotation.y = Math.PI / 6;
    this.orbitGroup.add(orbitRing2);

    this.scene.add(this.orbitGroup);
  }

  createOrbIconSprite(icon) {
    const canvas = document.createElement('canvas');
    canvas.width = 128;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    ctx.font = '700 64px "Segoe UI Emoji", "Apple Color Emoji", sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#FFFFFF';
    ctx.shadowColor = '#40E8FF';
    ctx.shadowBlur = 15;
    ctx.fillText(icon, 64, 64);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true, blending: THREE.AdditiveBlending });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(0.7, 0.7, 1);
    return sprite;
  }

  createOrbTextSprite(text) {
    const canvas = document.createElement('canvas');
    canvas.width = 256;
    canvas.height = 64;
    const ctx = canvas.getContext('2d');

    ctx.font = '700 24px "Space Grotesk", sans-serif';
    ctx.fillStyle = '#FFFFFF'; // Pure White text
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.shadowColor = 'rgba(123, 63, 255, 0.8)';
    ctx.shadowBlur = 12;
    ctx.fillText(text, 128, 32);

    const texture = new THREE.CanvasTexture(canvas);
    const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
    const sprite = new THREE.Sprite(spriteMat);
    sprite.scale.set(1.5, 0.38, 1);
    return sprite;
  }

  createCosmicParticles() {
    // Starfield Points (Tiny Sparkles)
    const starsGeo = new THREE.BufferGeometry();
    const starCount = 750;
    const posArray = new Float32Array(starCount * 3);

    for (let i = 0; i < starCount * 3; i += 3) {
      posArray[i] = (Math.random() - 0.5) * 45;
      posArray[i + 1] = (Math.random() - 0.5) * 45;
      posArray[i + 2] = (Math.random() - 0.5) * 35;
    }

    starsGeo.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const starsMat = new THREE.PointsMaterial({
      size: 0.09,
      color: 0x40E8FF,
      transparent: true,
      opacity: 0.85,
      blending: THREE.AdditiveBlending
    });

    this.starField = new THREE.Points(starsGeo, starsMat);
    this.scene.add(this.starField);

    // Purple & Pink Nebula Soft Particles
    const nebulaGeo = new THREE.BufferGeometry();
    const nebulaCount = 200;
    const nPos = new Float32Array(nebulaCount * 3);

    for (let i = 0; i < nebulaCount * 3; i += 3) {
      nPos[i] = (Math.random() - 0.5) * 32;
      nPos[i + 1] = (Math.random() - 0.5) * 32;
      nPos[i + 2] = (Math.random() - 0.5) * 20;
    }

    nebulaGeo.setAttribute('position', new THREE.BufferAttribute(nPos, 3));
    const nebulaMat = new THREE.PointsMaterial({
      size: 0.35,
      color: 0xFF5FD7,
      transparent: true,
      opacity: 0.45,
      blending: THREE.AdditiveBlending
    });

    this.nebulaParticles = new THREE.Points(nebulaGeo, nebulaMat);
    this.scene.add(this.nebulaParticles);
  }

  createCrystalShards() {
    this.shardsGroup = new THREE.Group();
    const shardGeo = new THREE.BoxGeometry(0.22, 0.22, 0.22);

    for (let i = 0; i < 24; i++) {
      const shardMat = new THREE.MeshBasicMaterial({
        color: i % 2 === 0 ? 0x40E8FF : 0x7B3FFF,
        transparent: true,
        opacity: 0.6,
        wireframe: true
      });
      const shard = new THREE.Mesh(shardGeo, shardMat);
      shard.position.set(
        this.centerOffsetX + (Math.random() - 0.5) * 11,
        (Math.random() - 0.5) * 9,
        (Math.random() - 0.5) * 7
      );
      shard.userData = {
        rotSpeed: (Math.random() - 0.5) * 0.02,
        floatSpeed: (Math.random() - 0.5) * 0.01
      };
      this.shardsGroup.add(shard);
    }
    this.scene.add(this.shardsGroup);
  }

  addEvents() {
    window.addEventListener('resize', () => this.onResize());
    window.addEventListener('mousemove', (e) => {
      this.mouse.targetX = (e.clientX / this.width - 0.5) * 1.2;
      this.mouse.targetY = -(e.clientY / this.height - 0.5) * 1.2;
    });
  }

  onResize() {
    this.width = window.innerWidth;
    this.height = window.innerHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
    this.updateCameraPosition();
  }

  animate() {
    requestAnimationFrame(() => this.animate());

    const elapsedTime = this.clock.getElapsedTime();

    this.mouse.x += (this.mouse.targetX - this.mouse.x) * 0.04;
    this.mouse.y += (this.mouse.targetY - this.mouse.y) * 0.04;

    const isMobile = this.width < 992;
    const targetX = isMobile ? 0 : 2.2;
    this.camera.position.x = targetX + this.mouse.x;
    this.camera.position.y = 0.2 + this.mouse.y * 0.7;
    this.camera.lookAt(targetX, 0, 0);

    // Cube floating & slow rotation
    if (this.cubeGroup) {
      this.cubeGroup.position.y = 0.1 + Math.sin(elapsedTime * 1.4) * 0.18;
      this.crystalCube.rotation.x = elapsedTime * 0.15;
      this.crystalCube.rotation.y = elapsedTime * 0.22;
      this.innerCube.rotation.x = -elapsedTime * 0.25;
      this.innerCube.rotation.y = -elapsedTime * 0.18;
      this.cubeEdges.rotation.x = elapsedTime * 0.15;
      this.cubeEdges.rotation.y = elapsedTime * 0.22;
    }

    // Pedestal rings continuous rotation
    if (this.rings) {
      this.rings.forEach(ring => {
        ring.rotation.z += ring.userData.speed;
      });
    }

    // Floating Orb Bubbles slowly orbiting around anchor positions
    if (this.featureNodes) {
      this.featureNodes.forEach(node => {
        const offset = node.userData.offset;
        node.position.x = node.userData.anchorX + Math.sin(elapsedTime * 1.1 + offset) * 0.14;
        node.position.y = node.userData.anchorY + Math.cos(elapsedTime * 1.4 + offset) * 0.16;
        node.position.z = node.userData.anchorZ + Math.sin(elapsedTime * 0.8 + offset) * 0.08;
      });
    }

    // Background particle drift
    if (this.starField) {
      this.starField.rotation.y = elapsedTime * 0.012;
    }
    if (this.nebulaParticles) {
      this.nebulaParticles.rotation.y = -elapsedTime * 0.008;
    }

    // Drifting Crystal Shards
    if (this.shardsGroup) {
      this.shardsGroup.children.forEach(shard => {
        shard.rotation.x += shard.userData.rotSpeed;
        shard.rotation.y += shard.userData.rotSpeed;
        shard.position.y += Math.sin(elapsedTime * 2) * shard.userData.floatSpeed;
      });
    }

    this.renderer.render(this.scene, this.camera);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  if (typeof THREE !== 'undefined') {
    new Crystal3DScene();
  } else {
    window.addEventListener('load', () => new Crystal3DScene());
  }
});
