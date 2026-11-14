import { motion, useReducedMotion } from "framer-motion";
import { cn } from "../components/ui";

const tilePop = { type: "spring", stiffness: 300, damping: 22, mass: 0.7 } as const;

/**
 * Attestive mark: a check whose long arm rises — attestation and ascent in one
 * stroke. Geometry matches `public/attestive-mark.svg` (the favicon); keep the
 * two in step when editing (this file's viewBox is 32, the favicon's is 64).
 *
 * Motion: the tile springs in, the check draws itself, then a light sweeps
 * across the tile every few seconds. Everything is skipped when the visitor
 * asks for reduced motion.
 */
export function LogoMark({ className }: { className?: string }) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.span
      initial={reduceMotion ? false : { scale: 0.8, opacity: 0, rotate: -10 }}
      animate={{ scale: 1, opacity: 1, rotate: 0 }}
      transition={reduceMotion ? { duration: 0 } : tilePop}
      className={cn(
        "relative flex size-8 items-center justify-center overflow-hidden rounded-lg bg-gradient-to-br from-electric via-[#6f8cff] to-violet shadow-[0_0_24px_-6px_rgba(107,124,255,0.8)]",
        className,
      )}
    >
      {reduceMotion ? null : (
        <motion.span
          aria-hidden
          className="pointer-events-none absolute inset-y-0 w-1/2 bg-gradient-to-r from-transparent via-white/45 to-transparent"
          initial={{ x: "-160%", skewX: -14 }}
          animate={{ x: "260%" }}
          transition={{
            duration: 1.15,
            ease: "easeInOut",
            repeat: Infinity,
            repeatDelay: 4.2,
            delay: 1.4,
          }}
        />
      )}
      <svg viewBox="0 0 32 32" className="relative size-5" fill="none" aria-hidden>
        <motion.path
          d="M7.6 20.4 13.6 26.4 25.4 7.6"
          stroke="white"
          strokeWidth="3.2"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={reduceMotion ? false : { pathLength: 0, opacity: 0.35 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={
            reduceMotion
              ? { duration: 0 }
              : {
                  pathLength: { duration: 0.75, ease: "easeInOut", delay: 0.18 },
                  opacity: { duration: 0.3, delay: 0.18 },
                }
          }
        />
      </svg>
    </motion.span>
  );
}

export function Logo({ className, withWordmark = true }: { className?: string; withWordmark?: boolean }) {
  const reduceMotion = useReducedMotion();

  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark />
      {withWordmark ? (
        <motion.span
          initial={reduceMotion ? false : { opacity: 0, x: -4 }}
          animate={{ opacity: 1, x: 0 }}
          transition={reduceMotion ? { duration: 0 } : { duration: 0.45, delay: 0.15, ease: "easeOut" }}
          className="text-[15px] font-semibold tracking-tight text-fog-100"
        >
          Attest<span className="text-fog-400">ive</span>
        </motion.span>
      ) : null}
    </span>
  );
}
