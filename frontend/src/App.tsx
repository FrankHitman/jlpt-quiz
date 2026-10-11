import { HashRouter, Link, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { isMockMode } from './api';
import Home from './pages/Home';
import MockExam from './pages/MockExam';
import Practice from './pages/Practice';
import Result from './pages/Result';

function Header() {
  const { user } = useAuth();
  return (
    <header className="app-header">
      <Link to="/" className="brand">
        JLPT N1 刷題系統
      </Link>
      <nav className="app-nav">
        <Link to="/">首頁</Link>
        <Link to="/practice">專項練習</Link>
      </nav>
      <div className="header-right">
        {isMockMode && <span className="badge badge-mock">演示資料模式</span>}
        <span className="user-status">{user ? user.username : '未登入'}</span>
      </div>
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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="app-footer">題庫僅供個人學習使用・聽解暫無音頻</footer>
      </AuthProvider>
    </HashRouter>
  );
}
