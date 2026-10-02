from dataclasses import dataclass

@dataclass
class Detection:
    bbox:list[float]
    class_id : int
    confidence : float
    class_name : str