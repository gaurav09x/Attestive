import { motion } from "framer-motion";
import { weekdayLabel } from "../lib/format";
import type { DashboardResponse } from "../lib/types";

export function ActivityChart({ days }: { days: DashboardResponse["activity_series"] }) {
  const max = Math.max(30, ...days.map((day) => day.minutes));
  const total = days.reduce((sum, day) => sum + day.minutes, 0);

  return (
    <div>
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-fog-200">Last 7 days</p>
          <p className="mt-0.5 text-xs text-fog-500">
            {total > 0 ? `${total} minutes of real study time` : "No study time recorded yet"}
          </p>
        </div>
        <p className="font-mono text-xs text-fog-500">max {max}m</p>
      </div>

      <div className="mt-5 flex h-40 items-end gap-2 sm:gap-3" role="img" aria-label="Study minutes over the last seven days">
        {days.map((day, index) => {
          const height = day.minutes > 0 ? Math.max(6, (day.minutes / max) * 100) : 3;
          return (
            <div key={day.day} className="flex flex-1 flex-col items-center gap-2">
              <div className="flex h-32 w-full items-end">
                <motion.div
                  initial={{ height: 0 }}
                  animate={{ height: `${height}%` }}
                  transition={{ duration: 0.6, delay: index * 0.05, ease: [0.16, 1, 0.3, 1] }}
                  className="w-full rounded-t-[4px] bg-ink-700"
                  title={`${day.minutes} minutes`}
                >
                  {day.minutes > 0 ? (
                    <div className="h-full w-full rounded-t-[4px] bg-gradient-to-t from-electric/25 via-electric/60 to-cyan/90" />
                  ) : null}
                </motion.div>
              </div>
              <span className="text-[11px] text-fog-500">{weekdayLabel(day.day)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function RadialProgress({
  value,
  size = 132,
  label,
  caption,
}: {
  value: number;
  size?: number;
  label: string;
  caption?: string;
}) {
  const stroke = 9;
  const radius = (size - stroke) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90" aria-hidden>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(30,39,57,0.9)"
          strokeWidth={stroke}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="url(#radial-gradient)"
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference - (clamped / 100) * circumference }}
          transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
        />
        <defs>
          <linearGradient id="radial-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#4c8dff" />
            <stop offset="100%" stopColor="#9a7bff" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-2xl font-semibold tracking-tight">{label}</span>
        {caption ? <span className="mt-0.5 text-[11px] text-fog-500">{caption}</span> : null}
      </div>
    </div>
  );
}
