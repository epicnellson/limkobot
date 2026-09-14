import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import KnowledgeBase from "./pages/KnowledgeBase";
import FlaggedConversations from "./pages/FlaggedConversations";
import StudentLookup from "./pages/StudentLookup";

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-blue-700 text-white p-4 flex gap-6">
        <Link to="/">Dashboard</Link>
        <Link to="/knowledge-base">Knowledge Base</Link>
        <Link to="/flagged">Flagged Conversations</Link>
        <Link to="/students">Student Lookup</Link>
        <Link to="/login" className="ml-auto">Login</Link>
      </nav>
      {children}
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/"
          element={
            <Layout>
              <Dashboard />
            </Layout>
          }
        />
        <Route
          path="/knowledge-base"
          element={
            <Layout>
              <KnowledgeBase />
            </Layout>
          }
        />
        <Route
          path="/flagged"
          element={
            <Layout>
              <FlaggedConversations />
            </Layout>
          }
        />
        <Route
          path="/students"
          element={
            <Layout>
              <StudentLookup />
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}