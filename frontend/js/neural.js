class NeuralCanvas {
  constructor(){
    this.canvas = document.getElementById('neuralCanvas') || this._create();
    this.ctx = this.canvas.getContext('2d');
    this.nodes = []; this.pulses = [];
    this.mouse = { x: -1000, y: -1000, r: 180 };
    this._resize(); window.addEventListener('resize',()=>this._resize());
    window.addEventListener('mousemove', (e) => {
      this.mouse.x = e.clientX;
      this.mouse.y = e.clientY;
    });
    this._spawn(); this._loop();
  }
  _create(){
    const c=document.createElement('canvas');
    c.id='neuralCanvas'; c.className='neural-canvas';
    c.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:0;';
    document.body.prepend(c); return c;
  }
  _resize(){ this.W=this.canvas.width=window.innerWidth; this.H=this.canvas.height=window.innerHeight; }
  _spawn(){
    this.nodes=[];
    for(let i=0;i<56;i++) this.nodes.push({
      x:Math.random()*this.W, y:Math.random()*this.H,
      vx:(Math.random()-.5)*.5, vy:(Math.random()-.5)*.5,
      r:Math.random()*2.2+1, p:Math.random()*Math.PI*2,
      type: i % 4
    });
  }
  _loop(){
    const ctx=this.ctx;
    ctx.clearRect(0,0,this.W,this.H);

    // Draw cursor mouse glow
    if (this.mouse.x > 0) {
      const mg = ctx.createRadialGradient(this.mouse.x, this.mouse.y, 0, this.mouse.x, this.mouse.y, this.mouse.r);
      mg.addColorStop(0, 'rgba(236, 72, 153, 0.10)');
      mg.addColorStop(0.5, 'rgba(139, 92, 246, 0.05)');
      mg.addColorStop(1, 'transparent');
      ctx.beginPath();
      ctx.arc(this.mouse.x, this.mouse.y, this.mouse.r, 0, Math.PI*2);
      ctx.fillStyle = mg;
      ctx.fill();
    }

    for(const n of this.nodes){
      n.x+=n.vx; n.y+=n.vy; n.p+=.022;
      if(n.x<0||n.x>this.W) n.vx*=-1;
      if(n.y<0||n.y>this.H) n.vy*=-1;
    }
    for(let i=0;i<this.nodes.length;i++){
      for(let j=i+1;j<this.nodes.length;j++){
        const a=this.nodes[i], b=this.nodes[j];
        const d=Math.hypot(a.x-b.x,a.y-b.y);
        if(d<150){
          const alpha=(1-d/150)*.25;
          const g=ctx.createLinearGradient(a.x,a.y,b.x,b.y);
          g.addColorStop(0,`rgba(139, 92, 246,${alpha})`);
          g.addColorStop(0.5,`rgba(236, 72, 153,${alpha*0.8})`);
          g.addColorStop(1,`rgba(168, 85, 247,${alpha})`);
          ctx.beginPath(); ctx.moveTo(a.x,a.y); ctx.lineTo(b.x,b.y);
          ctx.strokeStyle=g; ctx.lineWidth=.8; ctx.stroke();
          if(Math.random()<.001) this.pulses.push({x1:a.x,y1:a.y,x2:b.x,y2:b.y,t:0,s:.02+Math.random()*.02});
        }
      }
    }
    for(let i=this.pulses.length-1;i>=0;i--){
      const p=this.pulses[i]; p.t+=p.s;
      if(p.t>=1){this.pulses.splice(i,1);continue;}
      const px=p.x1+(p.x2-p.x1)*p.t, py=p.y1+(p.y2-p.y1)*p.t;
      ctx.beginPath(); ctx.arc(px,py,2.5,0,Math.PI*2);
      ctx.fillStyle='#EC4899'; ctx.shadowBlur=12; ctx.shadowColor='#EC4899';
      ctx.fill(); ctx.shadowBlur=0;
    }
    const colors=['rgba(139, 92, 246, .85)','rgba(236, 72, 153, .85)','rgba(168, 85, 247, .85)','rgba(192, 132, 252, .9)'];
    const glows=['#8b5cf6','#ec4899','#a855f7','#c084fc'];
    for(const n of this.nodes){
      const pr=n.r+Math.sin(n.p)*.6;
      ctx.beginPath(); ctx.arc(n.x,n.y,pr,0,Math.PI*2);
      ctx.fillStyle=colors[n.type]; ctx.shadowBlur=10; ctx.shadowColor=glows[n.type];
      ctx.fill(); ctx.shadowBlur=0;
    }
    requestAnimationFrame(()=>this._loop());
  }
}
document.addEventListener('DOMContentLoaded',()=>new NeuralCanvas());
