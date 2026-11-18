import { cn } from "@/lib/utils"

const tones = {
    neutral: "bg-muted-foreground/50",
    high: "bg-destructive",
    medium: "bg-warning",
    low: "bg-success",
    resolved: "bg-success",
    pending: "bg-warning",
}

export default function StatusDot({ tone = "neutral", children, className }) {
    return (
        <span className={cn("inline-flex items-center gap-2 text-sm", className)}>
            <span
                aria-hidden="true"
                className={cn("size-1.5 shrink-0 rounded-full", tones[tone])}
            />
            {children}
        </span>
    )
}
