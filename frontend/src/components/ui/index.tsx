import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";

export function cn(...classes: (string | false | null | undefined)[]): string {
  return classes.filter(Boolean).join(" ");
}

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg";

const buttonVariants: Record<ButtonVariant, string> = {
  primary:
    "bg-gradient-to-r from-electric to-violet text-white shadow-[0_8px_30px_-12px_rgba(76,141,255,0.65)] hover:brightness-110",
  secondary:
    "border border-line-bright bg-ink-800/80 text-fog-100 hover:border-electric/60 hover:bg-ink-700",
  ghost: "text-fog-300 hover:bg-ink-700/70 hover:text-fog-100",
  danger: "border border-rose/40 bg-rose/10 text-rose hover:bg-rose/20",
};

const buttonSizes: Record<ButtonSize, string> = {
  sm: "h-9 px-3.5 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-[15px]",
};

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  { variant = "primary", size = "md", loading = false, className, children, disabled, ...props },
  ref,
) {
  return (
    <button
      ref={ref}
      disabled={disabled || loading}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200",
        "disabled:cursor-not-allowed disabled:opacity-50",
        buttonVariants[variant],
        buttonSizes[size],
        className,
      )}
      {...props}
    >
      {loading ? <Loader2 className="size-4 animate-spin" aria-hidden /> : null}
      {children}
    </button>
  );
});

export function Panel({
  children,
  className,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article";
}) {
  return (
    <Tag className={cn("rounded-xl border border-line bg-ink-850/80 backdrop-blur-sm", className)}>
      {children}
    </Tag>
  );
}

type BadgeTone = "neutral" | "blue" | "violet" | "emerald" | "amber" | "rose";

const badgeTones: Record<BadgeTone, string> = {
  neutral: "border-line-bright bg-ink-700 text-fog-300",
  blue: "border-electric/35 bg-electric/10 text-[#9cc0ff]",
  violet: "border-violet/35 bg-violet/10 text-[#c4b2ff]",
  emerald: "border-emerald/35 bg-emerald/10 text-emerald",
  amber: "border-amber/35 bg-amber/10 text-amber",
  rose: "border-rose/35 bg-rose/10 text-rose",
};

export function Badge({
  children,
  tone = "neutral",
  className,
}: {
  children: ReactNode;
  tone?: BadgeTone;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        badgeTones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Field({
  label,
  htmlFor,
  hint,
  error,
  children,
  optional = false,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  children: ReactNode;
  optional?: boolean;
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={htmlFor} className="text-sm font-medium text-fog-200">
          {label}
        </label>
        {optional ? <span className="text-xs text-fog-500">Optional</span> : null}
      </div>
      {children}
      {error ? (
        <p className="flex items-start gap-1.5 text-xs text-rose" id={`${htmlFor}-error`}>
          <AlertCircle className="mt-0.5 size-3.5 shrink-0" aria-hidden />
          {error}
        </p>
      ) : hint ? (
        <p className="text-xs text-fog-500">{hint}</p>
      ) : null}
    </div>
  );
}

const fieldBase =
  "w-full rounded-lg border bg-ink-900/80 px-3.5 text-sm text-fog-100 placeholder:text-fog-500 transition-colors focus:border-electric/70 focus:outline-none focus:ring-2 focus:ring-electric/20 disabled:opacity-60";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }>(
  function Input({ className, invalid, ...props }, ref) {
    return (
      <input
        ref={ref}
        aria-invalid={invalid || undefined}
        className={cn(fieldBase, "h-11", invalid ? "border-rose/60" : "border-line", className)}
        {...props}
      />
    );
  },
);

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  TextareaHTMLAttributes<HTMLTextAreaElement> & { invalid?: boolean }
>(function Textarea({ className, invalid, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      aria-invalid={invalid || undefined}
      className={cn(
        fieldBase,
        "min-h-24 py-2.5",
        invalid ? "border-rose/60" : "border-line",
        className,
      )}
      {...props}
    />
  );
});

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  function Select({ className, children, ...props }, ref) {
    return (
      <select ref={ref} className={cn(fieldBase, "h-11 appearance-none border-line pr-9", className)} {...props}>
        {children}
      </select>
    );
  },
);

export function Progress({
  value,
  className,
  tone = "blue",
}: {
  value: number;
  className?: string;
  tone?: "blue" | "violet" | "emerald";
}) {
  const gradients = {
    blue: "from-electric to-cyan",
    violet: "from-violet to-electric",
    emerald: "from-emerald to-cyan",
  };
  return (
    <div
      className={cn("h-1.5 w-full overflow-hidden rounded-full bg-ink-700", className)}
      role="progressbar"
      aria-valuenow={Math.round(value)}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
        className={cn("h-full rounded-full bg-gradient-to-r", gradients[tone])}
      />
    </div>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-10 text-sm text-fog-400" role="status">
      <Loader2 className="size-4 animate-spin" aria-hidden />
      {label}
    </div>
  );
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  compact = false,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-line bg-ink-900/40 text-center",
        compact ? "px-4 py-6" : "px-6 py-10",
      )}
    >
      <div className="mb-3 flex size-10 items-center justify-center rounded-lg border border-line bg-ink-800 text-fog-400">
        {icon}
      </div>
      <h3 className="text-sm font-semibold text-fog-100">{title}</h3>
      <p className="mt-1.5 max-w-sm text-sm leading-relaxed text-fog-400">{description}</p>
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function Alert({
  tone = "error",
  children,
}: {
  tone?: "error" | "success" | "info";
  children: ReactNode;
}) {
  const tones = {
    error: "border-rose/30 bg-rose/10 text-rose",
    success: "border-emerald/30 bg-emerald/10 text-emerald",
    info: "border-electric/30 bg-electric/10 text-[#a9c7ff]",
  };
  const Icon = tone === "success" ? CheckCircle2 : AlertCircle;
  return (
    <motion.div
      initial={{ opacity: 0, y: -4 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("flex items-start gap-2 rounded-lg border px-3.5 py-3 text-sm", tones[tone])}
      role={tone === "error" ? "alert" : "status"}
    >
      <Icon className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="leading-relaxed">{children}</div>
    </motion.div>
  );
}

export function AnimatedList({ children }: { children: ReactNode }) {
  return <AnimatePresence initial={false}>{children}</AnimatePresence>;
}
