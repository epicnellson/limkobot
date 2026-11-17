import { useEffect, useState } from "react"
import { NavLink, useNavigate } from "react-router-dom"
import {
    BookOpenText,
    Flag,
    GraduationCap,
    LayoutDashboard,
    LogOut,
    Menu,
    UsersRound,
    X,
} from "lucide-react"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import { clearSession, getUser } from "@/lib/api"
import { cn } from "@/lib/utils"

const navigation = [
    { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
    { to: "/knowledge-base", label: "Knowledge Base", icon: BookOpenText },
    { to: "/flagged", label: "Flagged Conversations", icon: Flag },
    { to: "/students", label: "Student Lookup", icon: UsersRound },
]

function initialsFor(name) {
    return (
        name
            ?.trim()
            .split(/\s+/)
            .slice(0, 2)
            .map((part) => part[0])
            .join("")
            .toUpperCase() || "ST"
    )
}

export default function AppShell({ children }) {
    const [menuOpen, setMenuOpen] = useState(false)
    const navigate = useNavigate()
    const user = getUser()
    const displayName = user?.full_name || user?.email || "Staff member"

    useEffect(() => {
        function onKeyDown(event) {
            if (event.key === "Escape") setMenuOpen(false)
        }
        window.addEventListener("keydown", onKeyDown)
        return () => window.removeEventListener("keydown", onKeyDown)
    }, [])

    function logout() {
        clearSession()
        navigate("/login", { replace: true })
    }

    return (
        <div className="min-h-screen">
            {menuOpen && (
                <button
                    type="button"
                    aria-label="Close navigation"
                    onClick={() => setMenuOpen(false)}
                    className="fixed inset-0 z-30 bg-foreground/30 backdrop-blur-[2px] lg:hidden"
                />
            )}

            <aside
                className={cn(
                    "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-sidebar-border bg-sidebar transition-transform duration-200 ease-out lg:translate-x-0",
                    menuOpen ? "translate-x-0" : "-translate-x-full"
                )}
            >
                <div className="flex h-16 shrink-0 items-center gap-3 border-b border-sidebar-border px-4">
                    <span className="grid size-9 shrink-0 place-items-center rounded-nested bg-primary text-primary-foreground">
                        <GraduationCap className="size-[18px]" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                        <p className="truncate text-sm font-semibold tracking-tight">
                            Limkobot
                        </p>
                        <p className="truncate text-xs text-muted-foreground">
                            Staff console
                        </p>
                    </div>
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        className="ml-auto lg:hidden"
                        aria-label="Close navigation"
                        onClick={() => setMenuOpen(false)}
                    >
                        <X />
                    </Button>
                </div>

                <nav aria-label="Main navigation" className="flex-1 space-y-1 overflow-y-auto p-3">
                    {navigation.map(({ to, label, icon: Icon, end }) => (
                        <NavLink
                            key={to}
                            to={to}
                            end={end}
                            onClick={() => setMenuOpen(false)}
                            className={({ isActive }) =>
                                cn(
                                    "flex items-center gap-3 rounded-nested px-3 py-2 text-sm font-medium text-sidebar-foreground/70 transition-colors hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-2 focus-visible:outline-offset-2",
                                    isActive &&
                                        "bg-sidebar-accent text-sidebar-accent-foreground"
                                )
                            }
                        >
                            <Icon className="size-[18px] shrink-0" aria-hidden="true" />
                            <span className="truncate">{label}</span>
                        </NavLink>
                    ))}
                </nav>

                <div className="shrink-0 border-t border-sidebar-border p-3">
                    <div className="flex items-center gap-3 rounded-nested px-2 py-2">
                        <Avatar size="sm">
                            <AvatarFallback className="bg-sidebar-accent text-sidebar-accent-foreground">
                                {initialsFor(displayName)}
                            </AvatarFallback>
                        </Avatar>
                        <div className="min-w-0 flex-1">
                            <p className="truncate text-xs font-medium">{displayName}</p>
                            <p className="truncate text-xs text-muted-foreground">
                                {user?.email || "Signed in"}
                            </p>
                        </div>
                        <Button
                            type="button"
                            variant="ghost"
                            size="icon-sm"
                            onClick={logout}
                            aria-label="Sign out"
                            title="Sign out"
                        >
                            <LogOut />
                        </Button>
                    </div>
                </div>
            </aside>

            <div className="lg:pl-64">
                <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-border bg-background/95 px-4 backdrop-blur-sm sm:px-6 lg:hidden">
                    <Button
                        type="button"
                        variant="ghost"
                        size="icon-sm"
                        aria-label="Open navigation"
                        aria-expanded={menuOpen}
                        onClick={() => setMenuOpen(true)}
                    >
                        <Menu />
                    </Button>
                    <GraduationCap
                        className="size-4 text-primary"
                        aria-hidden="true"
                    />
                    <span className="text-sm font-semibold tracking-tight">Limkobot</span>
                </header>

                <main className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:py-8">
                    {children}
                </main>
            </div>
        </div>
    )
}
