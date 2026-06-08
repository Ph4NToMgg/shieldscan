import { useEffect, useRef } from 'react';

interface ScoreCardProps {
  score: number;
  totalChecks: number;
  passed: number;
  failed: number;
}

function getScoreRawColor(score: number): string {
  if (score >= 80) return '#22c55e';
  if (score >= 60) return '#84cc16';
  if (score >= 40) return '#f59e0b';
  return '#ef4444';
}

function getScoreLabel(score: number): string {
  if (score >= 80) return 'EXCELLENT';
  if (score >= 60) return 'GOOD';
  if (score >= 40) return 'FAIR';
  return 'CRITICAL';
}

function padNumber(n: number): string {
  return n.toString().padStart(2, '0');
}

/* Arc geometry — semicircle from left to right */
const ARC_WIDTH = 200;
const ARC_HEIGHT = 120;
const STROKE = 8;
const CX = ARC_WIDTH / 2;
const CY = ARC_HEIGHT - 4;
const RADIUS = 82;

/* semicircle path: from left to right (180° arc) */
function describeArc(): string {
  const startX = CX - RADIUS;
  const startY = CY;
  const endX = CX + RADIUS;
  const endY = CY;
  return `M ${startX} ${startY} A ${RADIUS} ${RADIUS} 0 0 1 ${endX} ${endY}`;
}

const ARC_PATH = describeArc();

/* total arc length for a semicircle */
const ARC_LENGTH = Math.PI * RADIUS;

export default function ScoreCard({ score, totalChecks, passed, failed }: ScoreCardProps) {
  const rawColor = getScoreRawColor(score);
  const label = getScoreLabel(score);
  const arcRef = useRef<SVGPathElement>(null);
  const numberRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const arcEl = arcRef.current;
    const numEl = numberRef.current;
    if (!arcEl || !numEl) return;

    const targetOffset = ARC_LENGTH * (1 - score / 100);
    const duration = 600;
    const startTime = performance.now();

    /* start fully hidden */
    arcEl.style.strokeDasharray = `${ARC_LENGTH}`;
    arcEl.style.strokeDashoffset = `${ARC_LENGTH}`;

    function animate(now: number) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      /* ease-out cubic */
      const eased = 1 - Math.pow(1 - progress, 3);

      const currentOffset = ARC_LENGTH - eased * (ARC_LENGTH - targetOffset);
      if (arcEl) {
        arcEl.style.strokeDashoffset = `${currentOffset}`;
      }

      const currentScore = Math.round(eased * score);
      if (numEl) {
        numEl.textContent = String(currentScore);
      }

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    }

    requestAnimationFrame(animate);
  }, [score]);

  return (
    <div>
      {/* Arc gauge */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
      }}>
        <div style={{ position: 'relative', width: ARC_WIDTH, height: ARC_HEIGHT }}>
          <svg
            width={ARC_WIDTH}
            height={ARC_HEIGHT}
            viewBox={`0 0 ${ARC_WIDTH} ${ARC_HEIGHT}`}
            fill="none"
          >
            {/* Background arc */}
            <path
              d={ARC_PATH}
              stroke="var(--border)"
              strokeWidth={STROKE}
              strokeLinecap="round"
              fill="none"
            />
            {/* Foreground arc */}
            <path
              ref={arcRef}
              d={ARC_PATH}
              stroke={rawColor}
              strokeWidth={STROKE}
              strokeLinecap="round"
              fill="none"
            />
          </svg>

          {/* Score text centered in arc */}
          <div style={{
            position: 'absolute',
            left: '50%',
            bottom: 4,
            transform: 'translateX(-50%)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
          }}>
            <span
              ref={numberRef}
              style={{
                fontFamily: 'var(--font-display)',
                fontSize: 48,
                lineHeight: 1,
                color: rawColor,
              }}
            >
              0
            </span>
            <span style={{
              fontFamily: 'var(--font-mono)',
              fontSize: 12,
              color: 'var(--text-muted)',
              marginTop: 2,
            }}>
              /100
            </span>
          </div>
        </div>

        {/* Rating label */}
        <span style={{
          fontFamily: 'var(--font-mono)',
          fontSize: 11,
          fontWeight: 600,
          letterSpacing: '0.2em',
          textTransform: 'uppercase' as const,
          color: rawColor,
          marginTop: 12,
        }}>
          {label}
        </span>
      </div>

      {/* Stats row */}
      <div className="stats-row" style={{ marginTop: 24, justifyContent: 'center' }}>
        <span className="stat-item">{padNumber(totalChecks)} CHECKS</span>
        <span className="stat-divider">|</span>
        <span className="stat-item">{padNumber(passed)} PASSED</span>
        <span className="stat-divider">|</span>
        <span className="stat-item">{padNumber(failed)} FAILED</span>
      </div>

      {/* Weighted scoring note */}
      <p style={{
        fontFamily: 'var(--font-mono)',
        fontSize: 11,
        color: 'var(--text-muted)',
        marginTop: 12,
        textAlign: 'center',
      }}>
        * Score is weighted by severity. Critical issues have greater impact.
      </p>
    </div>
  );
}
