"""隔离旧技能的同名模块；复用原文件，不复制 Actor 或机器人资产。"""
from contextlib import contextmanager
import importlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]


class Plugin:
    def __init__(self, name, modules):
        self.path = ROOT / name
        self.names = {p.stem for p in self.path.glob('*.py')}
        self.names |= {p.name for p in self.path.iterdir() if (p/'__init__.py').exists()}
        self.cache = {}
        with self.active():
            self.modules = {name: importlib.import_module(name) for name in modules}

    @contextmanager
    def active(self):
        def local(name):
            return name.split('.')[0] in self.names
        saved = {k: v for k, v in list(sys.modules.items()) if local(k)}
        for k in saved:
            del sys.modules[k]
        sys.modules.update(self.cache)
        old_path = sys.path[:]
        sys.path.insert(0, str(self.path))
        try:
            yield
        finally:
            self.cache = {k: v for k, v in list(sys.modules.items()) if local(k)}
            for k in self.cache:
                del sys.modules[k]
            sys.modules.update(saved)
            sys.path[:] = old_path

    def __getitem__(self, name):
        return self.modules[name]
