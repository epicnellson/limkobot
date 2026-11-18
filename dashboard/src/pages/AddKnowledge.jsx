import { useId, useRef, useState } from "react"
import { Link } from "react-router-dom"
import {
    AlignLeft,
    ArrowLeft,
    CircleAlert,
    CircleCheck,
    FileText,
    Inbox,
    ShieldAlert,
    Upload,
    X,
} from "lucide-react"
import PageHeader from "@/components/layout/PageHeader"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button, buttonVariants } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"
import { Textarea } from "@/components/ui/textarea"
import { api, getUser } from "@/lib/api"
import { cn } from "@/lib/utils"

const MAX_FILE_BYTES = 10 * 1024 * 1024
const ACCEPTED_EXTENSIONS = [".pdf", ".txt", ".md", ".markdown", ".html", ".htm"]
const ACCEPTED_TYPES =
    ".pdf,.txt,.md,.markdown,.html,.htm,application/pdf,text/plain,text/markdown,text/html"
const CATEGORY_SUGGESTIONS = [
    "Admissions",
    "Fees",
    "Programmes",
    "Academics",
    "Policies",
]

function formatBytes(bytes) {
    if (!bytes) return "0 KB"
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function formatTime(value) {
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return "Just now"
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
}

function fileTitle(file) {
    return file.name.replace(/\.[^.]+$/, "")
}

export default function AddKnowledge() {
    const user = getUser()
    const isAdmin = user?.role === "admin"
    const categoryListId = useId()

    const [mode, setMode] = useState("file")
    const [title, setTitle] = useState("")
    const [category, setCategory] = useState("")
    const [file, setFile] = useState(null)
    const [content, setContent] = useState("")
    const [isDragging, setIsDragging] = useState(false)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [status, setStatus] = useState(null)
    const [added, setAdded] = useState([])
    const fileInputRef = useRef(null)

    if (!isAdmin) {
        return (
            <>
                <PageHeader
                    title="Add knowledge"
                    description="Seed the assistant with documents and notes before retrieval is enabled."
                    actions={
                        <Link
                            to="/knowledge-base"
                            className={buttonVariants({ variant: "outline" })}
                        >
                            <ArrowLeft />
                            Back to library
                        </Link>
                    }
                />
                <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
                    <div className="flex flex-col items-center gap-3 p-10 text-center">
                        <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                            <ShieldAlert className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                            <p className="text-sm font-medium">Admin access required</p>
                            <p className="mt-1 text-sm text-muted-foreground">
                                Only administrators can add knowledge to the assistant.
                            </p>
                        </div>
                    </div>
                </Card>
            </>
        )
    }

    function resetFileInput() {
        if (fileInputRef.current) fileInputRef.current.value = ""
    }

    function chooseFile(candidate) {
        if (!candidate) return false

        const extension = candidate.name
            .slice(candidate.name.lastIndexOf("."))
            .toLowerCase()
        if (!ACCEPTED_EXTENSIONS.includes(extension)) {
            setStatus({
                type: "error",
                message: "Unsupported file type. Use PDF, TXT, MD or HTML.",
            })
            return false
        }
        if (candidate.size > MAX_FILE_BYTES) {
            setStatus({
                type: "error",
                message: "File is too large. The limit is 10 MB.",
            })
            return false
        }

        setFile(candidate)
        setStatus(null)
        setTitle((current) => current || fileTitle(candidate))
        return true
    }

    function clearFile() {
        setFile(null)
        resetFileInput()
    }

    function switchMode(nextMode) {
        if (nextMode === mode) return
        setMode(nextMode)
        setStatus(null)
    }

    async function handleSubmit(event) {
        event.preventDefault()
        if (isSubmitting) return

        const trimmedTitle = title.trim()
        if (!trimmedTitle) {
            setStatus({ type: "error", message: "Add a title before saving." })
            return
        }

        if (mode === "file") {
            if (!file) {
                setStatus({ type: "error", message: "Choose a file to upload." })
                return
            }

            const formData = new FormData()
            formData.append("file", file)
            formData.append("title", trimmedTitle)
            if (category.trim()) formData.append("category", category.trim())

            try {
                setIsSubmitting(true)
                setStatus(null)
                const result = await api("/admin/knowledge-base", {
                    method: "POST",
                    formData,
                })
                const saved = {
                    id: result?.doc_id || `${Date.now()}`,
                    title: result?.title || trimmedTitle,
                    category: result?.category || category.trim(),
                    source: "file",
                    fileName: file.name,
                    addedAt:
                        result?.updated_at ||
                        result?.created_at ||
                        new Date().toISOString(),
                }
                setAdded((current) => [saved, ...current])
                setStatus({
                    type: "success",
                    message: `“${saved.title}” was added to the knowledge base.`,
                })
                setFile(null)
                setTitle("")
                resetFileInput()
            } catch (error) {
                setStatus({ type: "error", message: error.message })
            } finally {
                setIsSubmitting(false)
            }
            return
        }

        if (!content.trim()) {
            setStatus({
                type: "error",
                message: "Paste the information you want the assistant to know.",
            })
            return
        }

        try {
            setIsSubmitting(true)
            setStatus(null)
            const result = await api("/documents", {
                method: "POST",
                body: {
                    title: trimmedTitle,
                    source_type: "manual",
                    category: category.trim() || null,
                    content: content.trim(),
                },
            })
            const saved = {
                id: result?.id || `${Date.now()}`,
                title: result?.title || trimmedTitle,
                category: result?.category || category.trim(),
                source: "text",
                addedAt:
                    result?.created_at ||
                    result?.updated_at ||
                    new Date().toISOString(),
            }
            setAdded((current) => [saved, ...current])
            setStatus({
                type: "success",
                message: `“${saved.title}” was saved as a text source.`,
            })
            setTitle("")
            setContent("")
        } catch (error) {
            setStatus({ type: "error", message: error.message })
        } finally {
            setIsSubmitting(false)
        }
    }

    const success = status?.type === "success"

    return (
        <>
            <PageHeader
                title="Add knowledge"
                description="Upload a file or paste text to seed the assistant. Chunking and embeddings will run once RAG is enabled."
                actions={
                    <Link
                        to="/knowledge-base"
                        className={buttonVariants({ variant: "outline" })}
                    >
                        <ArrowLeft />
                        Back to library
                    </Link>
                }
            />

            <div className="grid items-start gap-4 lg:grid-cols-3">
                <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)] lg:col-span-2">
                    <div className="flex flex-col gap-3 border-b px-(--surface-padding) py-3 sm:flex-row sm:items-center sm:justify-between">
                        <div>
                            <h2 className="text-sm font-semibold">
                                {mode === "file" ? "Upload a file" : "Paste information"}
                            </h2>
                            <p className="mt-0.5 text-xs text-muted-foreground">
                                {mode === "file"
                                    ? "PDF, TXT, MD or HTML — up to 10 MB."
                                    : "Add policies, notices or answers the assistant should use."}
                            </p>
                        </div>
                        <div className="flex items-center gap-1" role="group" aria-label="Knowledge source type">
                            <Button
                                type="button"
                                size="sm"
                                variant={mode === "file" ? "secondary" : "ghost"}
                                aria-pressed={mode === "file"}
                                onClick={() => switchMode("file")}
                            >
                                <Upload />
                                File
                            </Button>
                            <Button
                                type="button"
                                size="sm"
                                variant={mode === "text" ? "secondary" : "ghost"}
                                aria-pressed={mode === "text"}
                                onClick={() => switchMode("text")}
                            >
                                <AlignLeft />
                                Text
                            </Button>
                        </div>
                    </div>

                    <form onSubmit={handleSubmit} aria-busy={isSubmitting} className="space-y-4 p-(--surface-padding)">
                        <div aria-live="polite">
                            {status ? (
                                <Alert
                                    variant={success ? "default" : "destructive"}
                                    role={success ? "status" : "alert"}
                                    className={cn(
                                        "animate-in fade-in-0 slide-in-from-top-2 duration-200",
                                        success &&
                                            "border-success/30 bg-success/10 text-success [&_[data-slot=alert-description]]:text-success/90"
                                    )}
                                >
                                    {success ? (
                                        <CircleCheck aria-hidden="true" />
                                    ) : (
                                        <CircleAlert aria-hidden="true" />
                                    )}
                                    <AlertDescription>{status.message}</AlertDescription>
                                </Alert>
                            ) : null}
                        </div>

                        {mode === "file" ? (
                            <div className="space-y-2">
                                <Label htmlFor="knowledge-file">Document</Label>
                                <input
                                    ref={fileInputRef}
                                    id="knowledge-file"
                                    type="file"
                                    accept={ACCEPTED_TYPES}
                                    aria-describedby="knowledge-file-hint"
                                    className="peer sr-only"
                                    onChange={(event) => {
                                        chooseFile(event.target.files?.[0])
                                        event.target.value = ""
                                    }}
                                />
                                {file ? (
                                    <div className="flex items-center gap-3 rounded-nested border border-border p-3">
                                        <FileText
                                            className="size-4 shrink-0 text-muted-foreground"
                                            aria-hidden="true"
                                        />
                                        <div className="min-w-0 flex-1">
                                            <p className="truncate text-sm font-medium">
                                                {file.name}
                                            </p>
                                            <p className="text-xs text-muted-foreground tabular-nums">
                                                {formatBytes(file.size)}
                                            </p>
                                        </div>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="xs"
                                            onClick={() => fileInputRef.current?.click()}
                                        >
                                            Replace
                                        </Button>
                                        <Button
                                            type="button"
                                            variant="ghost"
                                            size="icon-xs"
                                            aria-label="Remove file"
                                            onClick={clearFile}
                                        >
                                            <X />
                                        </Button>
                                    </div>
                                ) : (
                                    <label
                                        htmlFor="knowledge-file"
                                        onDragOver={(event) => {
                                            event.preventDefault()
                                            setIsDragging(true)
                                        }}
                                        onDragLeave={() => setIsDragging(false)}
                                        onDrop={(event) => {
                                            event.preventDefault()
                                            setIsDragging(false)
                                            chooseFile(event.dataTransfer.files?.[0])
                                        }}
                                        className={cn(
                                            "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-nested border border-dashed px-4 py-8 text-center transition-colors peer-focus-visible:border-ring peer-focus-visible:ring-3 peer-focus-visible:ring-ring/50",
                                            isDragging
                                                ? "border-ring bg-accent/60"
                                                : "border-border hover:bg-muted/50"
                                        )}
                                    >
                                        <Upload
                                            className="size-5 text-muted-foreground"
                                            aria-hidden="true"
                                        />
                                        <span className="text-sm font-medium">
                                            Choose a file or drag it here
                                        </span>
                                    </label>
                                )}
                                <p
                                    id="knowledge-file-hint"
                                    className="text-xs text-muted-foreground"
                                >
                                    PDF, TXT, MD or HTML · 10 MB maximum
                                </p>
                            </div>
                        ) : null}

                        <div className="grid gap-4 sm:grid-cols-3">
                            <div className="space-y-2 sm:col-span-2">
                                <Label htmlFor="knowledge-title">Title</Label>
                                <Input
                                    id="knowledge-title"
                                    value={title}
                                    onChange={(event) => setTitle(event.target.value)}
                                    placeholder="e.g. 2026 fee schedule"
                                    maxLength={255}
                                    aria-required="true"
                                    disabled={isSubmitting}
                                />
                            </div>
                            <div className="space-y-2">
                                <Label htmlFor="knowledge-category">
                                    Category{" "}
                                    <span className="font-normal text-muted-foreground">
                                        optional
                                    </span>
                                </Label>
                                <Input
                                    id="knowledge-category"
                                    list={categoryListId}
                                    value={category}
                                    onChange={(event) => setCategory(event.target.value)}
                                    placeholder="e.g. Fees"
                                    maxLength={50}
                                    disabled={isSubmitting}
                                />
                                <datalist id={categoryListId}>
                                    {CATEGORY_SUGGESTIONS.map((suggestion) => (
                                        <option key={suggestion} value={suggestion} />
                                    ))}
                                </datalist>
                            </div>
                        </div>

                        {mode === "text" ? (
                            <div className="space-y-2">
                                <Label htmlFor="knowledge-content">Information</Label>
                                <Textarea
                                    id="knowledge-content"
                                    value={content}
                                    onChange={(event) => setContent(event.target.value)}
                                    placeholder="Paste the content the assistant should know…"
                                    className="min-h-48 resize-y"
                                    aria-required="true"
                                    disabled={isSubmitting}
                                />
                                <p className="text-xs text-muted-foreground tabular-nums">
                                    {content.length.toLocaleString()} characters
                                </p>
                            </div>
                        ) : null}

                        <div className="flex items-center justify-end gap-2 border-t pt-4">
                            <Button type="submit" disabled={isSubmitting}>
                                {isSubmitting ? (
                                    <>
                                        <Spinner />
                                        {mode === "file" ? "Uploading…" : "Saving…"}
                                    </>
                                ) : (
                                    <>
                                        {mode === "file" ? <Upload /> : <AlignLeft />}
                                        {mode === "file" ? "Upload document" : "Save information"}
                                    </>
                                )}
                            </Button>
                        </div>
                    </form>
                </Card>

                <Card className="gap-0 rounded-surface py-0 [--card-spacing:var(--surface-padding)]">
                    <div className="flex items-center justify-between gap-3 border-b px-(--surface-padding) py-3">
                        <h2 className="text-sm font-semibold">Added this session</h2>
                        <span className="text-xs text-muted-foreground tabular-nums">
                            {added.length} added
                        </span>
                    </div>

                    {added.length === 0 ? (
                        <div className="flex flex-col items-center gap-3 p-8 text-center">
                            <span className="grid size-10 place-items-center rounded-nested bg-muted text-muted-foreground">
                                <Inbox className="size-4" aria-hidden="true" />
                            </span>
                            <div>
                                <p className="text-sm font-medium">Nothing added yet</p>
                                <p className="mt-1 text-sm text-muted-foreground">
                                    Uploads and text sources appear here after they are saved.
                                </p>
                            </div>
                        </div>
                    ) : (
                        <ul className="divide-y">
                            {added.map((item) => (
                                <li
                                    key={item.id}
                                    className="flex items-start gap-3 px-(--surface-padding) py-3 animate-in fade-in-0 duration-200"
                                >
                                    <span className="grid size-8 shrink-0 place-items-center rounded-nested bg-muted text-muted-foreground">
                                        {item.source === "file" ? (
                                            <FileText className="size-4" aria-hidden="true" />
                                        ) : (
                                            <AlignLeft className="size-4" aria-hidden="true" />
                                        )}
                                    </span>
                                    <div className="min-w-0 flex-1">
                                        <p className="truncate text-sm font-medium">
                                            {item.title}
                                        </p>
                                        <p className="mt-0.5 truncate text-xs text-muted-foreground">
                                            {item.source === "file" ? "File" : "Text"}
                                            {item.category ? ` · ${item.category}` : ""}
                                            {" · "}
                                            <span className="tabular-nums">
                                                {formatTime(item.addedAt)}
                                            </span>
                                        </p>
                                    </div>
                                </li>
                            ))}
                        </ul>
                    )}
                </Card>
            </div>
        </>
    )
}
