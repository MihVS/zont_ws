from dataclasses import dataclass, field


@dataclass
class ZontDeviceInfo:
    model: str = ''
    hardware: str = ''
    software: str = ''


@dataclass
class ZontData:
    device_info: ZontDeviceInfo = field(default_factory=ZontDeviceInfo)
    ids: list[str] = field(default_factory=list)
    controls: dict[str, dict] = field(default_factory=dict)
