
import { useEffect, useState, type ReactNode } from "react";
import {
  Activity,
  Cpu,
  Database,
  Gauge,
  Info,
  RotateCcw,
  Settings as SettingsIcon,
  ShieldCheck,
  Save,
  Loader2,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

type RuntimeSettings = {
  confidence_threshold: number;
  device: string;
  max_batch_size: number;
  max_wait_ms: number;
  metrics_interval: number;
  drift_window_size: number;
  drift_monitor_interval: number;
  device_change_supported: boolean;
};

type SettingsDraft = Omit<RuntimeSettings, "device_change_supported">;

const DEFAULT_SETTINGS: SettingsDraft = {
  confidence_threshold: 0.5,
  device: "cpu",
  max_batch_size: 4,
  max_wait_ms: 15,
  metrics_interval: 10,
  drift_window_size: 1000,
  drift_monitor_interval: 30,
};

export default function Settings() {
  const [settings, setSettings] = useState<SettingsDraft>(DEFAULT_SETTINGS);
  const [deviceChangeSupported, setDeviceChangeSupported] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [savedSettings, setSavedSettings] =
    useState<SettingsDraft>(DEFAULT_SETTINGS);

  // Fetch current settings from the backend.
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(`${API_BASE_URL}/settings`);

        if (!response.ok) {
          throw new Error(`Failed to load settings (${response.status})`);
        }

        const data: RuntimeSettings = await response.json();

        const currentSettings: SettingsDraft = {
          confidence_threshold: data.confidence_threshold,
          device: data.device,
          max_batch_size: data.max_batch_size,
          max_wait_ms: data.max_wait_ms,
          metrics_interval: data.metrics_interval,
          drift_window_size: data.drift_window_size,
          drift_monitor_interval: data.drift_monitor_interval,
        };

        setSettings(currentSettings);
        setSavedSettings(currentSettings);
        setDeviceChangeSupported(data.device_change_supported);
      } catch (err) {
        setError(
          err instanceof Error
            ? err.message
            : "Could not connect to VisionCore backend."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  const updateSetting = <K extends keyof SettingsDraft>(
    key: K,
    value: SettingsDraft[K]
  ) => {
    setSettings((previous) => ({
      ...previous,
      [key]: value,
    }));

    setSuccess("");
    setError("");
  };

  const hasChanges =
    JSON.stringify(settings) !== JSON.stringify(savedSettings);

  // Send updated settings to the backend.
  const saveSettings = async () => {
    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const updates: Partial<SettingsDraft> = {};

      (
        Object.keys(settings) as Array<keyof SettingsDraft>
      ).forEach((key) => {
        if (settings[key] !== savedSettings[key]) {
          updates[key] = settings[key] as never;
        }
      });

      const response = await fetch(`${API_BASE_URL}/settings`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updates),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || `Failed to save settings (${response.status})`
        );
      }

      const updatedSettings: SettingsDraft = {
        confidence_threshold: data.confidence_threshold,
        device: data.device,
        max_batch_size: data.max_batch_size,
        max_wait_ms: data.max_wait_ms,
        metrics_interval: data.metrics_interval,
        drift_window_size: data.drift_window_size,
        drift_monitor_interval: data.drift_monitor_interval,
      };

      setSettings(updatedSettings);
      setSavedSettings(updatedSettings);
      setDeviceChangeSupported(data.device_change_supported);
      setSuccess("Settings updated successfully.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to save settings."
      );
    } finally {
      setSaving(false);
    }
  };

  // Reset backend settings to the project's default values.
  const resetSettings = async () => {
    try {
      setSaving(true);
      setError("");
      setSuccess("");

      const response = await fetch(`${API_BASE_URL}/settings`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          confidence_threshold: DEFAULT_SETTINGS.confidence_threshold,
          max_batch_size: DEFAULT_SETTINGS.max_batch_size,
          max_wait_ms: DEFAULT_SETTINGS.max_wait_ms,
          metrics_interval: DEFAULT_SETTINGS.metrics_interval,
          drift_window_size: DEFAULT_SETTINGS.drift_window_size,
          drift_monitor_interval:
            DEFAULT_SETTINGS.drift_monitor_interval,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || `Failed to reset settings (${response.status})`
        );
      }

      const updatedSettings: SettingsDraft = {
        confidence_threshold: data.confidence_threshold,
        device: data.device,
        max_batch_size: data.max_batch_size,
        max_wait_ms: data.max_wait_ms,
        metrics_interval: data.metrics_interval,
        drift_window_size: data.drift_window_size,
        drift_monitor_interval: data.drift_monitor_interval,
      };

      setSettings(updatedSettings);
      setSavedSettings(updatedSettings);
      setDeviceChangeSupported(data.device_change_supported);
      setSuccess("Settings restored to default values.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to reset settings."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-slate-400">
        <div className="flex items-center gap-3">
          <Loader2 size={20} className="animate-spin text-blue-400" />
          <span className="text-sm">Loading system settings...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6 text-slate-200 md:p-8">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <SettingsIcon size={16} />
            <span>Configuration / Settings</span>
          </div>

          <h1 className="mt-2 text-2xl font-semibold text-white">
            System Settings
          </h1>

          <p className="mt-1 text-sm text-slate-400">
            Configure detection, performance, and monitoring parameters.
          </p>
        </div>

        <button
          onClick={resetSettings}
          disabled={saving || !hasChanges && JSON.stringify(savedSettings) === JSON.stringify(DEFAULT_SETTINGS)}
          className="flex items-center justify-center gap-2 rounded-lg border border-slate-700 bg-slate-800 px-4 py-2 text-sm transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <RotateCcw size={15} />
          Reset Defaults
        </button>
      </div>

      {/* API Status */}
      <div className="flex items-start gap-3 rounded-xl border border-blue-500/20 bg-blue-500/5 p-4">
        <Info size={19} className="mt-0.5 shrink-0 text-blue-400" />
        <div>
          <p className="text-sm font-medium text-blue-300">
            Live Backend Configuration
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-400">
            Settings are loaded from and applied directly to the running
            VisionCore backend.
          </p>
        </div>
      </div>

      {error && (
        <StatusMessage type="error" message={error} />
      )}

      {success && (
        <StatusMessage type="success" message={success} />
      )}

      {/* Detection Settings */}
      <SettingsSection
        title="Detection Settings"
        description="Configure the YOLO inference behavior."
        icon={<ShieldCheck size={19} />}
      >
        <div className="grid gap-6 md:grid-cols-2">
          <div>
            <div className="mb-3 flex items-center justify-between">
              <label className="text-sm text-slate-300">
                Confidence Threshold
              </label>
              <span className="font-mono text-sm text-blue-400">
                {settings.confidence_threshold.toFixed(2)}
              </span>
            </div>

            <input
              type="range"
              min="0.05"
              max="1"
              step="0.05"
              value={settings.confidence_threshold}
              onChange={(e) =>
                updateSetting(
                  "confidence_threshold",
                  Number(e.target.value)
                )
              }
              className="w-full accent-blue-500"
            />

            <div className="mt-2 flex justify-between text-xs text-slate-500">
              <span>0.05</span>
              <span>1.00</span>
            </div>

            <p className="mt-3 text-xs leading-5 text-slate-500">
              Controls the minimum confidence required for a detection
              to be accepted.
            </p>
          </div>

          <div>
            <label className="mb-3 block text-sm text-slate-300">
              Inference Device
            </label>

            <select
              value={settings.device}
              disabled={!deviceChangeSupported}
              onChange={(e) =>
                updateSetting("device", e.target.value)
              }
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-200 outline-none focus:border-blue-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              <option value="cpu">CPU</option>
              <option value="cuda">CUDA</option>
            </select>

            <p className="mt-3 text-xs leading-5 text-slate-500">
              Current inference device. Changing it requires model
              reinitialization and is not currently supported.
            </p>
          </div>
        </div>
      </SettingsSection>

      {/* Performance Settings */}
      <SettingsSection
        title="Performance Settings"
        description="Tune batching and metrics collection."
        icon={<Gauge size={19} />}
      >
        <div className="grid gap-5 md:grid-cols-3">
          <NumberSetting
            label="Maximum Batch Size"
            value={settings.max_batch_size}
            min={1}
            max={32}
            unit="frames"
            onChange={(value) => updateSetting("max_batch_size", value)}
            description="Maximum frames processed together."
          />

          <NumberSetting
            label="Maximum Wait Time"
            value={settings.max_wait_ms}
            min={1}
            max={100}
            unit="ms"
            onChange={(value) => updateSetting("max_wait_ms", value)}
            description="Maximum time to wait for a full batch."
          />

          <NumberSetting
            label="Metrics Interval"
            value={settings.metrics_interval}
            min={1}
            max={60}
            unit="seconds"
            onChange={(value) =>
              updateSetting("metrics_interval", value)
            }
            description="How often performance metrics are collected."
          />
        </div>
      </SettingsSection>

      {/* Drift Settings */}
      <SettingsSection
        title="Drift Monitoring"
        description="Configure the data drift monitoring window."
        icon={<Activity size={19} />}
      >
        <div className="grid gap-5 md:grid-cols-2">
          <NumberSetting
            label="Window Size"
            value={settings.drift_window_size}
            min={100}
            max={10000}
            unit="frames"
            onChange={(value) =>
              updateSetting("drift_window_size", value)
            }
            description="Number of recent frames used for drift analysis."
          />

          <NumberSetting
            label="Monitoring Interval"
            value={settings.drift_monitor_interval}
            min={5}
            max={300}
            unit="seconds"
            onChange={(value) =>
              updateSetting("drift_monitor_interval", value)
            }
            description="How often the drift monitor checks the window."
          />
        </div>

        <div className="mt-6 border-t border-slate-800 pt-5">
          <h3 className="mb-3 text-sm font-medium text-slate-300">
            PSI Alert Thresholds
          </h3>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs text-slate-500">Moderate Drift</p>
              <p className="mt-1 text-lg font-semibold text-yellow-400">
                0.10
              </p>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950/70 p-4">
              <p className="text-xs text-slate-500">High Drift</p>
              <p className="mt-1 text-lg font-semibold text-red-400">
                0.25
              </p>
            </div>
          </div>

          <p className="mt-3 text-xs text-slate-500">
            These thresholds are currently fixed in the backend.
          </p>
        </div>
      </SettingsSection>

      {/* System Information */}
      <SettingsSection
        title="System Information"
        description="Current application configuration."
        icon={<Cpu size={19} />}
      >
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <InfoItem
            label="Detection Model"
            value="YOLO"
            icon={<ShieldCheck size={17} />}
          />

          <InfoItem
            label="Inference Device"
            value={settings.device.toUpperCase()}
            icon={<Cpu size={17} />}
          />

          <InfoItem
            label="Database"
            value="SQLite"
            icon={<Database size={17} />}
          />

          <InfoItem
            label="Batch Processing"
            value="Enabled"
            icon={<Activity size={17} />}
          />

          <InfoItem
            label="API Framework"
            value="FastAPI"
            icon={<SettingsIcon size={17} />}
          />

          <InfoItem
            label="Drift Monitoring"
            value="Enabled"
            icon={<Activity size={17} />}
          />
        </div>
      </SettingsSection>

      {/* Save Configuration */}
      <div className="flex flex-col gap-4 rounded-xl border border-slate-800 bg-slate-900 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-medium text-white">
            Configuration Preview
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {hasChanges
              ? "You have unsaved changes."
              : "All settings are synchronized with the backend."}
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span
            className={`rounded-lg border px-3 py-2 text-xs ${
              hasChanges
                ? "border-yellow-500/20 bg-yellow-500/10 text-yellow-400"
                : "border-green-500/20 bg-green-500/10 text-green-400"
            }`}
          >
            {hasChanges ? "Unsaved Changes" : "Applied"}
          </span>

          <button
            onClick={saveSettings}
            disabled={!hasChanges || saving}
            className="flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {saving ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Save size={16} />
            )}
            {saving ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>
    </div>
  );
}

