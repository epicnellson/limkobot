import { useState } from "react"
import { Link } from "react-router-dom"
import { FileText, Plus, SearchX } from "lucide-react"
import ErrorState from "@/components/shared/ErrorState"
import PageHeader from "@/components/layout/PageHeader"
import SearchField from "@/components/shared/SearchField"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { useApiData } from "@/hooks/use-api-data"
import { getUser } from "@/lib/api"
import { formatDate } from "@/lib/format"

const sourceLabels = {
    manual: "Manual entry",
    pdf: "PDF",
    txt: "Text",
    md: "Markdown",
    markdown: "Markdown",
    html: "HTML",
    htm: "HTML",
}

function sourceLabel(value) {
    if (!value) return "—"
    return sourceLabels[value.toLowerCase()] ?? value
}

export default function KnowledgeBase() {
    const [query, setQuery] = useState("")
    const isAdmin = getUser()?.role === "admin"
    const { data, error, isLoading, refetch } = useApiData("/documents")

    const allDocuments = data ?? []
    const normalizedQuery = query.trim().toLowerCase()
    const visibleDocuments = normalizedQuery
        ? allDocuments.filter((document) =>
              [document.title, document.category, document.source_type].some((value) =>
                  String(value ?? "")
                      .toLowerCase()
                      .includes(normalizedQuery)
              )
          )
        : allDocuments

    return (
        <>
            <PageHeader
                title="Knowledge Base"
                description="Documents the assistant uses when answering student questions."
                actions={
                    isAdmin ? (
                        <Link
                            to="/knowledge-base/upload"
                            className={buttonVariants()}
                        >
                            <Plus />
                            Add knowledge
                        </Link>
                    ) : null
                }
            />

            <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
                <div className="flex flex-col gap-3 border-b px-(--surface-padding) py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h2 className="text-sm font-semibold">Documents</h2>
                        <p className="mt-0.5 text-xs text-muted-foreground tabular-nums">
                            {error
                                ? "Couldn't load documents"
                                : isLoading
                                  ? "Loading documents…"
                                  : `${visibleDocuments.length} of ${allDocuments.length} shown`}
                        </p>
                    </div>
                    <SearchField
                        value={query}
                        onChange={setQuery}
                        label="Search documents"
                        placeholder="Search title, category or source…"
                        className="w-full sm:w-72"
                    />
                </div>

                {error ? (
                    <ErrorState
                        title="Documents unavailable"
                        message={error.message}
                        onRetry={refetch}
                    />
                ) : isLoading ? (
                    <div className="p-(--surface-padding)">
                        <div className="space-y-3">
                            {[0, 1, 2, 3].map((row) => (
                                <div key={row} className="grid grid-cols-4 gap-6">
                                    <Skeleton className="col-span-2 h-4" />
                                    <Skeleton className="h-4" />
                                    <Skeleton className="h-4" />
                                </div>
                            ))}
                        </div>
                    </div>
                ) : allDocuments.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 p-10 text-center">
                        <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                            <FileText className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                            <p className="text-sm font-medium">No documents yet</p>
                            <p className="mt-1 max-w-sm text-sm text-pretty text-muted-foreground">
                                Upload a file or add text so the assistant has something
                                to answer from.
                            </p>
                        </div>
                    </div>
                ) : visibleDocuments.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 p-10 text-center">
                        <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                            <SearchX className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                            <p className="text-sm font-medium">No matching documents</p>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Try a different title, category or source.
                            </p>
                        </div>
                        <Button variant="outline" size="sm" onClick={() => setQuery("")}>
                            Clear search
                        </Button>
                    </div>
                ) : (
                    <div className="p-(--surface-padding)">
                        <div className="overflow-hidden rounded-nested border">
                            <Table>
                                <TableHeader className="bg-muted/60">
                                    <TableRow className="hover:bg-transparent">
                                        <TableHead className="px-3 text-xs">Title</TableHead>
                                        <TableHead className="px-3 text-xs">Category</TableHead>
                                        <TableHead className="px-3 text-xs">Source</TableHead>
                                        <TableHead className="px-3 text-xs">Added</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {visibleDocuments.map((document) => (
                                        <TableRow key={document.id}>
                                            <TableCell className="px-3 py-3 font-medium">
                                                <span className="flex items-center gap-3">
                                                    <FileText
                                                        className="size-4 shrink-0 text-muted-foreground"
                                                        aria-hidden="true"
                                                    />
                                                    {document.title || "Untitled"}
                                                </span>
                                            </TableCell>
                                            <TableCell className="px-3 py-3 text-muted-foreground">
                                                {document.category || "—"}
                                            </TableCell>
                                            <TableCell className="px-3 py-3 text-muted-foreground">
                                                {sourceLabel(document.source_type)}
                                            </TableCell>
                                            <TableCell className="px-3 py-3 text-muted-foreground tabular-nums">
                                                {formatDate(document.created_at)}
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </div>
                    </div>
                )}
            </Card>
        </>
    )
}
