import { useEffect, useState } from "react";
import { apiGet } from "../api/client";

interface Camera {
  camera_id: string;
  status: string;
}

interface CamerasResponse {
  total: number;
  cameras: Camera[];
}

export function useCameras() {
  const [totalCameras, setTotalCameras] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function fetchCameras() {
      try {
        const data = await apiGet<CamerasResponse>("/cameras");

        if (active) {
          setTotalCameras(data.total);
          setError(null);
        }
      } catch (err) {
        if (active) {
          setError(
            err instanceof Error ? err.message : "Failed to fetch cameras"
          );
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    fetchCameras();

    const interval = window.setInterval(fetchCameras, 3000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return { totalCameras, loading, error };
}