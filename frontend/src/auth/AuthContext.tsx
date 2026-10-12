import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { getApi } from '../api';
import { getAuthToken, setAuthToken } from '../api/client';
import type { AuthUser } from '../types';

interface AuthContextValue {
  user: AuthUser | null;
  /** 啟動時是否已完成 token 恢復（避免閃爍） */
  ready: boolean;
  register: (username: string, password: string) => Promise<void>;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  ready: false,
  register: () => Promise.reject(new Error('not ready')),
  login: () => Promise.reject(new Error('not ready')),
  logout: () => {},
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  // 啟動時用 localStorage 的 token 恢復登入態
  useEffect(() => {
    let alive = true;
    (async () => {
      if (getAuthToken()) {
        try {
          const api = await getApi();
          const u = await api.me();
          if (alive) setUser(u);
        } catch {
          if (alive) setUser(null);
        }
      }
      if (alive) setReady(true);
    })();
    const onExpired = () => setUser(null);
    window.addEventListener('auth-expired', onExpired);
    return () => {
      alive = false;
      window.removeEventListener('auth-expired', onExpired);
    };
  }, []);

  const applySession = useCallback((token: string, u: AuthUser) => {
    setAuthToken(token);
    setUser(u);
  }, []);

  const register = useCallback(
    async (username: string, password: string) => {
      const api = await getApi();
      const s = await api.register(username.trim(), password);
      applySession(s.token, s.user);
    },
    [applySession],
  );

  const login = useCallback(
    async (username: string, password: string) => {
      const api = await getApi();
      const s = await api.login(username.trim(), password);
      applySession(s.token, s.user);
    },
    [applySession],
  );

  const logout = useCallback(() => {
    setAuthToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, ready, register, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}

/** 未登入時想打錯題本等受保護功能：觸發頂欄的登入彈窗。 */
export function promptLogin(): void {
  try {
    window.dispatchEvent(new CustomEvent('open-auth-modal'));
  } catch {
    /* 忽略 */
  }
}
