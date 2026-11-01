import { Bell, Search } from "lucide-react";

export default function Topbar() {
  return (
    <header className="flex h-[76px] items-center justify-between border-b border-slate-800 bg-[#0b1220] px-8">
      <div>
        <h2 className="text-lg font-semibold text-white">Dashboard</h2>
        <p className="text-xs text-slate-500">
          Monitor your computer vision system
        </p>
      </div>

      <div className="flex items-center gap-5">
        <div className="flex items-center gap-2 rounded-lg border border-slate-800 bg-[#111a2b] px-3 py-2">
          <Search size={16} className="text-slate-500" />
          <input
            placeholder="Search..."
            className="w-32 bg-transparent text-sm text-white outline-none placeholder:text-slate-600"
          />
        </div>

        <button className="relative text-slate-400 hover:text-white">
          <Bell size={20} />
          <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-blue-500" />
        </button>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600 text-sm font-bold text-white">
          VC
        </div>
      </div>
    </header>
  );
}