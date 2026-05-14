import { cn } from "@/lib/utils";

type Variant = "default" | "text" | "image" | "audio" | "success" | "warning" | "error" | "info";

const variants: Record<Variant, string> = {
  default: "bg-white/8 text-white/70",
  text: "bg-blue-500/20 text-blue-400 border border-blue-500/30",
  image: "bg-amber-500/18 text-amber-300 border border-amber-500/28",
  audio: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
  success: "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30",
  warning: "bg-amber-500/20 text-amber-400 border border-amber-500/30",
  error: "bg-red-500/20 text-red-400 border border-red-500/30",
  info: "bg-cyan-500/20 text-cyan-400 border border-cyan-500/30",
};

export function Badge({
  children,
  variant = "default",
  className,
}: {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
