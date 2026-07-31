// StudyMate AI - Premium Three.js Background
// Animated nebula, galaxy, aurora, stars, particles, and interactive effects

class PremiumBackground {
  constructor() {
    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.particles = null;
    this.stars = null;
    this.nebula = null;
    this.mouseX = 0;
    this.mouseY = 0;
    this.targetMouseX = 0;
    this.targetMouseY = 0;
    this.clock = new THREE.Clock();
    this.floatingCubes = [];
    
    this.init();
    this.createStarfield();
    this.createNebula();
    this.createParticles();
    this.createFloatingCubes();
    this.addEventListeners();
    this.animate();
  }

  init() {
    // Scene
    this.scene = new THREE.Scene();
    
    // Camera
    this.camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    this.camera.position.z = 50;
    
    // Renderer
    this.renderer = new THREE.WebGLRenderer({
      alpha: true,
      antialias: true
    });
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    
    let canvas = document.getElementById('bg-canvas');
    if (!canvas) {
      canvas = this.renderer.domElement;
      canvas.id = 'bg-canvas';
      document.body.prepend(canvas);
    } else {
      canvas.parentNode.replaceChild(this.renderer.domElement, canvas);
      this.renderer.domElement.id = 'bg-canvas';
    }
  }

  createStarfield() {
    const starsGeometry = new THREE.BufferGeometry();
    const starsCount = 2000;
    const positions = new Float32Array(starsCount * 3);
    const colors = new Float32Array(starsCount * 3);
    const sizes = new Float32Array(starsCount);
    
    for (let i = 0; i < starsCount; i++) {
      const i3 = i * 3;
      
      // Position
      positions[i3] = (Math.random() - 0.5) * 200;
      positions[i3 + 1] = (Math.random() - 0.5) * 200;
      positions[i3 + 2] = (Math.random() - 0.5) * 200;
      
      // Color (white to blue to purple)
      const colorChoice = Math.random();
      if (colorChoice < 0.33) {
        colors[i3] = 0.6; colors[i3 + 1] = 0.8; colors[i3 + 2] = 1.0; // Blue
      } else if (colorChoice < 0.66) {
        colors[i3] = 0.8; colors[i3 + 1] = 0.6; colors[i3 + 2] = 1.0; // Purple
      } else {
        colors[i3] = 1.0; colors[i3 + 1] = 1.0; colors[i3 + 2] = 1.0; // White
      }
      
      // Size
      sizes[i] = Math.random() * 2;
    }
    
    starsGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    starsGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    starsGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
    
    const starsMaterial = new THREE.PointsMaterial({
      size: 0.5,
      vertexColors: true,
      transparent: true,
      opacity: 0.8,
      sizeAttenuation: true
    });
    
    this.stars = new THREE.Points(starsGeometry, starsMaterial);
    this.scene.add(this.stars);
  }

  createNebula() {
    // Create nebula effect with multiple transparent planes
    const nebulaGeometry = new THREE.PlaneGeometry(100, 100);
    
    const nebulaMaterial1 = new THREE.MeshBasicMaterial({
      color: 0x6A5CFF,
      transparent: true,
      opacity: 0.15,
      side: THREE.DoubleSide
    });
    
    const nebulaMaterial2 = new THREE.MeshBasicMaterial({
      color: 0x00D8FF,
      transparent: true,
      opacity: 0.12,
      side: THREE.DoubleSide
    });
    
    const nebulaMaterial3 = new THREE.MeshBasicMaterial({
      color: 0xFF5CE5,
      transparent: true,
      opacity: 0.1,
      side: THREE.DoubleSide
    });
    
    this.nebula1 = new THREE.Mesh(nebulaGeometry, nebulaMaterial1);
    this.nebula1.position.set(-30, 20, -50);
    this.scene.add(this.nebula1);
    
    this.nebula2 = new THREE.Mesh(nebulaGeometry, nebulaMaterial2);
    this.nebula2.position.set(30, -20, -40);
    this.scene.add(this.nebula2);
    
    this.nebula3 = new THREE.Mesh(nebulaGeometry, nebulaMaterial3);
    this.nebula3.position.set(0, 0, -60);
    this.scene.add(this.nebula3);
  }

