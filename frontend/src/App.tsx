import { useEffect } from "react";
import { Outlet, Route, Routes, useLocation } from "react-router-dom";
import { AppShell } from "./components/layout/AppShell";
import { RequireAuth, RequireOnboarding } from "./routes/guards";
import About from "./pages/About";
import AssessmentAttempt from "./pages/AssessmentAttempt";
import AssessmentResult from "./pages/AssessmentResult";
import Assessments from "./pages/Assessments";
import Career from "./pages/Career";
import Dashboard from "./pages/Dashboard";
import ForgotPassword from "./pages/ForgotPassword";
import Insights from "./pages/Insights";
import Features from "./pages/Features";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";
import Onboarding from "./pages/Onboarding";
import Register from "./pages/Register";
import ResetPassword from "./pages/ResetPassword";
import Roadmap from "./pages/Roadmap";
import Settings from "./pages/Settings";
import Tutor from "./pages/Tutor";
import VerifyEmail from "./pages/VerifyEmail";

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [pathname]);
  return null;
}

function ProtectedLayout() {
  return (
    <RequireAuth>
      <AppShell>
        <Outlet />
      </AppShell>
    </RequireAuth>
  );
}

export default function App() {
  return (
    <>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/features" element={<Features />} />
        <Route path="/about" element={<About />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/verify-email" element={<VerifyEmail />} />

        <Route
          path="/onboarding"
          element={
            <RequireAuth>
              <Onboarding />
            </RequireAuth>
          }
        />

        <Route element={<ProtectedLayout />}>
          <Route
            path="/dashboard"
            element={
              <RequireOnboarding>
                <Dashboard />
              </RequireOnboarding>
            }
          />
          <Route
            path="/assessments"
            element={
              <RequireOnboarding>
                <Assessments />
              </RequireOnboarding>
            }
          />
          <Route
            path="/assessments/attempt/:attemptId"
            element={
              <RequireOnboarding>
                <AssessmentAttempt />
              </RequireOnboarding>
            }
          />
          <Route
            path="/assessments/result/:attemptId"
            element={
              <RequireOnboarding>
                <AssessmentResult />
              </RequireOnboarding>
            }
          />
          <Route
            path="/roadmap"
            element={
              <RequireOnboarding>
                <Roadmap />
              </RequireOnboarding>
            }
          />
          <Route
            path="/insights"
            element={
              <RequireOnboarding>
                <Insights />
              </RequireOnboarding>
            }
          />
          <Route
            path="/tutor"
            element={
              <RequireOnboarding>
                <Tutor />
              </RequireOnboarding>
            }
          />
          <Route
            path="/career"
            element={
              <RequireOnboarding>
                <Career />
              </RequireOnboarding>
            }
          />
          <Route path="/settings" element={<Settings />} />
        </Route>

        <Route path="*" element={<NotFound />} />
      </Routes>
    </>
  );
}
