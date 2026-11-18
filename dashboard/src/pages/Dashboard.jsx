import { Link } from "react-router-dom"
import {
    ArrowRight,
    BookOpenText,
    ChevronRight,
    CircleCheck,
    Flag,
    MessageSquare,
    Upload,
    UsersRound,
} from "lucide-react"
import ErrorState from "@/components/shared/ErrorState"
import PageHeader from "@/components/layout/PageHeader"
import StatCard from "@/components/shared/StatCard"
import StatusDot from "@/components/shared/StatusDot"
import { buttonVariants } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { useApiData } from "@/hooks/use-api-data"
import { getUser } from "@/lib/api"
import { formatDateTime } from "@/lib/format"
import { cn } from "@/lib/utils"

const shortcuts = [
    {
        to: "/knowledge-base/upload",
        label: "Add knowledge",
        icon: Upload,
        adminOnly: true,
    },
    { to: "/knowledge-base", label: "Browse knowledge documents", icon: BookOpenText },
    { to: "/students", label: "Look up a student", icon: UsersRound },
    { to: "/flagged", label: "Review flagged conversations", icon: Flag },
]

const severityTones = { high: "high", medium: "medium", low: "low" }

function severityTone(value) {
    return severityTones[String(value ?? "").toLowerCase()] ?? "neutral"
}

function severityLabel(value) {
    const label = String(value ?? "")
    return label ? label.charAt(0).toUpperCase() + label.slice(1) : "Flagged"
}

export default function Dashboard() {
    const isAdmin = getUser()?.role === "admin"
    const visibleShortcuts = shortcuts.filter((item) => !item.adminOnly || isAdmin)
    const statsRequest = useApiData("/admin/dashboard/stats")
    const flagsRequest = useApiData("/admin/flags", {
        params: { resolved: false },
    })

    const stats = statsRequest.data
    const messageCount = stats?.messages
    const openFlags = flagsRequest.data ?? []
    const recentFlags = openFlags.slice(0, 3)

    const metrics = [
        {
            label: "Users",
            value: stats?.users ?? "—",
            hint: "Registered accounts",
            icon: UsersRound,
            loading: statsRequest.isLoading,
        },
        {
            label: "Open flags",
            value: flagsRequest.error ? "—" : openFlags.length,
            hint: "Awaiting review",
            icon: Flag,
            loading: flagsRequest.isLoading,
        },
        {
            label: "Knowledge documents",
            value: stats?.documents ?? "—",
            hint: "Available to the assistant",
            icon: BookOpenText,
            loading: statsRequest.isLoading,
        },
        {
            label: "Conversations",
            value: stats?.conversations ?? "—",
            hint:
                messageCount === undefined
                    ? "All channels"
                    : `${messageCount.toLocaleString()} ${
                          messageCount === 1 ? "message" : "messages"
                      }`,
            icon: MessageSquare,
            loading: statsRequest.isLoading,
        },
    ]

    return (
        <>
            <PageHeader
                title="Dashboard overview"
                description="A snapshot of student activity and the queues that need your attention."
                actions={
                    <Link to="/flagged" className={buttonVariants()}>
                        Review flags
                        <ArrowRight />
                    </Link>
                }
            />

            <section
                aria-label="Key metrics"
                className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4"
            >
                {statsRequest.error ? (
                    <Card className="col-span-full gap-0 rounded-surface py-0">
                        <ErrorState
                            title="Metrics unavailable"
                            message={statsRequest.error.message}
                            onRetry={statsRequest.refetch}
                        />
                    </Card>
                ) : (
                    metrics.map((metric) => (
                        <StatCard key={metric.label} {...metric} />
                    ))
                )}
            </section>

            <div className="mt-6 grid gap-4 lg:grid-cols-3">
                <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)] lg:col-span-2">
                    <div className="flex items-center justify-between gap-3 border-b px-(--surface-padding) py-3">
                        <h2 className="text-sm font-semibold">Needs attention</h2>
                        {flagsRequest.isLoading || flagsRequest.error ? null : (
                            <span className="text-xs text-muted-foreground tabular-nums">
                                {openFlags.length} open
                            </span>
                        )}
                    </div>

                    {flagsRequest.error ? (
                        <ErrorState
                            title="Flags unavailable"
                            message={flagsRequest.error.message}
                            onRetry={flagsRequest.refetch}
                            className="p-6"
                        />
                    ) : flagsRequest.isLoading ? (
                        <div className="space-y-4 p-(--surface-padding)">
                            {[0, 1].map((item) => (
                                <div key={item} className="space-y-2">
                                    <Skeleton className="h-3 w-24" />
                                    <Skeleton className="h-4 w-3/4" />
                                </div>
                            ))}
                        </div>
                    ) : recentFlags.length === 0 ? (
                        <div className="flex flex-col items-center gap-3 p-8 text-center">
                            <span className="grid size-10 place-items-center rounded-nested bg-success/10 text-success">
                                <CircleCheck className="size-4" aria-hidden="true" />
                            </span>
                            <div>
                                <p className="text-sm font-medium">No open flags</p>
                                <p className="mt-1 text-sm text-muted-foreground">
                                    Messages escalated by the assistant will appear here.
                                </p>
                            </div>
                        </div>
                    ) : (
                        <ul className="divide-y">
                            {recentFlags.map((flag) => (
                                <li
                                    key={flag.flag_id}
                                    className="px-(--surface-padding) py-3"
                                >
                                    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1">
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
                                    <p className="mt-1.5 line-clamp-2 text-sm text-pretty text-muted-foreground">
                                        {flag.message_text || "No message text recorded."}
                                    </p>
                                </li>
                            ))}
                        </ul>
                    )}

                    <div className="border-t px-(--surface-padding) py-2">
                        <Link
                            to="/flagged"
                            className={cn(
                                buttonVariants({ variant: "link", size: "sm" }),
                                "px-0"
                            )}
                        >
                            View all conversations
                            <ArrowRight />
                        </Link>
                    </div>
                </Card>

                <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
                    <div className="border-b px-(--surface-padding) py-3">
                        <h2 className="text-sm font-semibold">Shortcuts</h2>
                    </div>
                    <nav aria-label="Shortcuts" className="p-(--surface-padding)">
                        {visibleShortcuts.map(({ to, label, icon: Icon }) => (
                            <Link
                                key={to}
                                to={to}
                                className="flex items-center gap-3 rounded-nested px-2 py-2.5 text-sm transition-colors hover:bg-muted"
                            >
                                <Icon
                                    className="size-4 shrink-0 text-muted-foreground"
                                    aria-hidden="true"
                                />
                                <span className="min-w-0 flex-1 text-balance">{label}</span>
                                <ChevronRight
                                    className="size-4 shrink-0 text-muted-foreground"
                                    aria-hidden="true"
                                />
                            </Link>
                        ))}
                    </nav>
                </Card>
            </div>
        </>
    )
}
