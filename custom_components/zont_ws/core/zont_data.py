from dataclasses import dataclass, field


@dataclass
class ZontDeviceInfo:
    model: str = ''
    hardware: str = ''
    software: str = ''


@dataclass
class ZontData:
    device_info: ZontDeviceInfo = field(default_factory=ZontDeviceInfo)
    ids: list[int] = field(default_factory=list)
    controls: dict[int, dict] = field(default_factory=dict)
