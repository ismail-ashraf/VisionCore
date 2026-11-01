
import { useCallback, useEffect, useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Line,
  LineChart,
} from "recharts";
import {
  Activity,
  Clock3,
  Layers,
  AlertTriangle,
  RefreshCw,
  TrendingUp,
} from "lucide-react";
import { apiGet } from "../api/client";

type PerformanceSnapshot = {
  timestamp: number;
  throughput_fps: number;
  average_batch_latency_ms: number;
  average_wait_time_ms: number;
  queue_size: number;
  total_errors: number;
};

type PerformanceResponse = {
  total: number;
  hours: number;
  snapshots: PerformanceSnapshot[];
};

type DriftReport = {
  timestamp: number;
  camera_id: string;
  brightness_psi: number;
  brightness_status: string;
  contrast_psi: number;
  contrast_status: string;
  sharpness_psi: number;
  sharpness_status: string;
};

type DriftResponse = {
  total: number;
  hours: number;
  camera_id: string | null;
  reports: DriftReport[];
};

const periods = [
  { label: "1 Hour", value: 1 },
  { label: "6 Hours", value: 6 },
  { label: "24 Hours", value: 24 },
  { label: "7 Days", value: 168 },
];

function formatTime(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(timestamp: number) {
  return new Date(timestamp * 1000).toLocaleString();
}

function MetricCard({
  title,
  value,
  unit,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  unit?: string;
  icon: typeof Activity;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#111a2b] p-5">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-400">{title}</p>
        <div className={`rounded-lg bg-slate-800/70 p-2 ${color}`}>
          <Icon size={19} />
        </div>
      </div>

      <div className="mt-4 flex items-baseline gap-2">
        <span className="text-3xl font-semibold text-white">{value}</span>
        {unit && <span className="text-sm text-slate-400">{unit}</span>}
      </div>
    </div>
  );
}

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-[#111a2b] p-5">
      <div className="mb-6">
        <h3 className="font-semibold text-white">{title}</h3>
        <p className="mt-1 text-xs text-slate-500">{subtitle}</p>
      </div>
      <div className="h-[280px]">{children}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();

  const styles =
    normalized === "low"
      ? "bg-emerald-500/10 text-emerald-400"
      : normalized === "moderate"
        ? "bg-amber-500/10 text-amber-400"
        : "bg-red-500/10 text-red-400";

  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${styles}`}>
      {status}
    </span>
  );
}

export default function Analytics() {
  const [hours, setHours] = useState(24);
  const [performance, setPerformance] = useState<PerformanceSnapshot[]>([]);
  const [driftReports, setDriftReports] = useState<DriftReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setError(null);

      const [performanceData, driftData] = await Promise.all([
        apiGet<PerformanceResponse>(
          `/analytics/performance?hours=${hours}&limit=1000`,
        ),
        apiGet<DriftResponse>(
          `/analytics/drift?hours=${hours}&limit=1000`,
        ),
      ]);

      setPerformance(performanceData.snapshots);
      setDriftReports(driftData.reports);
      setLastUpdated(new Date());
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load analytics data",
      );
    } finally {
      setLoading(false);
    }
  }, [hours]);

  useEffect(() => {
    setLoading(true);
    fetchAnalytics();

    const interval = setInterval(fetchAnalytics, 10000);

    return () => clearInterval(interval);
  }, [fetchAnalytics]);

  const latest = performance[performance.length - 1];

  const averageLatency =
    performance.length > 0
      ? performance.reduce(
          (sum, item) => sum + item.average_batch_latency_ms,
          0,
        ) / performance.length
      : 0;

  const chartData = performance.map((item) => ({
    ...item,
    time: formatTime(item.timestamp),
  }));

  return (
    <div className="min-h-screen space-y-6 bg-[#0b1220] p-6 text-white">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2">
            <TrendingUp className="text-blue-400" size={22} />
            <h1 className="text-2xl font-bold">Analytics</h1>
          </div>
          <p className="mt-1 text-sm text-slate-400">
            Historical performance and system monitoring
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <select
            value={hours}
            onChange={(e) => setHours(Number(e.target.value))}
            className="rounded-lg border border-slate-700 bg-[#111a2b] px-3 py-2 text-sm text-white outline-none focus:border-blue-500"
          >
            {periods.map((period) => (
              <option key={period.value} value={period.value}>
                {period.label}
              </option>
            ))}
          </select>

          <button
            onClick={fetchAnalytics}
            className="flex items-center gap-2 rounded-lg border border-slate-700 bg-[#111a2b] px-3 py-2 text-sm text-slate-300 transition hover:bg-slate-800"
          >
            <RefreshCw size={15} />
            Refresh
          </button>
        </div>
      </div>

      {lastUpdated && (
        <p className="text-xs text-slate-500">
          Last updated: {lastUpdated.toLocaleTimeString()}
        </p>
      )}

      {error && (
        <div className="flex items-center gap-3 rounded-lg border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-300">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Latest Throughput"
          value={latest ? latest.throughput_fps.toFixed(2) : "--"}
          unit="FPS"
          icon={Activity}
          color="text-blue-400"
        />

        <MetricCard
          title="Average Batch Latency"
          value={performance.length ? averageLatency.toFixed(2) : "--"}
          unit="ms"
          icon={Clock3}
          color="text-violet-400"
        />

        <MetricCard
          title="Latest Queue Size"
          value={latest ? latest.queue_size : "--"}
          icon={Layers}
          color="text-amber-400"
        />

        <MetricCard
          title="Total Errors"
          value={latest ? latest.total_errors : "--"}
          icon={AlertTriangle}
          color="text-red-400"
        />
      </div>

      {/* Loading / Empty State */}
      {loading && performance.length === 0 ? (
        <div className="rounded-xl border border-slate-800 bg-[#111a2b] p-12 text-center text-slate-400">
          Loading analytics data...
        </div>
      ) : (
        <>
          {performance.length === 0 && !error && (
            <div className="rounded-xl border border-slate-800 bg-[#111a2b] p-10 text-center">
              <Activity className="mx-auto mb-3 text-slate-500" size={30} />
              <h3 className="font-medium text-white">No performance data</h3>
              <p className="mt-1 text-sm text-slate-500">
                No snapshots were recorded during this period.
              </p>
            </div>
          )}

          {/* Charts */}
          {performance.length > 0 && (
            <div className="grid grid-cols-1 gap-5 xl:grid-cols-2">
              <ChartCard
                title="Throughput History"
                subtitle="Recorded inference throughput over time"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <defs>
                      <linearGradient
                        id="throughputGradient"
                        x1="0"
                        y1="0"
                        x2="0"
                        y2="1"
                      >
                        <stop
                          offset="0%"
                          stopColor="#3b82f6"
                          stopOpacity={0.3}
                        />
                        <stop
                          offset="95%"
                          stopColor="#3b82f6"
                          stopOpacity={0}
                        />
                      </linearGradient>
                    </defs>

                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#263449"
                    />
                    <XAxis
                      dataKey="time"
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                      minTickGap={25}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#111a2b",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#cbd5e1" }}
                    />
                    <Area
                      type="monotone"
                      dataKey="throughput_fps"
                      name="Throughput"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      fill="url(#throughputGradient)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard
                title="Inference Latency"
                subtitle="Average batch inference time in milliseconds"
              >
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#263449"
                    />
                    <XAxis
                      dataKey="time"
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                      minTickGap={25}
                    />
                    <YAxis
                      stroke="#64748b"
                      tick={{ fontSize: 11 }}
                    />
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#111a2b",
                        border: "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#cbd5e1" }}
                    />
                    <Line
                      type="monotone"
                      dataKey="average_batch_latency_ms"
                      name="Latency"
                      stroke="#a78bfa"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>
          )}

          {/* Drift History */}
          <div className="overflow-hidden rounded-xl border border-slate-800 bg-[#111a2b]">
            <div className="flex items-center justify-between border-b border-slate-800 p-5">
              <div>
                <h3 className="font-semibold text-white">Drift History</h3>
                <p className="mt-1 text-xs text-slate-500">
                  Historical feature distribution changes
                </p>
              </div>
              <span className="rounded-full bg-slate-800 px-3 py-1 text-xs text-slate-300">
                {driftReports.length} Reports
              </span>
            </div>

            {driftReports.length === 0 ? (
              <div className="p-10 text-center">
                <AlertTriangle
                  className="mx-auto mb-3 text-slate-500"
                  size={28}
                />
                <h3 className="font-medium text-white">
                  No drift reports available
                </h3>
                <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                  Historical drift reports have not been stored yet. Once
                  persistence is enabled, they will appear here.
                </p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-800/40 text-xs uppercase text-slate-400">
                    <tr>
                      <th className="px-5 py-3">Camera</th>
                      <th className="px-5 py-3">Date</th>
                      <th className="px-5 py-3">Brightness</th>
                      <th className="px-5 py-3">Contrast</th>
                      <th className="px-5 py-3">Sharpness</th>
                    </tr>
                  </thead>
                  <tbody>
                    {driftReports.map((report, index) => (
                      <tr
                        key={`${report.camera_id}-${report.timestamp}-${index}`}
                        className="border-t border-slate-800 text-slate-300"
                      >
                        <td className="px-5 py-4 font-medium text-white">
                          {report.camera_id}
                        </td>
                        <td className="whitespace-nowrap px-5 py-4 text-slate-400">
                          {formatDate(report.timestamp)}
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            {report.brightness_psi.toFixed(3)}
                            <StatusBadge status={report.brightness_status} />
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            {report.contrast_psi.toFixed(3)}
                            <StatusBadge status={report.contrast_status} />
                          </div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="flex items-center gap-2">
                            {report.sharpness_psi.toFixed(3)}
                            <StatusBadge status={report.sharpness_status} />
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
