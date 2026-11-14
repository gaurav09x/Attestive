import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { apiFetch, authApi, setAccessToken } from "./api";
import type { AuthResponse, MeResponse, User } from "./types";

type Status = "loading" | "authenticated" | "anonymous";

interface AuthContextValue {
  user: User | null;
  status: Status;
  login: (email: string, password: string) => Promise<void>;
  register: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  reloadUser: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, updateUser] = useState<User | null>(null);
  const [status, setStatus] = useState<Status>("loading");

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      const refreshed = await authApi.refresh();
      if (!refreshed) {
        if (!cancelled) setStatus("anonymous");
        return;
      }
      try {
        const me = await apiFetch<MeResponse>("/auth/me");
        if (!cancelled) {
          updateUser(me.user);
          setStatus("authenticated");
        }
      } catch {
        if (!cancelled) setStatus("anonymous");
      }
    }

    void bootstrap();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    function handleUnauthorized() {
      setAccessToken(null);
      updateUser(null);
      setStatus("anonymous");
    }
    window.addEventListener("sf:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("sf:unauthorized", handleUnauthorized);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await apiFetch<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setAccessToken(response.access_token);
    updateUser(response.user);
    setStatus("authenticated");
  }, []);

  const register = useCallback(async (fullName: string, email: string, password: string) => {
    const response = await apiFetch<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    setAccessToken(response.access_token);
    updateUser(response.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logoutRequest();
    } finally {
      updateUser(null);
      setStatus("anonymous");
    }
  }, []);

  const reloadUser = useCallback(async () => {
    const me = await apiFetch<MeResponse>("/auth/me");
    updateUser(me.user);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      login,
      register,
      logout,
      reloadUser,
      setUser: updateUser,
    }),
    [user, status, login, register, logout, reloadUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside <AuthProvider>");
  }
  return context;
}
