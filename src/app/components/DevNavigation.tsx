import { useNavigate, useLocation } from 'react-router';
import { LayoutDashboard, Activity, User, BarChart3, Smartphone, Settings, Link2, MessageSquare, FileText, Menu } from 'lucide-react';
import { useState } from 'react';
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

export default function DevNavigation() {
  const navigate = useNavigate();
  const location = useLocation();
  const [isExpanded, setIsExpanded] = useState(false);

  const activeRoute = NAV_ITEMS.find((r) => isNavRouteActive(r.id, location.pathname));

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
        isExpanded ? 'w-auto' : 'w-[56px]'
      }`}
      onMouseEnter={() => setIsExpanded(true)}
      onMouseLeave={() => setIsExpanded(false)}
    >
      {isExpanded ? (
        <div className="bg-white border border-gray-200 rounded-lg px-4 py-2.5 flex items-center gap-1.5 shadow-lg max-w-[95vw] overflow-x-auto animate-in fade-in zoom-in duration-200">
          {NAV_ITEMS.map((route) => {
            const Icon = route.icon;
            const isActive = isNavRouteActive(route.id, location.pathname);
            return (
              <button
                key={route.id}
                onClick={() => navigate(resolveNavPath(route.id))}
                className={`flex items-center gap-2 px-3 py-2 rounded transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-[#E31E24] text-white border border-[#E31E24] font-semibold'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
                title={route.label}
              >
                <Icon className="w-4 h-4" />
                <span className="text-xs font-medium">{route.label}</span>
              </button>
            );
          })}
        </div>
      ) : (
        <div className="flex justify-center">
          <button
            className="w-14 h-14 bg-white border-2 border-[#E31E24] rounded-full flex items-center justify-center shadow-lg hover:shadow-xl transition-all hover:scale-110 duration-200"
            title={activeRoute?.label || 'Navigation'}
          >
            {activeRoute ? (
              <div className="flex flex-col items-center justify-center gap-0.5">
                {(() => {
                  const Icon = activeRoute.icon;
                  return <Icon className="w-5 h-5 text-[#E31E24]" />;
                })()}
                <div className="text-[8px] text-[#E31E24] font-bold text-center leading-none">
                  {activeRoute.label.split(' ')[0]}
                </div>
              </div>
            ) : (
              <Menu className="w-6 h-6 text-[#E31E24]" />
            )}
          </button>
        </div>
      )}

      <style>{`
        @keyframes fadeInZoom {
          from {
            opacity: 0;
            transform: scale(0.85);
          }
          to {
            opacity: 1;
            transform: scale(1);
          }
        }
        .animate-in.fade-in.zoom-in {
          animation: fadeInZoom 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