  createParticles() {
    const particlesGeometry = new THREE.BufferGeometry();
    const particlesCount = 500;
    const positions = new Float32Array(particlesCount * 3);
    
    for (let i = 0; i < particlesCount; i++) {
      const i3 = i * 3;
      positions[i3] = (Math.random() - 0.5) * 100;
      positions[i3 + 1] = (Math.random() - 0.5) * 100;
      positions[i3 + 2] = (Math.random() - 0.5) * 100;
    }
    
    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    
    const particlesMaterial = new THREE.PointsMaterial({
      color: 0x00D8FF,
      size: 0.3,
      transparent: true,
      opacity: 0.6,
      sizeAttenuation: true
    });
    
    this.particles = new THREE.Points(particlesGeometry, particlesMaterial);
    this.scene.add(this.particles);
  }

  createFloatingCubes() {
    const cubeGeometry = new THREE.BoxGeometry(1, 1, 1);
    const cubeMaterial = new THREE.MeshBasicMaterial({
      color: 0x6A5CFF,
      wireframe: true,
      transparent: true,
      opacity: 0.3
    });
    
    for (let i = 0; i < 15; i++) {
      const cube = new THREE.Mesh(cubeGeometry, cubeMaterial.clone());
      cube.position.set(
        (Math.random() - 0.5) * 80,
        (Math.random() - 0.5) * 80,
        (Math.random() - 0.5) * 40 - 20
      );
      cube.rotation.set(
        Math.random() * Math.PI,
        Math.random() * Math.PI,
        Math.random() * Math.PI
      );
      cube.userData = {
        rotationSpeed: {
          x: (Math.random() - 0.5) * 0.01,
          y: (Math.random() - 0.5) * 0.01,
          z: (Math.random() - 0.5) * 0.01
        },
        floatSpeed: Math.random() * 0.5 + 0.5,
        floatOffset: Math.random() * Math.PI * 2
      };
      
      this.floatingCubes.push(cube);
      this.scene.add(cube);
    }
  }

  addEventListeners() {
    window.addEventListener('resize', () => this.onResize());
    window.addEventListener('mousemove', (e) => this.onMouseMove(e));
  }

  onResize() {
    this.camera.aspect = window.innerWidth / window.innerHeight;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  onMouseMove(event) {
    this.targetMouseX = (event.clientX / window.innerWidth) * 2 - 1;
    this.targetMouseY = -(event.clientY / window.innerHeight) * 2 + 1;
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    
    const time = this.clock.getElapsedTime();
    
    // Smooth mouse follow
    this.mouseX += (this.targetMouseX - this.mouseX) * 0.05;
    this.mouseY += (this.targetMouseY - this.mouseY) * 0.05;
    
    // Rotate stars slowly
    if (this.stars) {
      this.stars.rotation.y = time * 0.02;
      this.stars.rotation.x = time * 0.01;
    }
    
    // Animate nebula
    if (this.nebula1) {
      this.nebula1.rotation.z = time * 0.05;
      this.nebula1.position.x = -30 + Math.sin(time * 0.2) * 5;
    }
    if (this.nebula2) {
      this.nebula2.rotation.z = -time * 0.03;
      this.nebula2.position.y = -20 + Math.cos(time * 0.15) * 5;
    }
    if (this.nebula3) {
      this.nebula3.rotation.z = time * 0.04;
    }
    
    // Rotate particles
    if (this.particles) {
      this.particles.rotation.y = time * 0.05;
      this.particles.rotation.x = time * 0.03;
    }
    
    // Animate floating cubes
    this.floatingCubes.forEach(cube => {
      cube.rotation.x += cube.userData.rotationSpeed.x;
      cube.rotation.y += cube.userData.rotationSpeed.y;
      cube.rotation.z += cube.userData.rotationSpeed.z;
      cube.position.y += Math.sin(time * cube.userData.floatSpeed + cube.userData.floatOffset) * 0.01;
    });
    
    // Camera parallax based on mouse
    this.camera.position.x = this.mouseX * 3;
    this.camera.position.y = this.mouseY * 3;
    this.camera.lookAt(this.scene.position);
    
    this.renderer.render(this.scene, this.camera);
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  // Only initialize on pages that need it
  if (document.getElementById('ai-cube') || document.querySelector('.hero')) {
    new PremiumBackground();
  }
});

// Export for use in other modules
window.PremiumBackground = PremiumBackground;