import { useState } from "react"
import { CircleCheck, CircleDashed, SearchX, UserRound } from "lucide-react"
import ErrorState from "@/components/shared/ErrorState"
import PageHeader from "@/components/layout/PageHeader"
import SearchField from "@/components/shared/SearchField"
import { Button } from "@/components/ui/button"
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

export default function StudentLookup() {
    const [query, setQuery] = useState("")
    const { data, error, isLoading, refetch } = useApiData("/admin/users")

    const allStudents = (data ?? []).filter((account) => account.role === "student")
    const normalizedQuery = query.trim().toLowerCase()
    const visibleStudents = normalizedQuery
        ? allStudents.filter((student) =>
              [student.full_name, student.phone, student.student_id].some((value) =>
                  String(value ?? "")
                      .toLowerCase()
                      .includes(normalizedQuery)
              )
          )
        : allStudents

    return (
        <>
            <PageHeader
                title="Student Lookup"
                description="Find a student by name, phone number or student ID."
            />

            <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
                <div className="flex flex-col gap-3 border-b px-(--surface-padding) py-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                        <h2 className="text-sm font-semibold">Students</h2>
                        <p className="mt-0.5 text-xs text-muted-foreground tabular-nums">
                            {error
                                ? "Couldn't load students"
                                : isLoading
                                  ? "Loading students…"
                                  : `${visibleStudents.length} of ${allStudents.length} shown`}
                        </p>
                    </div>
                    <SearchField
                        value={query}
                        onChange={setQuery}
                        label="Search students"
                        placeholder="Name, phone or student ID…"
                        className="w-full sm:w-72"
                    />
                </div>

                {error ? (
                    <ErrorState
                        title="Students unavailable"
                        message={error.message}
                        onRetry={refetch}
                    />
                ) : isLoading ? (
                    <div className="p-(--surface-padding)">
                        <div className="space-y-3">
                            {[0, 1, 2].map((row) => (
                                <div key={row} className="grid grid-cols-4 gap-6">
                                    <Skeleton className="h-4" />
                                    <Skeleton className="h-4" />
                                    <Skeleton className="h-4" />
                                    <Skeleton className="h-4" />
                                </div>
                            ))}
                        </div>
                    </div>
                ) : allStudents.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 p-10 text-center">
                        <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                            <UserRound className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                            <p className="text-sm font-medium">No students yet</p>
                            <p className="mt-1 max-w-sm text-sm text-pretty text-muted-foreground">
                                Student accounts will appear here once they are created.
                            </p>
                        </div>
                    </div>
                ) : visibleStudents.length === 0 ? (
                    <div className="flex flex-col items-center gap-3 p-10 text-center">
                        <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                            <SearchX className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                            <p className="text-sm font-medium">No students found</p>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Check the name, phone or student ID and try again.
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
                                        <TableHead className="px-3 text-xs">Student</TableHead>
                                        <TableHead className="px-3 text-xs">Phone</TableHead>
                                        <TableHead className="px-3 text-xs">Student ID</TableHead>
                                        <TableHead className="px-3 text-xs">Verification</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {visibleStudents.map((student) => (
                                        <TableRow key={student.id}>
                                            <TableCell className="px-3 py-3 font-medium">
                                                <span className="flex items-center gap-3">
                                                    <UserRound
                                                        className="size-4 shrink-0 text-muted-foreground"
                                                        aria-hidden="true"
                                                    />
                                                    {student.full_name || "Unnamed student"}
                                                </span>
                                            </TableCell>
                                            <TableCell className="px-3 py-3 text-muted-foreground tabular-nums">
                                                {student.phone || "—"}
                                            </TableCell>
                                            <TableCell className="px-3 py-3 text-muted-foreground tabular-nums">
                                                {student.student_id || "—"}
                                            </TableCell>
                                            <TableCell className="px-3 py-3">
                                                <span
                                                    className={
                                                        student.is_verified
                                                            ? "inline-flex items-center gap-1.5 text-xs text-success"
                                                            : "inline-flex items-center gap-1.5 text-xs text-muted-foreground"
                                                    }
                                                >
                                                    {student.is_verified ? (
                                                        <CircleCheck
                                                            className="size-4"
                                                            aria-hidden="true"
                                                        />
                                                    ) : (
                                                        <CircleDashed
                                                            className="size-4"
                                                            aria-hidden="true"
                                                        />
                                                    )}
                                                    {student.is_verified
                                                        ? "Verified"
                                                        : "Not verified"}
                                                </span>
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
