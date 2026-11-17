import { useId } from "react"
import { Search } from "lucide-react"
import { Input } from "@/components/ui/input"

export default function SearchField({ value, onChange, placeholder, label, className }) {
    const searchId = useId()

    return (
        <div className={className}>
            <label className="sr-only" htmlFor={searchId}>
                {label}
            </label>
            <div className="relative">
                <Search
                    className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
                    aria-hidden="true"
                />
                <Input
                    id={searchId}
                    type="search"
                    value={value}
                    onChange={(event) => onChange(event.target.value)}
                    placeholder={placeholder}
                    className="h-9 pl-8"
                />
            </div>
        </div>
    )
}
