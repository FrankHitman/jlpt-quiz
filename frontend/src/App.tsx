import { useEffect, useState } from 'react';
import { HashRouter, Link, Navigate, Route, Routes, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { isMockMode } from './api';
import Home from './pages/Home';
import MockExam from './pages/MockExam';
import Practice from './pages/Practice';
import Result from './pages/Result';
import WrongBook from './pages/WrongBook';

function AuthModal({ onClose }: { onClose: () => void }) {
  const { login, register } = useAuth();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setError(null);
    if (username.trim().length < 3 || username.trim().length > 32) {
      setError('用戶名需為 3–32 個字元');
      return;
    }
    if (password.length < 6) {
      setError('密碼至少 6 個字元');
      return;
    }
    setBusy(true);
    try {
      if (mode === 'login') await login(username, password);
      else await register(username, password);
      onClose();
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-tabs">
          <button
            type="button"
            className={mode === 'login' ? 'tab active' : 'tab'}
            onClick={() => { setMode('login'); setError(null); }}
          >
            登入
          </button>
          <button
            type="button"
            className={mode === 'register' ? 'tab active' : 'tab'}
            onClick={() => { setMode('register'); setError(null); }}
          >
            註冊
          </button>
        </div>
        <label>
          用戶名
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="3–32 個字元"
            autoComplete="username"
          />
        </label>
        <label>
          密碼
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="至少 6 個字元"
            autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            onKeyDown={(e) => { if (e.key === 'Enter') submit(); }}
          />
        </label>
        {error && <p className="error">{error}</p>}
        <div className="modal-actions">
          <button type="button" className="primary-btn" onClick={submit} disabled={busy}>
            {busy ? '處理中…' : mode === 'login' ? '登入' : '註冊'}
          </button>
          <button type="button" className="ghost-btn" onClick={onClose}>
            取消
          </button>
        </div>
        <p className="hint">登入後答錯的題目會自動收錄進錯題本；不登入也可正常刷題。</p>
      </div>
    </div>
  );
}

function Header() {
  const { user, ready, logout } = useAuth();
  const [authOpen, setAuthOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const open = () => setAuthOpen(true);
    window.addEventListener('open-auth-modal', open);
    return () => window.removeEventListener('open-auth-modal', open);
  }, []);

  const goWrongBook = () => {
    if (user) navigate('/wrong-book');
    else {
      setAuthOpen(true);
    }
  };

  return (
    <header className="app-header">
      <Link to="/" className="brand">
        JLPT N1 刷題系統
      </Link>
      <nav className="app-nav">
        <Link to="/">首頁</Link>
        <Link to="/practice">專項練習</Link>
        <button type="button" className="nav-link-btn" onClick={goWrongBook}>
          錯題本
        </button>
      </nav>
      <div className="header-right">
        {isMockMode && <span className="badge badge-mock">演示資料模式</span>}
        {!ready ? (
          <span className="user-status">載入中…</span>
        ) : user ? (
          <>
            <span className="user-status">{user.username}</span>
            <button type="button" className="link-btn" onClick={logout}>
              退出
            </button>
          </>
        ) : (
          <button type="button" className="primary-btn small" onClick={() => setAuthOpen(true)}>
            登入／註冊
          </button>
        )}
      </div>
      {authOpen && <AuthModal onClose={() => setAuthOpen(false)} />}
    </header>
  );
}

export default function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <Header />
        <main className="app-main">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/mock/:examId" element={<MockExam />} />
            <Route path="/practice" element={<Practice />} />
            <Route path="/result/:attemptId" element={<Result />} />
            <Route path="/wrong-book" element={<WrongBook />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="app-footer">題庫僅供個人學習使用・聽解暫無音頻</footer>
      </AuthProvider>
    </HashRouter>
  );
}
