import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

export default function StatCard({ label, value, hint, icon: Icon, loading = false }) {
    return (
        <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
            <div className="p-(--surface-padding)">
                {loading ? (
                    <div className="space-y-3">
                        <Skeleton className="h-4 w-28" />
                        <Skeleton className="h-9 w-16" />
                        <Skeleton className="h-3 w-24" />
                    </div>
                ) : (
                    <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                            <p className="text-sm text-muted-foreground">{label}</p>
                            <p className="mt-2 text-3xl font-semibold tracking-tight tabular-nums">
                                {value}
                            </p>
                            {hint ? (
                                <p className="mt-1 text-xs text-muted-foreground">
                                    {hint}
                                </p>
                            ) : null}
                        </div>
                        <span className="grid size-9 shrink-0 place-items-center rounded-nested bg-accent text-accent-foreground">
                            <Icon className="size-4" aria-hidden="true" />
                        </span>
                    </div>
                )}
            </div>
        </Card>
    )
}
