import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import PlatformDirs


@dataclass(frozen=True)
class AppPaths:
    config_dir: Path
    data_dir: Path
    state_dir: Path
    runtime_dir: Path

    @property
    def config_file(self) -> Path: return self.config_dir / "config.toml"
    @property
    def pid_file(self) -> Path: return self.runtime_dir / "hi-puter.pid"
    @property
    def lock_file(self) -> Path: return self.runtime_dir / "hi-puter.lock"
    @property
    def log_file(self) -> Path: return self.state_dir / "hi-puter.log"

    def ensure(self) -> None:
        for path in (self.config_dir, self.data_dir, self.state_dir, self.runtime_dir):
            path.mkdir(parents=True, exist_ok=True, mode=0o700)
            try: os.chmod(path, 0o700)
            except OSError: pass


def get_paths() -> AppPaths:
    dirs = PlatformDirs("hi-puter", "Hi-Puter")
    runtime = Path(dirs.user_runtime_dir) if dirs.user_runtime_dir else Path(dirs.user_state_dir)
    return AppPaths(Path(dirs.user_config_dir), Path(dirs.user_data_dir), Path(dirs.user_state_dir), runtime)
