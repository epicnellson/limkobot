import {
  BrowserRouter,
  Routes,
  Route,
  Link,
  Navigate,
  useNavigate,
} from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import KnowledgeBase from "./pages/KnowledgeBase";
import FlaggedConversations from "./pages/FlaggedConversations";
import StudentLookup from "./pages/StudentLookup";
import { getToken, getUser, clearSession } from "./lib/api";

function Layout({ children }) {
  const navigate = useNavigate();
  const user = getUser();

  function logout() {
    clearSession();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-blue-700 text-white p-4 flex gap-6 items-center">
        <Link to="/">Dashboard</Link>
        <Link to="/knowledge-base">Knowledge Base</Link>
        <Link to="/flagged">Flagged Conversations</Link>
        <Link to="/students">Student Lookup</Link>
        <span className="ml-auto text-sm opacity-80">
          {user?.full_name || user?.email}
        </span>
        <button onClick={logout} className="underline text-sm">
          Log out
        </button>
      </nav>
      {children}
    </div>
  );
}

function Protected({ children }) {
  if (!getToken()) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<Protected><Dashboard /></Protected>} />
        <Route
          path="/knowledge-base"
          element={<Protected><KnowledgeBase /></Protected>}
        />
        <Route
          path="/flagged"
          element={<Protected><FlaggedConversations /></Protected>}
        />
        <Route
          path="/students"
          element={<Protected><StudentLookup /></Protected>}
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}