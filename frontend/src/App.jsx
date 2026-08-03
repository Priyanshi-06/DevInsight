import { Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import RequireAuth from './components/RequireAuth';
import RootRoute from './components/RootRoute';
import TopBar from './components/TopBar';
import RepoLayout from './layouts/RepoLayout';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ForgotPassword from './pages/ForgotPassword';
import RepoDashboard from './pages/RepoDashboard';
import Chat from './pages/Chat';
import Architecture from './pages/Architecture';
import Recommendations from './pages/Recommendations';
import PrAssistant from './pages/PrAssistant';
import TestGenerator from './pages/TestGenerator';

export default function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col">
        <TopBar />
        <div className="flex-1 flex flex-col">
          <Routes>
            <Route path="/" element={<RootRoute />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route element={<RequireAuth />}>
              <Route path="/repos/:id" element={<RepoLayout />}>
                <Route index element={<RepoDashboard />} />
                <Route path="chat" element={<Chat />} />
                <Route path="architecture" element={<Architecture />} />
                <Route path="recommendations" element={<Recommendations />} />
                <Route path="pr-assistant" element={<PrAssistant />} />
                <Route path="tests" element={<TestGenerator />} />
              </Route>
            </Route>
          </Routes>
        </div>
      </div>
    </AuthProvider>
  );
}
