(function () {
  function buildCurves() {
    const palettes = [
      { stroke: "rgba(20, 93, 242, 0.88)", fill: "rgba(20, 93, 242, 0.22)" },
      { stroke: "rgba(11, 127, 115, 0.90)", fill: "rgba(11, 127, 115, 0.24)" },
      { stroke: "rgba(31, 63, 122, 0.82)", fill: "rgba(31, 63, 122, 0.20)" },
      { stroke: "rgba(67, 160, 71, 0.84)", fill: "rgba(67, 160, 71, 0.20)" },
    ];

    return palettes.map((palette, index) => {
      const points = [];
      const phase = index * 1.27;
      const steps = 180;
      for (let i = 0; i <= steps; i += 1) {
        const t = (i / steps) * Math.PI * 4.4;
        const radius = 1.1 + 0.18 * Math.sin(2.8 * t + phase);
        const x = Math.cos(t + phase) * radius;
        const y = Math.sin(1.85 * t + phase * 0.7) * 0.68 + Math.cos(t * 0.35 + phase) * 0.18;
        const z = Math.sin(t * 0.92 + phase) * 1.18 + Math.cos(t * 0.55 + phase) * 0.24;
        points.push({ x, y, z });
      }
      return { palette, points };
    });
  }

  function rotatePoint(point, yaw, pitch) {
    const cy = Math.cos(yaw);
    const sy = Math.sin(yaw);
    const cp = Math.cos(pitch);
    const sp = Math.sin(pitch);

    const x1 = point.x * cy - point.z * sy;
    const z1 = point.x * sy + point.z * cy;
    const y1 = point.y * cp - z1 * sp;
    const z2 = point.y * sp + z1 * cp;

    return { x: x1, y: y1, z: z2 };
  }

  function mount(canvas) {
    if (!canvas || canvas.__proteinViewerMounted) {
      return;
    }
    canvas.__proteinViewerMounted = true;

    const context = canvas.getContext("2d");
    const curves = buildCurves();
    const parent = canvas.parentElement || canvas;
    const dpr = () => Math.max(1, Math.min(window.devicePixelRatio || 1, 2));
    let width = 0;
    let height = 0;

    function resize() {
      const rect = parent.getBoundingClientRect();
      width = Math.max(220, Math.floor(rect.width));
      height = Math.max(220, Math.floor(rect.height));
      canvas.width = Math.floor(width * dpr());
      canvas.height = Math.floor(height * dpr());
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr(), 0, 0, dpr(), 0, 0);
    }

    function drawFrame(now) {
      const time = now * 0.001;
      const yaw = time * 0.55;
      const pitch = 0.45 + Math.sin(time * 0.45) * 0.12;
      const scale = Math.min(width, height) * 0.18;
      const perspective = 4.3;
      const cx = width / 2;
      const cy = height / 2;

      context.clearRect(0, 0, width, height);

      const background = context.createRadialGradient(cx, cy, Math.min(width, height) * 0.08, cx, cy, Math.min(width, height) * 0.64);
      background.addColorStop(0, "rgba(255,255,255,0.96)");
      background.addColorStop(1, "rgba(228,236,248,0.18)");
      context.fillStyle = background;
      context.fillRect(0, 0, width, height);

      context.save();
      context.strokeStyle = "rgba(19, 37, 64, 0.08)";
      context.lineWidth = 1;
      for (let ring = 0; ring < 4; ring += 1) {
        const radius = Math.min(width, height) * (0.18 + ring * 0.085);
        context.beginPath();
        context.arc(cx, cy, radius, 0, Math.PI * 2);
        context.stroke();
      }
      context.restore();

      curves.forEach((curve) => {
        const projected = curve.points.map((point) => {
          const rotated = rotatePoint(point, yaw, pitch);
          const depth = perspective / (perspective - rotated.z);
          return {
            x: cx + rotated.x * depth * scale,
            y: cy + rotated.y * depth * scale,
            z: rotated.z,
            depth,
          };
        });

        context.beginPath();
        projected.forEach((point, index) => {
          if (index === 0) {
            context.moveTo(point.x, point.y);
          } else {
            context.lineTo(point.x, point.y);
          }
        });
        context.strokeStyle = curve.palette.stroke;
        context.lineWidth = 2.4;
        context.stroke();

        projected.forEach((point, index) => {
          if (index % 14 !== 0) {
            return;
          }
          context.beginPath();
          context.arc(point.x, point.y, Math.max(1.6, point.depth * 2.3), 0, Math.PI * 2);
          context.fillStyle = curve.palette.fill;
          context.fill();
        });
      });

      context.save();
      context.fillStyle = "rgba(19, 37, 64, 0.58)";
      context.font = "12px Arial, Calibri, sans-serif";
      context.fillText("Illustrative rotating structure view", 16, height - 18);
      context.restore();

      window.requestAnimationFrame(drawFrame);
    }

    resize();
    window.addEventListener("resize", resize);
    window.requestAnimationFrame(drawFrame);
  }

  function mountAll() {
    document.querySelectorAll("[data-protein-viewer]").forEach((canvas) => mount(canvas));
  }

  window.ECMOProteinViewer = { mount, mountAll };
})();
