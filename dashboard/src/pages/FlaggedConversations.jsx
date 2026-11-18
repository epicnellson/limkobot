import { useState } from "react"
import { CheckCircle2, CircleDashed, Inbox } from "lucide-react"
import ErrorState from "@/components/shared/ErrorState"
import PageHeader from "@/components/layout/PageHeader"
import StatusDot from "@/components/shared/StatusDot"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useApiData } from "@/hooks/use-api-data"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const severityTones = { high: "high", medium: "medium", low: "low" }
const filters = [
    { value: "open", label: "Open" },
    { value: "resolved", label: "Resolved" },
    { value: "all", label: "All" },
]

function severityTone(value) {
    return severityTones[String(value ?? "").toLowerCase()] ?? "neutral"
}

function severityLabel(value) {
    const label = String(value ?? "")
    return label ? label.charAt(0).toUpperCase() + label.slice(1) : "Flagged"
}

function shortId(value) {
    return value ? String(value).slice(0, 8) : "—"
}

export default function FlaggedConversations() {
    const [filter, setFilter] = useState("open")
    const { data, error, isLoading, refetch } = useApiData("/admin/flags")

    const allFlags = [...(data ?? [])].sort(
        (left, right) =>
            new Date(right.timestamp ?? 0).getTime() -
            new Date(left.timestamp ?? 0).getTime()
    )
    const visibleFlags = allFlags.filter((flag) =>
        filter === "all" ? true : filter === "open" ? !flag.resolved : flag.resolved
    )
    const openCount = allFlags.filter((flag) => !flag.resolved).length

    return (
        <>
            <PageHeader
                title="Flagged Conversations"
                description={
                    error || isLoading ? (
                        "Messages escalated by the assistant."
                    ) : (
                        <>
                            Messages escalated by the assistant —{" "}
                            <span className="tabular-nums">{openCount}</span> open,{" "}
                            <span className="tabular-nums">{allFlags.length}</span> total.
                        </>
                    )
                }
            />

            <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
                <div className="flex flex-col gap-3 border-b px-(--surface-padding) py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div
                        className="flex items-center gap-1"
                        role="group"
                        aria-label="Filter conversations"
                    >
                        {filters.map((item) => (
                            <Button
                                key={item.value}
                                type="button"
                                size="sm"
                                variant={filter === item.value ? "secondary" : "ghost"}
                                aria-pressed={filter === item.value}
                                onClick={() => setFilter(item.value)}
                            >
                                {item.label}
                            </Button>
                        ))}
                    </div>
                    <p className="text-xs text-muted-foreground tabular-nums">
                        {error
                            ? "Unavailable"
                            : isLoading
                              ? "Loading flags…"
                              : `${visibleFlags.length} shown`}
                    </p>
                </div>

                {error ? (
                    <ErrorState
                        title="Flags unavailable"
                        message={error.message}
                        onRetry={refetch}
                    />
                ) : isLoading ? (
                    <div className="space-y-5 p-(--surface-padding)">
                        {[0, 1, 2].map((row) => (
                            <div key={row} className="space-y-2">
                                <Skeleton className="h-3 w-32" />
                                <Skeleton className="h-4 w-2/3" />
                                <Skeleton className="h-3 w-24" />
                            </div>
                        ))}
                    </div>
                ) : visibleFlags.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 p-10 text-center">
                        <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                            <Inbox className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                            <p className="text-sm font-medium">
                                {filter === "open"
                                    ? "Nothing needs review"
                                    : "No conversations here"}
                            </p>
                            <p className="mt-1 text-sm text-muted-foreground">
                                {filter === "open"
                                    ? "All escalated messages have been resolved."
                                    : "Try another filter to see more conversations."}
                            </p>
                        </div>
                    </div>
                ) : (
                    <ul className="divide-y">
                        {visibleFlags.map((flag) => (
                            <li
                                key={flag.flag_id}
                                className="flex flex-col gap-3 px-(--surface-padding) py-4 transition-colors hover:bg-muted/40 sm:flex-row sm:items-start sm:justify-between"
                            >
                                <div className="min-w-0">
                                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                                        <StatusDot
                                            tone={severityTone(flag.severity)}
                                            className="text-xs font-medium"
                                        >
                                            {severityLabel(flag.severity)} priority
                                        </StatusDot>
                                        <span className="text-xs text-muted-foreground tabular-nums">
                                            {formatDateTime(flag.timestamp)}
                                        </span>
                                    </div>
                                    <p className="mt-1.5 max-w-xl text-sm text-pretty">
                                        {flag.message_text || "No message text recorded."}
                                    </p>
                                    <p className="mt-1 text-xs text-muted-foreground">
                                        Conversation{" "}
                                        <span className="font-mono tabular-nums">
                                            {shortId(flag.log_id)}
                                        </span>
                                    </p>
                                </div>

                                <div className="flex shrink-0 items-center gap-3 sm:flex-col sm:items-end sm:gap-2">
                                    <span
                                        className={cn(
                                            "inline-flex items-center gap-1.5 text-xs",
                                            flag.resolved
                                                ? "text-success"
                                                : "text-muted-foreground"
                                        )}
                                    >
                                        {flag.resolved ? (
                                            <CheckCircle2
                                                className="size-4"
                                                aria-hidden="true"
                                            />
                                        ) : (
                                            <CircleDashed
                                                className="size-4"
                                                aria-hidden="true"
                                            />
                                        )}
                                        {flag.resolved ? "Resolved" : "Open"}
                                    </span>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </Card>
        </>
    )
}
