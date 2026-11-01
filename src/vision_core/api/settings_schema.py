
from pydantic import BaseModel, Field, ConfigDict


class RuntimeSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confidence_threshold: float | None = Field(
        default=None, ge=0, le=1
    )

    max_batch_size: int | None = Field(
        default=None, gt=0
    )

    max_wait_ms: float | None = Field(
        default=None, gt=0
    )

    metrics_interval: float | None = Field(
        default=None, gt=0
    )

    drift_window_size: int | None = Field(
        default=None, gt=0
    )

    drift_monitor_interval: float | None = Field(
        default=None, gt=0
    )
