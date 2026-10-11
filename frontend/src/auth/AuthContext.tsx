import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';

/**
 * 用戶系統預留（T4）：目前未啟用登入，全站經由 useAuth() 取用戶，
 * 後期接上真實登入時呼叫方零改動。
 */
export interface AuthUser {
  id: number;
  username: string;
}

interface AuthContextValue {
  user: AuthUser | null;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

function notEnabled(): Promise<void> {
  return Promise.reject(new Error('Auth not enabled yet'));
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  login: notEnabled,
  logout: () => Promise.resolve(),
});

export function AuthProvider({ children }: { children: ReactNode }) {
  const value: AuthContextValue = { user: null, login: notEnabled, logout: () => Promise.resolve() };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  return useContext(AuthContext);
}
