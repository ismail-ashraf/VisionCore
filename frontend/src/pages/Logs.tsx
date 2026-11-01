
import { useCallback, useEffect, useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Search,
  Server,
} from "lucide-react";
import { apiGet } from "../api/client";

type SystemLog = {
  id: number;
  timestamp: number;
  level: string;
  event: string;
  message: string;
  camera_id: string | null;
};

type LogsResponse = {
  total: number;
  filters: {
    hours: number;
    level: string | null;
    camera_id: string | null;
    search: string | null;
  };
  logs: SystemLog[];
};

const levelStyles: Record<string, string> = {
  INFO: "bg-blue-500/10 text-blue-400 border-blue-500/20",
  WARNING: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  ERROR: "bg-red-500/10 text-red-400 border-red-500/20",
  CRITICAL: "bg-red-500/10 text-red-400 border-red-500/20",
};

function getLevelIcon(level: string) {
  switch (level.toUpperCase()) {
    case "ERROR":
    case "CRITICAL":
      return <AlertCircle size={15} />;
    case "WARNING":
      return <AlertTriangle size={15} />;
    default:
      return <CheckCircle2 size={15} />;
  }
}

function formatTimestamp(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleString();
}

export default function Logs() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [total, setTotal] = useState(0);

  const [hours, setHours] = useState("24");
  const [level, setLevel] = useState("ALL");
  const [cameraId, setCameraId] = useState("");
  const [search, setSearch] = useState("");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      setError(null);

      const params = new URLSearchParams({
        hours,
        limit: "1000",
      });

      if (level !== "ALL") {
        params.set("level", level);
      }

      if (cameraId.trim()) {
        params.set("camera_id", cameraId.trim());
      }

      if (search.trim()) {
        params.set("search", search.trim());
      }

      const response = await apiGet<LogsResponse>(
        `/logs?${params.toString()}`
      );

      setLogs(response.logs);
      setTotal(response.total);
      setLastUpdated(new Date());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load system logs"
      );
    } finally {
      setLoading(false);
    }
  }, [hours, level, cameraId, search]);

  useEffect(() => {
    setLoading(true);
    fetchLogs();

    const interval = setInterval(fetchLogs, 10000);

    return () => clearInterval(interval);
  }, [fetchLogs]);

  const errorCount = logs.filter(
    (log) => ["ERROR", "CRITICAL"].includes(log.level.toUpperCase())
  ).length;

  const warningCount = logs.filter(
    (log) => log.level.toUpperCase() === "WARNING"
  ).length;

  const infoCount = logs.filter(
    (log) => log.level.toUpperCase() === "INFO"
  ).length;

  return (
    <div className="space-y-6 text-slate-200">
      {/* Page Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-slate-400">
            <Server size={17} />
            <span className="text-sm">Monitoring / System Logs</span>
          </div>

          <h1 className="mt-2 text-2xl font-semibold text-white">
            System Logs
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            Monitor system events, warnings, and errors.
          </p>
        </div>

        <button
          onClick={() => {
            setLoading(true);
            fetchLogs();
          }}
          disabled={loading}
          className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm text-slate-200 transition hover:bg-slate-700 disabled:opacity-50"
        >
          <RefreshCw size={15} className={loading ? "animate-spin" : ""} />
          Refresh
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SummaryCard
          title="Total Events"
          value={total}
          icon={<Server size={19} />}
          color="text-blue-400"
        />

        <SummaryCard
          title="Info"
          value={infoCount}
          icon={<CheckCircle2 size={19} />}
          color="text-blue-400"
        />

        <SummaryCard
          title="Warnings"
          value={warningCount}
          icon={<AlertTriangle size={19} />}
          color="text-yellow-400"
        />

        <SummaryCard
          title="Errors"
          value={errorCount}
          icon={<AlertCircle size={19} />}
          color="text-red-400"
        />
      </div>

      {/* Filters */}
      <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="font-medium text-white">Filters</h2>

          {lastUpdated && (
            <span className="text-xs text-slate-500">
              Updated: {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-4">
          <div>
            <label className="mb-2 block text-xs text-slate-400">
              Time Range
            </label>
            <select
              value={hours}
              onChange={(e) => setHours(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-200 outline-none focus:border-blue-500"
            >
              <option value="1">Last hour</option>
              <option value="6">Last 6 hours</option>
              <option value="24">Last 24 hours</option>
              <option value="168">Last 7 days</option>
              <option value="720">Last 30 days</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs text-slate-400">
              Log Level
            </label>
            <select
              value={level}
              onChange={(e) => setLevel(e.target.value)}
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm outline-none focus:border-blue-500"
            >
              <option value="ALL">All Levels</option>
              <option value="INFO">Info</option>
              <option value="WARNING">Warning</option>
              <option value="ERROR">Error</option>
              <option value="CRITICAL">Critical</option>
            </select>
          </div>

          <div>
            <label className="mb-2 block text-xs text-slate-400">
              Camera ID
            </label>
            <input
              value={cameraId}
              onChange={(e) => setCameraId(e.target.value)}
              placeholder="Search camera ID..."
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2.5 text-sm text-slate-200 outline-none placeholder:text-slate-600 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-xs text-slate-400">
              Search Events
            </label>
            <div className="flex items-center gap-2 rounded-lg border border-slate-700 bg-slate-950 px-3">
              <Search size={16} className="text-slate-500" />
              <input
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search logs..."
                className="w-full bg-transparent py-2.5 text-sm text-slate-200 outline-none placeholder:text-slate-600"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Logs Table */}
      <div className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-800 px-5 py-4">
          <h2 className="font-medium text-white">Event History</h2>
          <span className="text-xs text-slate-500">
            {logs.length} records loaded
          </span>
        </div>

        {error ? (
          <div className="flex flex-col items-center gap-3 px-5 py-16 text-center">
            <AlertCircle size={30} className="text-red-400" />
            <p className="text-sm text-red-400">{error}</p>
            <button
              onClick={() => {
                setLoading(true);
                fetchLogs();
              }}
              className="rounded-lg bg-slate-800 px-4 py-2 text-sm hover:bg-slate-700"
            >
              Try Again
            </button>
          </div>
        ) : loading && logs.length === 0 ? (
          <div className="px-5 py-16 text-center text-sm text-slate-400">
            Loading system logs...
          </div>
        ) : logs.length === 0 ? (
          <div className="flex flex-col items-center gap-3 px-5 py-16 text-center">
            <Clock size={30} className="text-slate-600" />
            <p className="text-sm text-slate-300">No logs found</p>
            <p className="text-xs text-slate-500">
              Try changing your filters or wait for new system events.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[850px] text-left text-sm">
              <thead className="bg-slate-950/70 text-xs uppercase text-slate-500">
                <tr>
                  <th className="px-5 py-3 font-medium">Timestamp</th>
                  <th className="px-5 py-3 font-medium">Level</th>
                  <th className="px-5 py-3 font-medium">Event</th>
                  <th className="px-5 py-3 font-medium">Camera</th>
                  <th className="px-5 py-3 font-medium">Message</th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800">
                {logs.map((log) => (
                  <tr
                    key={log.id}
                    className="transition hover:bg-slate-800/40"
                  >
                    <td className="whitespace-nowrap px-5 py-4 text-xs text-slate-400">
                      {formatTimestamp(log.timestamp)}
                    </td>

                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-xs font-medium ${
                          levelStyles[log.level.toUpperCase()] ??
                          "border-slate-700 bg-slate-800 text-slate-300"
                        }`}
                      >
                        {getLevelIcon(log.level)}
                        {log.level}
                      </span>
                    </td>

                    <td className="whitespace-nowrap px-5 py-4 font-mono text-xs text-slate-300">
                      {log.event}
                    </td>

                    <td className="px-5 py-4 text-xs text-slate-400">
                      {log.camera_id ?? "—"}
                    </td>

                    <td className="max-w-md px-5 py-4 text-xs leading-5 text-slate-300">
                      {log.message}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  title,
  value,
  icon,
  color,
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-slate-400">{title}</span>
        <span className={color}>{icon}</span>
      </div>

      <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
    </div>
  );
}
