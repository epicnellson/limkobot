export default function PageHeader({ title, description, actions }) {
    return (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="min-w-0 max-w-2xl">
                <h1 className="text-2xl font-semibold tracking-tight text-balance sm:text-[1.75rem]">
                    {title}
                </h1>
                {description ? (
                    <p className="mt-1 text-sm text-pretty text-muted-foreground">
                        {description}
                    </p>
                ) : null}
            </div>
            {actions ? (
                <div className="flex shrink-0 flex-wrap items-center gap-2">
                    {actions}
                </div>
            ) : null}
        </div>
    )
}
