import * as THREE from 'three';
import { useEffect, useRef, useState, useCallback } from 'react';

export type AetherBackgroundProps = {
  overlayGradient?: string;
  className?: string;
};

const vertexShader = `void main(){ gl_Position = vec4(position, 1.0); }`;

const fragmentShader = `
uniform float iTime;
uniform vec3 iResolution;

#define TAU 6.2831853071795865
#define TUNNEL_LAYERS 96
#define RING_POINTS 128
#define POINT_SIZE 1.8
#define POINT_COLOR_A vec3(1.0)
#define POINT_COLOR_B vec3(0.7)
#define SPEED 0.7

float sq(float x){ return x*x; }

vec2 AngRep(vec2 uv, float angle){
  vec2 polar = vec2(atan(uv.y, uv.x), length(uv));
  polar.x = mod(polar.x + angle/2.0, angle) - angle/2.0;
  return polar.y * vec2(cos(polar.x), sin(polar.x));
}

float sdCircle(vec2 uv, float r){ return length(uv) - r; }

vec3 MixShape(float sd, vec3 fill, vec3 target){
  float blend = smoothstep(0.0, 1.0/iResolution.y, sd);
  return mix(fill, target, blend);
}

vec2 TunnelPath(float x){
  vec2 offs = vec2(
    0.2 * sin(TAU * x * 0.5) + 0.4 * sin(TAU * x * 0.2 + 0.3),
    0.3 * cos(TAU * x * 0.3) + 0.2 * cos(TAU * x * 0.1)
  );
  offs *= smoothstep(1.0, 4.0, x);
  return offs;
}

void main(){
  vec2 res = iResolution.xy / iResolution.y;
  vec2 uv = gl_FragCoord.xy / iResolution.y - res/2.0;
  vec3 color = vec3(0.0);
  float repAngle = TAU / float(RING_POINTS);
  float pointSize = POINT_SIZE / (2.0 * iResolution.y);
  float camZ = iTime * SPEED;
  vec2 camOffs = TunnelPath(camZ);

  for(int i = 1; i <= TUNNEL_LAYERS; i++){
    float pz = 1.0 - (float(i) / float(TUNNEL_LAYERS));
    pz -= mod(camZ, 4.0 / float(TUNNEL_LAYERS));
    vec2 offs = TunnelPath(camZ + pz) - camOffs;
    float ringRad = 0.15 * (1.0 / sq(pz * 0.8 + 0.4));
    if(abs(length(uv + offs) - ringRad) < pointSize * 1.5){
      vec2 aruv = AngRep(uv + offs, repAngle);
      float pdist = sdCircle(aruv - vec2(ringRad, 0), pointSize);
      vec3 ptColor = (mod(float(i/2), 2.0) == 0.0) ? POINT_COLOR_A : POINT_COLOR_B;
      float shade = (1.0 - pz);
      color = MixShape(pdist, ptColor * shade, color);
    }
  }

  gl_FragColor = vec4(color, 1.0);
}
`;

type ThreeContext = {
  renderer: THREE.WebGLRenderer;
  scene: THREE.Scene;
  camera: THREE.OrthographicCamera;
  material: THREE.ShaderMaterial;
  mesh: THREE.Mesh;
  geometry: THREE.PlaneGeometry;
};

function createThreeForCanvas(canvas: HTMLCanvasElement, width: number, height: number): ThreeContext {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  renderer.setPixelRatio(dpr);
  renderer.setSize(width, height);

  const scene = new THREE.Scene();
  const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  const material = new THREE.ShaderMaterial({
    uniforms: {
      iTime: { value: 0 },
      iResolution: { value: new THREE.Vector3(width, height, 1) },
    },
    vertexShader,
    fragmentShader,
  });

  const geometry = new THREE.PlaneGeometry(2, 2);
  const mesh = new THREE.Mesh(geometry, material);
  scene.add(mesh);

  return { renderer, scene, camera, material, mesh, geometry };
}

function disposeThree(ctx: ThreeContext) {
  try {
    ctx.scene.remove(ctx.mesh);
    ctx.mesh.geometry.dispose();
    ctx.material.dispose();
    ctx.renderer.dispose();
  } catch {
    /* ignore disposal errors */
  }
}

export default function AetherBackground({
  overlayGradient = 'linear-gradient(180deg, rgba(0, 0, 0, 0.4) 0%, rgba(0, 0, 0, 0.15) 40%, rgba(0, 0, 0, 0.45) 100%)',
  className = '',
}: AetherBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const ctxRef = useRef<ThreeContext | null>(null);
  const lastTimeRef = useRef<number>(0);
  const animRef = useRef<number | null>(null);
  const pausedRef = useRef<boolean>(false);
  const rafResizeRef = useRef<boolean>(false);

  const [waveEnabled, setWaveEnabled] = useState(
    () => localStorage.getItem('shieldscan_wave_enabled') !== 'false'
  );

  useEffect(() => {
    const handleToggle = () => {
      setWaveEnabled(localStorage.getItem('shieldscan_wave_enabled') !== 'false');
    };
    window.addEventListener('shieldscan_wave_toggle', handleToggle);
    return () => window.removeEventListener('shieldscan_wave_toggle', handleToggle);
  }, []);

  const animate = useCallback((time: number) => {
    if (!ctxRef.current) return;
    animRef.current = requestAnimationFrame(animate);

    time *= 0.001; // ms -> s
    const delta = time - (lastTimeRef.current || time);
    lastTimeRef.current = time;

    if (!pausedRef.current && waveEnabled) {
      ctxRef.current.material.uniforms.iTime.value += delta * 0.5;
    }
    ctxRef.current.renderer.render(ctxRef.current.scene, ctxRef.current.camera);
  }, [waveEnabled]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || typeof window === 'undefined') return;

    const width = window.innerWidth;
    const height = window.innerHeight;
    const ctx = createThreeForCanvas(canvas, width, height);
    ctxRef.current = ctx;

    const handleResize = () => {
      if (!ctxRef.current) return;
      if (rafResizeRef.current) return;
      rafResizeRef.current = true;
      requestAnimationFrame(() => {
        rafResizeRef.current = false;
        const w = window.innerWidth;
        const h = window.innerHeight;
        ctxRef.current!.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
        ctxRef.current!.renderer.setSize(w, h);
        (ctxRef.current!.material.uniforms.iResolution.value as THREE.Vector3).set(w, h, 1);
      });
    };
    window.addEventListener('resize', handleResize);

    const handleVisibility = () => {
      pausedRef.current = !!document.hidden;
    };
    document.addEventListener('visibilitychange', handleVisibility);
    handleVisibility();

    animRef.current = requestAnimationFrame(animate);

    return () => {
      if (animRef.current) cancelAnimationFrame(animRef.current);
      window.removeEventListener('resize', handleResize);
      document.removeEventListener('visibilitychange', handleVisibility);
      if (ctxRef.current) {
        disposeThree(ctxRef.current);
        ctxRef.current = null;
      }
    };
  }, [animate]);

  return (
    <div
      className={`aether-bg-fixed ${className}`}
      style={{
        position: 'fixed',
        inset: 0,
        width: '100vw',
        height: '100vh',
        zIndex: 0,
        pointerEvents: 'none',
        overflow: 'hidden',
      }}
    >
      <canvas
        ref={canvasRef}
        role="img"
        aria-label="Infinite 3D Tunnel background"
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          display: 'block',
          userSelect: 'none',
          touchAction: 'none',
        }}
      />
      {/* Overlay gradient to keep website text and UI sharp & readable */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          background: overlayGradient,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
}
