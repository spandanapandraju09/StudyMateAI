/* StudyMate AI — Orbiting AI Core hero (vanilla JS, no dependencies)
   Builds the orbiting node network, connecting lines, particle field,
   and mouse-parallax tilt inside <div class="ai-core-scene" id="aiScene">. */
(function () {
  const scene = document.getElementById('aiScene');
  if (!scene) return;

  const nodeDefs = [
    { icon: '💬', label: 'AI Chat' },
    { icon: '📄', label: 'Notes' },
    { icon: '🎯', label: 'Quiz' },
    { icon: '🃏', label: 'Flashcards' },
    { icon: '📈', label: 'Progress' },
  ];

  const nodes = nodeDefs.map((def, i) => {
    const el = document.createElement('div');
    el.className = 'neural-node';
    el.innerHTML = `<span class="n-icon">${def.icon}</span><span class="n-label">${def.label}</span>`;
    scene.appendChild(el);

    const line = document.createElement('div');
    line.className = 'neural-line';
    line.style.animationDelay = (i * 0.4) + 's';
    scene.appendChild(line);

    return { el, line, angle: (Math.PI * 2 / nodeDefs.length) * i - Math.PI / 2 };
  });

  // A few small drifting hex shapes, purely decorative
  const hexEmojis = ['◆', '⬡', '◇'];
  for (let i = 0; i < 4; i++) {
    const s = document.createElement('div');
    s.className = 'float-shape';
    s.textContent = hexEmojis[i % hexEmojis.length];
    s.style.left = (10 + Math.random() * 80) + '%';
    s.style.top = (10 + Math.random() * 80) + '%';
    s.style.fontSize = (12 + Math.random() * 10) + 'px';
    s.style.color = ['#00E5FF', '#A855F7', '#EC4899'][i % 3];
    s.style.animationDelay = (Math.random() * 4) + 's';
    scene.appendChild(s);
  }

  let orbitAngle = 0;
  let parallaxX = 0, parallaxY = 0;

  function layout() {
    const w = scene.clientWidth, h = scene.clientHeight;
    const cx = w / 2, cy = h / 2;
    const radius = Math.min(w, h) * 0.36;

    nodes.forEach(n => {
      const a = n.angle + orbitAngle;
      const x = cx + Math.cos(a) * radius + parallaxX;
      const y = cy + Math.sin(a) * radius * 0.62 + parallaxY;
      n.el.style.left = x + 'px';
      n.el.style.top = y + 'px';

      const dx = x - cx, dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);
      const ang = Math.atan2(dy, dx) * 180 / Math.PI;
      n.line.style.width = dist + 'px';
      n.line.style.transform = `rotate(${ang}deg)`;
    });
  }

  function animateOrbit() {
    orbitAngle += 0.0028;
    layout();
    requestAnimationFrame(animateOrbit);
  }

  window.addEventListener('resize', layout);
  layout();
  animateOrbit();

  // Mouse parallax — network bends slightly toward the cursor
  scene.addEventListener('mousemove', (e) => {
    const rect = scene.getBoundingClientRect();
    const relX = (e.clientX - rect.left) / rect.width - 0.5;
    const relY = (e.clientY - rect.top) / rect.height - 0.5;
    parallaxX = relX * 24;
    parallaxY = relY * 24;
    scene.style.transform = `rotateY(${relX * 6}deg) rotateX(${-relY * 6}deg)`;
  });
  scene.addEventListener('mouseleave', () => {
    parallaxX = 0; parallaxY = 0;
    scene.style.transform = 'rotateY(0deg) rotateX(0deg)';
  });

  // Particle field
  const canvas = document.createElement('canvas');
  canvas.className = 'particle-field';
  scene.insertBefore(canvas, scene.firstChild);
  const ctx = canvas.getContext('2d');
  let particles = [];

  function resizeCanvas() {
    canvas.width = scene.clientWidth;
    canvas.height = scene.clientHeight;
  }
  function initParticles() {
    const count = Math.min(120, Math.floor((canvas.width * canvas.height) / 7000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.5 + 0.4,
    }));
  }
  resizeCanvas();
  initParticles();
  window.addEventListener('resize', () => { resizeCanvas(); initParticles(); });

  const palette = ['#00E5FF', '#A855F7', '#EC4899', '#6C63FF'];

  function drawParticles() {
    if (!canvas.width || !canvas.height) { requestAnimationFrame(drawParticles); return; }
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    });
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const a = particles[i], b = particles[j];
        const d = Math.hypot(a.x - b.x, a.y - b.y);
        if (d < 85) {
          ctx.strokeStyle = `rgba(168,85,247,${0.14 * (1 - d / 85)})`;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(a.x, a.y);
          ctx.lineTo(b.x, b.y);
          ctx.stroke();
        }
      }
    }
    particles.forEach((p, i) => {
      ctx.fillStyle = palette[i % palette.length];
      ctx.globalAlpha = 0.55;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    });
    requestAnimationFrame(drawParticles);
  }
  drawParticles();

  // Public helper other scripts (e.g. chat send) can call for the "thinking" burst
  window.aiCoreThinking = function (ms) {
    scene.classList.add('thinking');
    setTimeout(() => scene.classList.remove('thinking'), ms || 2000);
  };
})();
