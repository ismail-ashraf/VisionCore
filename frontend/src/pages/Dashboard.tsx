
import { useCallback, useEffect, useRef, useState } from "react";

import {
  Activity,
  Camera,
  Gauge,
  Layers3,
  AlertTriangle,
  Plus,
} from "lucide-react";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

import StatCard from "../components/StatCard";
import CameraCard from "../components/CameraCard";
import AddCameraModal from "../components/AddCameraModal";

import { apiGet } from "../api/client";
import { useSystemMetrics } from "../hooks/useSystemMetrics";

interface PerformancePoint {
  time: string;
  fps: number;
}

interface CameraRecord {
  camera_id: string;
  status: string;
}

interface CamerasResponse {
  total: number;
  cameras: CameraRecord[];
}

interface CameraHealth {
  camera_id: string;
  health_status: string;
  last_frame_at: number | null;
  seconds_since_last_frame: number | null;
  producer_thread_alive: boolean;
  consumer_thread_alive: boolean;
}

interface CameraHealthResponse {
  total_cameras: number;
  cameras: CameraHealth[];
}

function Dashboard() {
  const { metrics, loading, error } = useSystemMetrics();

  const [cameras, setCameras] = useState<CameraRecord[]>([]);
  const [cameraHealth, setCameraHealth] = useState<CameraHealth[]>([]);

  const [totalCameras, setTotalCameras] = useState(0);

  const [camerasLoading, setCamerasLoading] = useState(true);
  const [camerasError, setCamerasError] = useState<string | null>(null);
  const [healthError, setHealthError] = useState<string | null>(null);

  const [showAddCamera, setShowAddCamera] = useState(false);

  // Live throughput chart data.
  const [performanceData, setPerformanceData] = useState<
    PerformancePoint[]
  >([]);

  // Store the previous metrics reading to calculate interval FPS.
  const previousMetrics = useRef<{
    totalFrames: number;
    timestamp: number;
  } | null>(null);

  useEffect(() => {
    if (!metrics) return;

    const now = Date.now();
    const currentFrames = metrics.total_frames;

    // First reading: establish the baseline.
    if (previousMetrics.current === null) {
      previousMetrics.current = {
        totalFrames: currentFrames,
        timestamp: now,
      };

      return;
    }

    const previous = previousMetrics.current;

    const elapsedSeconds = (now - previous.timestamp) / 1000;
    const framesProcessed = currentFrames - previous.totalFrames;

    // Update the baseline for the next reading.
    previousMetrics.current = {
      totalFrames: currentFrames,
      timestamp: now,
    };

    if (elapsedSeconds <= 0) return;

    // Handle a backend restart or counter reset.
    // Start measuring again without adding a misleading point.
    if (framesProcessed < 0) {
      setPerformanceData([]);
      return;
    }

    // Calculate FPS during this specific interval.
    const intervalFps = framesProcessed / elapsedSeconds;

    const point: PerformancePoint = {
      time: new Date(now).toLocaleTimeString(),
      fps: Number(intervalFps.toFixed(2)),
    };

    // Keep only the latest 30 readings.
    setPerformanceData((previousData) =>
      [...previousData, point].slice(-30)
    );
  }, [metrics]);

  // Fetch camera list and health information.
  const refreshCameras = useCallback(async () => {
    const [cameraResult, healthResult] = await Promise.allSettled([
      apiGet<CamerasResponse>("/cameras"),
      apiGet<CameraHealthResponse>("/monitoring/cameras/health"),
    ]);

    // Handle camera list.
    if (cameraResult.status === "fulfilled") {
      const cameraData = cameraResult.value;

      setCameras(cameraData.cameras ?? []);
      setTotalCameras(cameraData.total ?? 0);
      setCamerasError(null);
    } else {
      const message =
        cameraResult.reason instanceof Error
          ? cameraResult.reason.message
          : "Failed to fetch cameras";

      setCamerasError(message);
    }

    // Handle camera health separately.
    // A health API failure should not prevent cameras from appearing.
    if (healthResult.status === "fulfilled") {
      const healthData = healthResult.value;

      setCameraHealth(healthData.cameras ?? []);
      setHealthError(null);
    } else {
      const message =
        healthResult.reason instanceof Error
          ? healthResult.reason.message
          : "Failed to fetch camera health";

      setHealthError(message);
      setCameraHealth([]);
    }

    if (cameraResult.status === "rejected") {
      throw cameraResult.reason;
    }
  }, []);

  // Initial fetch and automatic refresh every 3 seconds.
  useEffect(() => {
    let active = true;

    async function fetchCameras() {
      try {
        await refreshCameras();
      } catch {
        // Error is already handled inside refreshCameras.
      } finally {
        if (active) {
          setCamerasLoading(false);
        }
      }
    }

    fetchCameras();

    const interval = window.setInterval(fetchCameras, 3000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, [refreshCameras]);

  const totalErrors = metrics?.errors.total_errors ?? 0;
  const systemHealthy = !error && totalErrors === 0;

  const healthyCameras = cameraHealth.filter(
    (camera) => camera.health_status === "healthy"
  ).length;

  return (
    <div className="space-y-8 p-8">
      {/* Page heading */}
      <section className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">System Overview</h1>

          <p className="mt-1 text-sm text-slate-500">
            Here's what's happening with your VisionCore system.
          </p>
        </div>

        <div
          className={`flex items-center gap-2 rounded-lg border px-3 py-2 ${
            systemHealthy
              ? "border-emerald-500/20 bg-emerald-500/10"
              : "border-amber-500/20 bg-amber-500/10"
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full ${
              systemHealthy ? "bg-emerald-400" : "bg-amber-400"
            }`}
          />

          <span
            className={`text-xs font-semibold ${
              systemHealthy ? "text-emerald-400" : "text-amber-400"
            }`}
          >
            {error
              ? "BACKEND CONNECTION ERROR"
              : totalErrors > 0
                ? "SYSTEM HAS ERRORS"
                : "SYSTEM OPERATIONAL"}
          </span>
        </div>
      </section>

      {/* System metrics error */}
      {error && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <p className="text-sm font-semibold text-red-400">
            Failed to fetch system metrics
          </p>

          <p className="mt-1 text-xs text-red-300">{error}</p>
        </div>
      )}

      {/* Camera API error */}
      {camerasError && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <p className="text-sm font-semibold text-red-400">
            Failed to fetch cameras
          </p>

          <p className="mt-1 text-xs text-red-300">{camerasError}</p>
        </div>
      )}

      {/* Camera health warning */}
      {healthError && (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/10 p-4">
          <p className="text-sm font-semibold text-amber-400">
            Camera health information is unavailable
          </p>

          <p className="mt-1 text-xs text-amber-300">{healthError}</p>
        </div>
      )}

      {/* Metrics */}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Total Cameras"
          value={camerasLoading ? "..." : String(totalCameras)}
          subtitle="Registered cameras"
          icon={Camera}
          iconColor="text-blue-400"
        />

        <StatCard
          title="Healthy Cameras"
          value={camerasLoading ? "..." : String(healthyCameras)}
          subtitle="Currently healthy streams"
          icon={Activity}
          iconColor="text-emerald-400"
        />

        <StatCard
          title="Inference Throughput"
          value={
            loading
              ? "..."
              : `${(metrics?.throughput_fps ?? 0).toFixed(2)} FPS`
          }
          subtitle="Average FPS since startup"
          icon={Gauge}
          iconColor="text-violet-400"
        />

        <StatCard
          title="Average Latency"
          value={
            loading
              ? "..."
              : `${(
                  metrics?.average_batch_latency_ms ?? 0
                ).toFixed(2)} ms`
          }
          subtitle="Batch inference latency"
          icon={Layers3}
          iconColor="text-amber-400"
        />
      </section>

      {/* Camera Monitoring */}
      <section>
        <div className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-semibold">Camera Monitoring</h2>

            <p className="mt-1 text-xs text-slate-500">
              Live status of connected camera streams
            </p>
          </div>

          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-400">
              {camerasLoading
                ? "Loading cameras..."
                : `${totalCameras} registered`}
            </span>

            <button
              onClick={() => setShowAddCamera(true)}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white transition hover:bg-blue-500"
            >
              <Plus size={16} />
              Add Camera
            </button>
          </div>
        </div>

        {camerasLoading ? (
          <div className="rounded-xl border border-slate-800 bg-[#111a2b] p-8 text-center text-sm text-slate-400">
            Loading cameras...
          </div>
        ) : cameras.length === 0 ? (
          <div className="rounded-xl border border-slate-800 bg-[#111a2b] p-8 text-center">
            <Camera
              size={32}
              className="mx-auto mb-3 text-slate-600"
            />

            <p className="text-sm font-medium text-slate-300">
              No cameras registered
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Add a camera to start monitoring its stream.
            </p>
          </div>
        ) : (
          <div className="grid gap-5 xl:grid-cols-2">
            {cameras.map((camera) => {
              const cameraId = camera.camera_id;

              const health = cameraHealth.find(
                (item) => item.camera_id === cameraId
              );

              const status =
                health?.health_status ?? camera.status ?? "Unknown";

              const lastFrame =
                health?.last_frame_at != null
                  ? `Last frame: ${new Date(
                      health.last_frame_at * 1000
                    ).toLocaleTimeString()}`
                  : "Waiting for first frame";

              return (
                <CameraCard
                  key={cameraId}
                  cameraId={cameraId}
                  status={status}
                  lastFrame={lastFrame}
                  onDeleted={refreshCameras}
                />
              );
            })}
          </div>
        )}
      </section>

      {/* Performance and errors */}
      <section className="grid gap-5 xl:grid-cols-3">
        <div className="rounded-2xl border border-slate-800 bg-[#111a2b] p-5 xl:col-span-2">
          <div className="mb-6 flex items-center justify-between">
            <div>
              <h2 className="font-semibold">Inference Performance</h2>

              <p className="mt-1 text-xs text-slate-500">
                Live throughput — updated every 3 seconds
              </p>
            </div>

            <span className="rounded-lg bg-blue-500/10 px-3 py-1.5 text-xs text-blue-400">
              FPS
            </span>
          </div>

          <div className="h-64 w-full">
            {performanceData.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm text-slate-500">
                Waiting for throughput data...
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={performanceData}>
                  <defs>
                    <linearGradient
                      id="fpsGradient"
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
                    stroke="#263247"
                    strokeDasharray="3 3"
                    vertical={false}
                  />

                  <XAxis
                    dataKey="time"
                    stroke="#64748b"
                    tickLine={false}
                    axisLine={false}
                    fontSize={11}
                  />

                  <YAxis
                    stroke="#64748b"
                    tickLine={false}
                    axisLine={false}
                    fontSize={11}
                    domain={[0, "auto"]}
                  />

                  <Tooltip
                    contentStyle={{
                      background: "#111a2b",
                      border: "1px solid #334155",
                      borderRadius: "10px",
                      color: "#fff",
                    }}
                    formatter={(value) => [
                      `${Number(value).toFixed(2)} FPS`,
                      "Throughput",
                    ]}
                  />

                  <Area
                    type="monotone"
                    dataKey="fps"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    fill="url(#fpsGradient)"
                    isAnimationActive={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* System Health */}
        <div className="rounded-2xl border border-slate-800 bg-[#111a2b] p-5">
          <h2 className="font-semibold">System Health</h2>

          <p className="mt-1 text-xs text-slate-500">
            Current monitoring status
          </p>

          <div className="mt-7 space-y-6">
            {/* Current Request Queue */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Layers3 size={18} className="text-blue-400" />

                <span className="text-sm text-slate-300">
                  Request Queue
                </span>
              </div>

              <span className="text-sm font-semibold text-white">
                {loading ? "..." : metrics?.queue_size ?? 0}
              </span>
            </div>

            {/* Peak Request Queue */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Layers3 size={18} className="text-violet-400" />

                <span className="text-sm text-slate-300">
                  Peak Queue
                </span>
              </div>

              <span className="text-sm font-semibold text-white">
                {loading ? "..." : metrics?.max_queue_size ?? 0}
              </span>
            </div>

            {/* Total Errors */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <AlertTriangle
                  size={18}
                  className="text-amber-400"
                />

                <span className="text-sm text-slate-300">
                  Total Errors
                </span>
              </div>

              <span
                className={`text-sm font-semibold ${
                  totalErrors > 0
                    ? "text-red-400"
                    : "text-emerald-400"
                }`}
              >
                {loading ? "..." : totalErrors}
              </span>
            </div>

            {/* System Status */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Activity
                  size={18}
                  className="text-emerald-400"
                />

                <span className="text-sm text-slate-300">
                  System Status
                </span>
              </div>

              <span
                className={`text-xs font-semibold ${
                  systemHealthy
                    ? "text-emerald-400"
                    : "text-amber-400"
                }`}
              >
                {loading
                  ? "LOADING"
                  : systemHealthy
                    ? "HEALTHY"
                    : "CHECK SYSTEM"}
              </span>
            </div>
          </div>

          <div
            className={`mt-8 rounded-xl border p-4 ${
              systemHealthy
                ? "border-emerald-500/10 bg-emerald-500/5"
                : "border-amber-500/10 bg-amber-500/5"
            }`}
          >
            <p
              className={`text-xs leading-5 ${
                systemHealthy
                  ? "text-emerald-300"
                  : "text-amber-300"
              }`}
            >
              {error
                ? "Unable to retrieve system metrics. Check the backend connection."
                : totalErrors > 0
                  ? `${totalErrors} inference errors have been recorded. Check system logs.`
                  : loading
                    ? "Loading system information..."
                    : "No inference errors recorded. Monitoring metrics are being updated."}
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-slate-800 pt-5 text-center text-xs text-slate-600">
        VisionCore AI Monitoring Platform
      </footer>

      {/* Add Camera Modal */}
      {showAddCamera && (
        <AddCameraModal
          onClose={() => setShowAddCamera(false)}
          onAdded={refreshCameras}
        />
      )}
    </div>
  );
}

export default Dashboard;
