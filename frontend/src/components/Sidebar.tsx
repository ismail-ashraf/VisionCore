
import {
  LayoutDashboard,
  ChartNoAxesCombined,
  FileText,
  Settings,
  Activity,
  ChevronLeft,
} from "lucide-react";

import { NavLink } from "react-router-dom";

const navItems = [
  { label: "Dashboard", path: "/", icon: LayoutDashboard },
  { label: "Analytics", path: "/analytics", icon: ChartNoAxesCombined },
  { label: "System Logs", path: "/logs", icon: FileText },
  { label: "Settings", path: "/settings", icon: Settings },
];

export default function Sidebar() {
  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-slate-800 bg-[#111a2b] px-5 py-6">
      <div className="mb-12 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600">
          <Activity size={23} />
        </div>

        <div>
          <h1 className="text-lg font-bold tracking-wide text-white">
            VisionCore
          </h1>
          <p className="text-xs text-slate-500">AI Vision Platform</p>
        </div>
      </div>

      <p className="mb-4 px-3 text-xs font-semibold uppercase tracking-widest text-slate-500">
        Workspace
      </p>

      <nav className="flex flex-col gap-2">
        {navItems.map(({ label, path, icon: Icon }) => (
          <NavLink
            key={path}
            to={path}
            end={path === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-3 text-sm transition ${
                isActive
                  ? "bg-blue-600/15 font-semibold text-blue-400"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={19} />
                {label}

                {isActive && (
                  <span className="ml-auto h-2 w-2 rounded-full bg-blue-500" />
                )}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-xl border border-slate-800 bg-[#0b1220] p-4">
        <div className="mb-2 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-emerald-400" />
          <span className="text-xs font-semibold text-emerald-400">
            SYSTEM ONLINE
          </span>
        </div>

        <p className="text-xs leading-5 text-slate-500">
          VisionCore monitoring system is running normally.
        </p>
      </div>

      <button className="mt-5 flex items-center gap-2 px-3 text-xs text-slate-500 hover:text-white">
        <ChevronLeft size={16} />
        Collapse sidebar
      </button>
    </aside>
  );
}
