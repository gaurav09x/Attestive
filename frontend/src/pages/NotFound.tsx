import { Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import { Logo } from "../components/Logo";
import { Button, Panel } from "../components/ui";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center px-5">
      <Logo />
      <Panel className="mt-8 max-w-md p-8 text-center">
        <p className="font-mono text-xs text-fog-500">404</p>
        <h1 className="mt-2 text-xl font-semibold">This page doesn't exist</h1>
        <p className="mt-2 text-sm text-fog-400">
          The link may be outdated, or the page may arrive in a later phase.
        </p>
        <div className="mt-6 flex justify-center gap-2">
          <Link to="/">
            <Button variant="secondary">
              <ArrowLeft className="size-4" aria-hidden />
              Home
            </Button>
          </Link>
          <Link to="/dashboard">
            <Button>Open dashboard</Button>
          </Link>
        </div>
      </Panel>
    </div>
  );
}
