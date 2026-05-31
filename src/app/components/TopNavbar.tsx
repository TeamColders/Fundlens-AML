import { useNavigate, useLocation } from 'react-router';
import { LayoutDashboard, Activity, FileText, User, BarChart3, MessageSquare, Link2, Settings, Smartphone } from 'lucide-react';
import { isNavRouteActive, resolveNavPath } from '../../lib/appNav';

const NAV_ITEMS = [
  { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { id: 'graph', label: 'Graph View', icon: Activity },
  { id: 'str', label: 'STR Generation', icon: FileText },
  { id: 'entity', label: 'Entity Profile', icon: User },
  { id: 'analytics', label: 'Analytics', icon: BarChart3 },
  { id: 'query', label: 'AI Query', icon: MessageSquare },
  { id: 'blockchain', label: 'Audit Trail', icon: Link2 },
  { id: 'admin', label: 'Configuration', icon: Settings },
  { id: 'mobile', label: 'Mobile', icon: Smartphone },
] as const;

export default function TopNavbar() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="bg-white border-b border-gray-200 px-8 py-4 sticky top-0 z-40 shadow-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-8">
          <h2 className="text-xl font-bold text-gray-900" style={{ fontFamily: 'Syne' }}>
            FundLens
          </h2>
          <div className="flex items-center gap-1">
            {NAV_ITEMS.map((route) => {
              const Icon = route.icon;
              const isActive = isNavRouteActive(route.id, location.pathname);
              return (
                <button
                  key={route.id}
                  onClick={() => navigate(resolveNavPath(route.id))}
                  className={`flex items-center gap-2 px-3 py-2 rounded transition-all text-sm ${
                    isActive
                      ? 'bg-[#E31E24] text-white font-semibold'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                  }`}
                  title={route.label}
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{route.label}</span>
                </button>
              );
            })}
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-600">
          <div className="w-2 h-2 rounded-full bg-green-500" />
          <span>System Active</span>
        </div>
      </div>
    </div>
  );
}
