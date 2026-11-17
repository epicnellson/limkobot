import { CircleAlert, RotateCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export default function ErrorState({
    title = "Couldn't load this data",
    message,
    onRetry,
    className,
}) {
    return (
        <div
            role="alert"
            className={cn(
                "flex flex-col items-center gap-3 p-10 text-center",
                className
            )}
        >
            <span className="grid size-10 place-items-center rounded-nested bg-destructive/10 text-destructive">
                <CircleAlert className="size-4" aria-hidden="true" />
            </span>
            <div>
                <p className="text-sm font-medium">{title}</p>
                {message ? (
                    <p className="mt-1 max-w-md text-sm text-pretty text-muted-foreground">
                        {message}
                    </p>
                ) : null}
            </div>
            {onRetry ? (
                <Button variant="outline" size="sm" onClick={onRetry}>
                    <RotateCw />
                    Try again
                </Button>
            ) : null}
        </div>
    )
}
