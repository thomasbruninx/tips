from __future__ import annotations

from dataclasses import dataclass


@dataclass
class _Key:
    module: "FakeWinReg"
    hive: str
    key_path: str

    def __enter__(self):
        self.module._store.setdefault((self.hive, self.key_path), {})
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeWinReg:
    HKEY_CURRENT_USER = "HKCU"
    HKEY_LOCAL_MACHINE = "HKLM"
    KEY_READ = 1
    KEY_WRITE = 2

    REG_SZ = 1
    REG_DWORD = 2
    REG_QWORD = 3
    REG_BINARY = 4
    REG_MULTI_SZ = 5
    REG_EXPAND_SZ = 6

    def __init__(self) -> None:
        self._store: dict[tuple[str, str], dict[str, tuple[object, int]]] = {}

    def OpenKey(self, hive, key_path, _reserved=0, _mode=KEY_READ):
        if (hive, key_path) not in self._store:
            raise OSError("key not found")
        return _Key(self, hive, key_path)

    def CreateKeyEx(self, hive, key_path, _reserved=0, _mode=KEY_WRITE):
        self._store.setdefault((hive, key_path), {})
        return _Key(self, hive, key_path)

    def QueryValueEx(self, key: _Key, value_name: str):
        values = self._store.get((key.hive, key.key_path), {})
        if value_name not in values:
            raise OSError("value not found")
        return values[value_name]

    def SetValueEx(self, key: _Key, value_name: str, _reserved: int, reg_type: int, value):
        self._store.setdefault((key.hive, key.key_path), {})[value_name] = (value, reg_type)

    def DeleteValue(self, key: _Key, value_name: str):
        values = self._store.get((key.hive, key.key_path), {})
        if value_name not in values:
            raise OSError("value not found")
        del values[value_name]

    def DeleteKey(self, hive, key_path):
        if (hive, key_path) not in self._store:
            raise OSError("key not found")
        del self._store[(hive, key_path)]
