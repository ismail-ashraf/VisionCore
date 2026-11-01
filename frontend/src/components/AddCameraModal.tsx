
import { useState } from "react";
import { X, Camera, Plus } from "lucide-react";

interface AddCameraModalProps {
  onClose: () => void;
  onAdded: () => Promise<void>;
}

function AddCameraModal({ onClose, onAdded }: AddCameraModalProps) {
  const [cameraId, setCameraId] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setLoading(true);
    setError(null);

    try {
      const API_BASE_URL =
        import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

      const response = await fetch(`${API_BASE_URL}/cameras`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          camera_id: cameraId.trim(),
          source_url: sourceUrl.trim(),
        }),
      });

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          data?.detail || data?.message || `Request failed: ${response.status}`
        );
      }

      await onAdded();
      setSuccess(true);

      setTimeout(() => {
        onClose();
      }, 800);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to add camera"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4">
      <div className="w-full max-w-lg rounded-2xl border border-slate-700 bg-[#111a2b] p-6 shadow-2xl">
        <div className="mb-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-500/10 p-3">
              <Camera className="text-blue-400" size={22} />
            </div>

            <div>
              <h2 className="text-lg font-semibold text-white">
                Add New Camera
              </h2>
              <p className="text-xs text-slate-400">
                Connect a new video source to VisionCore
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-800 hover:text-white"
          >
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Camera ID
            </label>

            <input
              type="text"
              value={cameraId}
              onChange={(event) => setCameraId(event.target.value)}
              placeholder="e.g. camera-01"
              required
              className="w-full rounded-xl border border-slate-700 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500"
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-slate-300">
              Source URL / Video Path
            </label>

            <input
              type="text"
              value={sourceUrl}
              onChange={(event) => setSourceUrl(event.target.value)}
              placeholder="C:\Videos\video.mp4 or rtsp://..."
              required
              className="w-full rounded-xl border border-slate-700 bg-[#0b1220] px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500"
            />

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Enter a local video path on the backend machine or an RTSP stream URL.
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-3">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}

          {success && (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-3">
              <p className="text-sm text-emerald-400">
                Camera added successfully!
              </p>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-slate-700 px-4 py-2.5 text-sm text-slate-300 transition hover:bg-slate-800"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading || success}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Plus size={17} />
              {loading ? "Adding..." : "Add Camera"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddCameraModal;
