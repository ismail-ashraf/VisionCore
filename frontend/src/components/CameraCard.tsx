
import { useState } from "react";
import {
  Camera,
  Circle,
  MoreHorizontal,
  Trash2,
} from "lucide-react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type CameraCardProps = {
  cameraId: string;
  status: string;
  lastFrame: string;
  onDeleted: () => void;
};

export default function CameraCard({
  cameraId,
  status,
  lastFrame,
  onDeleted,
}: CameraCardProps) {
  const [menuOpen, setMenuOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");

  const normalizedStatus = status.toLowerCase();

  const isHealthy = normalizedStatus === "healthy";
  const isRunning = normalizedStatus === "running";
  const isLive = isHealthy || isRunning;

  const statusColor = isHealthy
    ? "text-emerald-400"
    : isRunning
      ? "text-blue-400"
      : "text-amber-400";

  const streamUrl = `${API_BASE_URL}/cameras/${encodeURIComponent(cameraId)}/stream`;

  async function handleDelete() {
    const confirmed = window.confirm(
      `Are you sure you want to delete camera "${cameraId}"?`
    );

    if (!confirmed) return;

    try {
      setDeleting(true);
      setError("");

      const response = await fetch(
        `${API_BASE_URL}/cameras/${encodeURIComponent(cameraId)}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const result = await response.json().catch(() => null);
        throw new Error(result?.detail || "Failed to delete camera");
      }

      setMenuOpen(false);
      onDeleted();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Something went wrong"
      );
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-800 bg-[#111a2b]">
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3">
          <div className="rounded-lg bg-blue-500/10 p-2 text-blue-400">
            <Camera size={18} />
          </div>

          <div>
            <h3 className="text-sm font-semibold text-white">
              {cameraId}
            </h3>
            <p className="text-xs text-slate-500">Video stream</p>
          </div>
        </div>

        <div className="relative">
          <button
            onClick={() => setMenuOpen((prev) => !prev)}
            disabled={deleting}
            className="rounded-lg p-1 text-slate-500 transition hover:bg-slate-800 hover:text-white"
            aria-label="Camera options"
          >
            <MoreHorizontal size={20} />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-9 z-50 w-44 overflow-hidden rounded-lg border border-slate-700 bg-[#172235] shadow-xl">
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="flex w-full items-center gap-2 px-3 py-2.5 text-left text-sm text-red-400 transition hover:bg-red-500/10 disabled:opacity-50"
              >
                <Trash2 size={16} />
                {deleting ? "Deleting..." : "Delete Camera"}
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="relative aspect-video overflow-hidden bg-[#080e19]">
        {isLive ? (
          <img
            src={streamUrl}
            alt={`Live feed from ${cameraId}`}
            className="h-full w-full object-contain"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-slate-600">
            <Camera size={35} strokeWidth={1.3} />
            <span className="text-xs">Camera is offline</span>
          </div>
        )}

        <div className="absolute left-3 top-3 flex items-center gap-2 rounded-md bg-black/60 px-2 py-1">
          <span
            className={`h-2 w-2 rounded-full ${
              isLive ? "bg-red-500" : "bg-slate-500"
            }`}
          />

          <span className="text-[10px] font-semibold tracking-wider text-white">
            {isLive ? "LIVE" : "OFFLINE"}
          </span>
        </div>
      </div>

      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-2">
          <Circle
            size={9}
            fill="currentColor"
            className={statusColor}
          />

          <span className="text-xs text-slate-300">
            {status}
          </span>
        </div>

        <span className="text-xs text-slate-500">
          {lastFrame}
        </span>
      </div>

      {error && (
        <p className="px-4 pb-3 text-xs text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}