function StatusMessage({
  type,
  message,
}: {
  type: "success" | "error";
  message: string;
}) {
  const isSuccess = type === "success";

  return (
    <div
      className={`flex items-start gap-3 rounded-xl border p-4 ${
        isSuccess
          ? "border-green-500/20 bg-green-500/5 text-green-400"
          : "border-red-500/20 bg-red-500/5 text-red-400"
      }`}
    >
      {isSuccess ? (
        <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
      ) : (
        <AlertCircle size={18} className="mt-0.5 shrink-0" />
      )}

      <p className="text-sm">{message}</p>
    </div>
  );
}

function SettingsSection({
  title,
  description,
  icon,
  children,
}: {
  title: string;
  description: string;
  icon: ReactNode;
  children: ReactNode;
}) {
  return (
    <section className="overflow-hidden rounded-xl border border-slate-800 bg-slate-900">
      <div className="flex items-start gap-3 border-b border-slate-800 px-5 py-4">
        <span className="mt-0.5 text-blue-400">{icon}</span>

        <div>
          <h2 className="font-medium text-white">{title}</h2>
          <p className="mt-1 text-xs text-slate-500">{description}</p>
        </div>
      </div>

      <div className="p-5">{children}</div>
    </section>
  );
}

function NumberSetting({
  label,
  value,
  min,
  max,
  unit,
  description,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  unit: string;
  description: string;
  onChange: (value: number) => void;
}) {
  return (
    <div>
      <label className="mb-2 block text-sm text-slate-300">
        {label}
      </label>

      <div className="flex items-center gap-2">
        <input
          type="number"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-white outline-none focus:border-blue-500"
        />

        <span className="min-w-16 text-xs text-slate-500">{unit}</span>
      </div>

      <p className="mt-2 text-xs leading-5 text-slate-500">
        {description}
      </p>

      <p className="mt-1 text-[11px] text-slate-600">
        Range: {min}–{max}
      </p>
    </div>
  );
}

function InfoItem({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-slate-800 bg-slate-950/60 p-4">
      <span className="text-slate-500">{icon}</span>

      <div>
        <p className="text-xs text-slate-500">{label}</p>
        <p className="mt-1 text-sm font-medium text-slate-200">
          {value}
        </p>
      </div>
    </div>
  );
}
