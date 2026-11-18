import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"
import AppShell from "@/components/layout/AppShell"
import AddKnowledge from "@/pages/AddKnowledge"
import FlaggedConversations from "@/pages/FlaggedConversations"
import KnowledgeBase from "@/pages/KnowledgeBase"
import Login from "@/pages/Login"
import StudentLookup from "@/pages/StudentLookup"
import Dashboard from "@/pages/Dashboard"
import { getToken } from "@/lib/api"

function Protected({ children }) {
    if (!getToken()) return <Navigate to="/login" replace />
    return <AppShell>{children}</AppShell>
}

export default function App() {
    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<Login />} />
                <Route
                    path="/"
                    element={
                        <Protected>
                            <Dashboard />
                        </Protected>
                    }
                />
                <Route
                    path="/knowledge-base"
                    element={
                        <Protected>
                            <KnowledgeBase />
                        </Protected>
                    }
                />
                <Route
                    path="/knowledge-base/upload"
                    element={
                        <Protected>
                            <AddKnowledge />
                        </Protected>
                    }
                />
                <Route
                    path="/flagged"
                    element={
                        <Protected>
                            <FlaggedConversations />
                        </Protected>
                    }
                />
                <Route
                    path="/students"
                    element={
                        <Protected>
                            <StudentLookup />
                        </Protected>
                    }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </BrowserRouter>
    )
}
