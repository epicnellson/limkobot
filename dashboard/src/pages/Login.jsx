import { useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { CircleAlert, Eye, EyeOff, GraduationCap, Lock, Mail } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Spinner } from "@/components/ui/spinner"
import { api, getToken, setSession } from "@/lib/api"

export default function Login() {
    const navigate = useNavigate()
    const [email, setEmail] = useState("")
    const [password, setPassword] = useState("")
    const [showPassword, setShowPassword] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState("")

    if (getToken()) return <Navigate to="/" replace />

    async function handleSubmit(event) {
        event.preventDefault()
        setError("")
        setLoading(true)

        try {
            const data = await api("/auth/staff/login", {
                method: "POST",
                body: { email, password },
                auth: false,
            })
            setSession(data.token, data.user)
            navigate("/", { replace: true })
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="flex min-h-screen items-center justify-center px-4 py-10 sm:px-6">
            <div className="w-full max-w-md">
                <div className="mb-8 flex items-center gap-3">
                    <span className="grid size-10 shrink-0 place-items-center rounded-nested bg-primary text-primary-foreground">
                        <GraduationCap className="size-5" aria-hidden="true" />
                    </span>
                    <div>
                        <p className="font-semibold tracking-tight">Limkobot</p>
                        <p className="text-xs text-muted-foreground">Staff console</p>
                    </div>
                </div>

                <form
                    onSubmit={handleSubmit}
                    aria-busy={loading}
                    className="rounded-surface bg-card p-(--surface-padding) ring-1 ring-foreground/10"
                >
                    <div className="mb-8">
                        <h1 className="text-3xl font-semibold tracking-tight text-balance">
                            Sign in to your workspace
                        </h1>
                        <p className="mt-2 text-sm text-pretty text-muted-foreground">
                            Use your staff credentials to continue.
                        </p>
                    </div>

                    <div aria-live="polite" className="space-y-5">
                        {error ? (
                            <Alert
                                variant="destructive"
                                className="animate-in fade-in-0 slide-in-from-top-2 duration-200"
                            >
                                <CircleAlert aria-hidden="true" />
                                <AlertDescription>{error}</AlertDescription>
                            </Alert>
                        ) : null}

                        <div className="space-y-2">
                            <Label htmlFor="email">Email address</Label>
                            <div className="relative">
                                <Mail
                                    className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
                                    aria-hidden="true"
                                />
                                <Input
                                    id="email"
                                    type="email"
                                    autoComplete="email"
                                    placeholder="you@university.edu"
                                    value={email}
                                    onChange={(event) => setEmail(event.target.value)}
                                    disabled={loading}
                                    className="h-10 pl-10"
                                    required
                                />
                            </div>
                        </div>

                        <div className="space-y-2">
                            <Label htmlFor="password">Password</Label>
                            <div className="relative">
                                <Lock
                                    className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground"
                                    aria-hidden="true"
                                />
                                <Input
                                    id="password"
                                    type={showPassword ? "text" : "password"}
                                    autoComplete="current-password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    disabled={loading}
                                    className="h-10 pr-11 pl-10"
                                    required
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowPassword((shown) => !shown)}
                                    aria-label={showPassword ? "Hide password" : "Show password"}
                                    aria-pressed={showPassword}
                                    className="absolute top-1/2 right-1 grid size-8 -translate-y-1/2 place-items-center rounded-nested text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-2 focus-visible:outline-offset-2"
                                >
                                    {showPassword ? (
                                        <EyeOff className="size-4" aria-hidden="true" />
                                    ) : (
                                        <Eye className="size-4" aria-hidden="true" />
                                    )}
                                </button>
                            </div>
                        </div>

                        <Button type="submit" disabled={loading} className="h-10 w-full">
                            {loading ? (
                                <>
                                    <Spinner />
                                    Signing in…
                                </>
                            ) : (
                                "Sign in"
                            )}
                        </Button>
                    </div>
                </form>
            </div>
        </main>
    )
}
