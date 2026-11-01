import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

export interface SystemMetrics {
  total_batches: number;
  total_frames: number;
  average_batch_latency_ms: number;
  last_latency_ms: number;
  throughput_fps: number;
  average_wait_time_ms: number;
  last_wait_time_ms: number;
  queue_size: number;
  max_queue_size: number;
  errors: {
    total_errors: number;
    total_failed_frames: number;
    last_error: string | null;
    last_error_at: number | null;
  };
}

export function useSystemMetrics() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function fetchMetrics() {
      try {
        const data = await apiGet<SystemMetrics>("/monitoring/system");

        if (active) {
          setMetrics(data);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Failed to fetch metrics"
          );
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    fetchMetrics();

    const interval = window.setInterval(fetchMetrics, 3000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return { metrics, loading, error };
}