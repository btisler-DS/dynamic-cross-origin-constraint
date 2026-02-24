import { Routes, Route, NavLink, useLocation } from 'react-router-dom';
import DashboardPage from './pages/DashboardPage';
import HistoryPage from './pages/HistoryPage';
import ComparisonPage from './pages/ComparisonPage';
import ReportPage from './pages/ReportPage';
import SettingsPage from './pages/SettingsPage';
import LoomVisualizerPage from './pages/LoomVisualizerPage';

const NOTEBOOK_ITEMS = [
  { path: '/',         label: 'Dashboard' },
  { path: '/history',  label: 'History'   },
  { path: '/compare',  label: 'Compare'   },
  { path: '/reports',  label: 'Reports'   },
];

const MICROSCOPE_ITEMS = [
  { path: '/visualizer/loom', label: 'Neural Loom' },
];

function NotebookLink({ path, label }: { path: string; label: string }) {
  return (
    <NavLink
      to={path}
      end={path === '/'}
      className={({ isActive }) =>
        `px-3 py-1.5 rounded text-sm transition-colors ${
          isActive
            ? 'bg-amber-900/60 text-amber-200 border border-amber-700/50'
            : 'text-gray-400 hover:text-amber-200 hover:bg-amber-900/30'
        }`
      }
    >
      {label}
    </NavLink>
  );
}

function MicroscopeLink({ path, label }: { path: string; label: string }) {
  return (
    <NavLink
      to={path}
      className={({ isActive }) =>
        `px-3 py-1.5 rounded text-sm transition-colors ${
          isActive
            ? 'bg-blue-600 text-white'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`
      }
    >
      {label}
    </NavLink>
  );
}

function ModeBadge() {
  const { pathname } = useLocation();
  const isMicroscope = pathname.startsWith('/visualizer');

  if (isMicroscope) {
    return (
      <span className="text-xs font-mono tracking-widest text-cyan-500/70 border border-cyan-800/40 rounded px-2 py-0.5">
        🔬 MICROSCOPE
      </span>
    );
  }
  if (pathname !== '/settings') {
    return (
      <span className="text-xs font-mono tracking-widest text-amber-500/70 border border-amber-800/40 rounded px-2 py-0.5">
        📓 LAB NOTEBOOK
      </span>
    );
  }
  return null;
}

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-gray-900 border-b border-gray-800 px-6 py-3">
        <div className="flex items-center gap-6">
          <h1 className="text-xl font-bold text-blue-400 shrink-0">Project Synapse</h1>

          <nav className="flex items-center gap-1 flex-1">
            {/* ── Lab Notebook section ──────────────────────────── */}
            <span className="text-[10px] font-mono tracking-widest text-amber-600/50 uppercase mr-1 select-none">
              📓 Notebook
            </span>
            {NOTEBOOK_ITEMS.map(({ path, label }) => (
              <NotebookLink key={path} path={path} label={label} />
            ))}

            {/* ── Divider ──────────────────────────────────────── */}
            <div className="w-px h-5 bg-gray-700 mx-2" />

            {/* ── Microscope section ────────────────────────────── */}
            <span className="text-[10px] font-mono tracking-widest text-cyan-600/50 uppercase mr-1 select-none">
              🔬 Microscope
            </span>
            {MICROSCOPE_ITEMS.map(({ path, label }) => (
              <MicroscopeLink key={path} path={path} label={label} />
            ))}

            {/* ── Settings ─────────────────────────────────────── */}
            <div className="w-px h-5 bg-gray-700 mx-2" />
            <NavLink
              to="/settings"
              className={({ isActive }) =>
                `px-3 py-1.5 rounded text-sm transition-colors ${
                  isActive
                    ? 'bg-gray-700 text-white'
                    : 'text-gray-500 hover:text-white hover:bg-gray-800'
                }`
              }
            >
              Settings
            </NavLink>
          </nav>

          <ModeBadge />
        </div>
      </header>

      <main className="flex-1 p-6">
        <Routes>
          <Route path="/"                  element={<DashboardPage />} />
          <Route path="/history"           element={<HistoryPage />} />
          <Route path="/compare"           element={<ComparisonPage />} />
          <Route path="/reports"           element={<ReportPage />} />
          <Route path="/visualizer/loom"   element={<LoomVisualizerPage />} />
          <Route path="/settings"          element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
