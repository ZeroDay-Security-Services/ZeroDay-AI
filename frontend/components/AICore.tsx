'use client';

import { useEffect, useRef } from 'react';

/** Signature animated AI core visualization -- HUD ring, rotating arcs, pulsing core. */
export default function AICore() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    let t = 0;
    let raf = 0;

    function resize() {
      if (!canvas || !canvas.parentElement) return;
      const rect = canvas.parentElement.getBoundingClientRect();
      const dpr = window.devicePixelRatio || 1;
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
      ctx?.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function draw() {
      if (!canvas || !canvas.parentElement || !ctx) return;
      const rect = canvas.parentElement.getBoundingClientRect();
      const cx = rect.width / 2;
      const cy = rect.height / 2;
      const R = (Math.min(rect.width, rect.height) / 2) * 0.86;
      ctx.clearRect(0, 0, rect.width, rect.height);

      ctx.save();
      ctx.translate(cx, cy);
      for (let i = 0; i < 72; i++) {
        const ang = (i / 72) * Math.PI * 2 + t * 0.06;
        const len = i % 6 === 0 ? 10 : 4;
        const r1 = R;
        const r2 = R - len;
        ctx.beginPath();
        ctx.moveTo(Math.cos(ang) * r1, Math.sin(ang) * r1);
        ctx.lineTo(Math.cos(ang) * r2, Math.sin(ang) * r2);
        ctx.strokeStyle = i % 6 === 0 ? 'rgba(0,232,255,0.5)' : 'rgba(124,141,166,0.25)';
        ctx.lineWidth = i % 6 === 0 ? 1.4 : 0.8;
        ctx.stroke();
      }
      ctx.restore();

      const arcs = [
        { r: R * 0.78, speed: 0.4, width: 2.2, color: 'rgba(0,232,255,0.75)', span: 1.1 },
        { r: R * 0.62, speed: -0.6, width: 1.6, color: 'rgba(45,107,255,0.6)', span: 2.0 },
        { r: R * 0.46, speed: 0.8, width: 1.2, color: 'rgba(0,232,255,0.4)', span: 0.7 },
      ];
      arcs.forEach((a) => {
        ctx.save();
        ctx.translate(cx, cy);
        const start = t * a.speed;
        ctx.beginPath();
        ctx.arc(0, 0, a.r, start, start + a.span);
        ctx.strokeStyle = a.color;
        ctx.lineWidth = a.width;
        ctx.lineCap = 'round';
        ctx.stroke();
        ctx.restore();
      });

      const pulse = 1 + Math.sin(t * 1.8) * 0.06;
      const coreR = R * 0.22 * pulse;
      const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, coreR * 3.2);
      grad.addColorStop(0, 'rgba(0,232,255,0.9)');
      grad.addColorStop(0.35, 'rgba(45,107,255,0.35)');
      grad.addColorStop(1, 'rgba(45,107,255,0)');
      ctx.beginPath();
      ctx.arc(cx, cy, coreR * 3.2, 0, Math.PI * 2);
      ctx.fillStyle = grad;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
      ctx.fillStyle = '#eafcff';
      ctx.shadowColor = 'rgba(0,232,255,0.9)';
      ctx.shadowBlur = 24;
      ctx.fill();
      ctx.shadowBlur = 0;

      for (let i = 0; i < 5; i++) {
        const ang = t * 0.5 + i * ((Math.PI * 2) / 5);
        const r = R * 0.62;
        const nx = cx + Math.cos(ang) * r;
        const ny = cy + Math.sin(ang) * r;
        ctx.beginPath();
        ctx.arc(nx, ny, 2.6, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0,232,255,0.85)';
        ctx.fill();
      }

      if (!reduceMotion) t += 0.016;
      raf = requestAnimationFrame(draw);
    }

    resize();
    draw();
    window.addEventListener('resize', resize);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', resize);
    };
  }, []);

  const readout = (label: string, value: string, className: string) => (
    <div className={`absolute flex flex-col gap-0.5 font-mono text-[9.5px] tracking-wider text-steel ${className}`}>
      {label}
      <span className="text-[10.5px] text-cyan">{value}</span>
    </div>
  );

  return (
    <div className="relative mx-auto aspect-square w-full max-w-[440px]">
      <canvas ref={canvasRef} className="absolute inset-0 h-full w-full" />
      {readout('SYSTEM STATUS', 'NOMINAL', 'left-[2%] top-[6%]')}
      {readout('THREAT LEVEL', 'LOW', 'right-[2%] top-[6%] text-right items-end')}
      {readout('AGENTS ACTIVE', '05 / 05', 'left-[2%] bottom-[6%]')}
      {readout('LATENCY', '12ms', 'right-[2%] bottom-[6%] text-right items-end')}
    </div>
  );
}
