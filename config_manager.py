import os
import json
import time
import uuid
from typing import List, Optional, Callable
from cryptography.fernet import Fernet

class APIConfig:
    def __init__(self, id: Optional[str]=None, name: str="", url: str="", api_key_enc: str="", model: str="", timeout: int=30, group: str="default", note: str="", prompt: str="", system_prompt: str="", api_base: str="", api_path: str="/v1/chat/completions", mode: str="openai"):
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.url = url
        self.api_key_enc = api_key_enc
        self.model = model
        self.timeout = timeout
        self.group = group
        self.note = note
        self.prompt = prompt
        self.system_prompt = system_prompt
        self.api_base = api_base
        self.api_path = api_path
        self.mode = mode

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "api_key": self.api_key_enc,
            "model": self.model,
            "timeout": self.timeout,
            "group": self.group,
            "note": self.note,
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "api_base": self.api_base,
            "api_path": self.api_path,
            "mode": self.mode,
        }

    @staticmethod
    def from_dict(d):
        return APIConfig(
            id=d.get("id"),
            name=d.get("name", ""),
            url=d.get("url", ""),
            api_key_enc=d.get("api_key", ""),
            model=d.get("model", ""),
            timeout=int(d.get("timeout", 30)),
            group=d.get("group", "default"),
            note=d.get("note", ""),
            prompt=d.get("prompt", ""),
            system_prompt=d.get("system_prompt", ""),
            api_base=d.get("api_base", d.get("url", "")),
            api_path=d.get("api_path", "/v1/chat/completions"),
            mode=d.get("mode", "openai"),
        )

class ConfigManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.config_path = os.path.join(base_dir, "configs", "api_configs.json")
        self.key_path = os.path.join(base_dir, "configs", "secret.key")
        self.audit_path = os.path.join(base_dir, "configs", "audit.log")
        self.admin_path = os.path.join(base_dir, "configs", "admin.hash")
        self._ensure_dirs()
        self._fernet = self._load_fernet()
        self.configs: List[APIConfig] = []
        self.selected_id: Optional[str] = None
        self.role = "viewer"
        self.listeners: List[Callable] = []
        self._load_configs()

    def _ensure_dirs(self):
        d = os.path.join(self.base_dir, "configs")
        if not os.path.isdir(d):
            os.makedirs(d, exist_ok=True)

    def _load_fernet(self):
        if not os.path.isfile(self.key_path):
            key = Fernet.generate_key()
            with open(self.key_path, "wb") as f:
                f.write(key)
        with open(self.key_path, "rb") as f:
            key = f.read()
        return Fernet(key)

    def _load_configs(self):
        if not os.path.isfile(self.config_path):
            self._save_configs()
        try:
            j = json.load(open(self.config_path, "r", encoding="utf-8"))
            self.configs = [APIConfig.from_dict(x) for x in j.get("items", [])]
            self.selected_id = j.get("selected_id")
        except Exception:
            self.configs = []
            self.selected_id = None
        if not self.configs:
            url = os.getenv("OCR_API_ENDPOINT", "http://localhost:1234")
            model = os.getenv("OCR_API_MODEL", "qwen/qwen3-vl-8b")
            timeout = int(os.getenv("OCR_TIMEOUT", "30"))
            key = os.getenv("OCR_API_KEY", "")
            enc = self.encrypt_key(key)
            prompt = os.getenv("OCR_PROMPT", "只返回图片中的可读字幕文本")
            system_prompt = os.getenv("OCR_SYSTEM_PROMPT", "")
            cfg = APIConfig(name="LM Studio Qwen-VL", url=url, api_key_enc=enc, model=model, timeout=timeout, group="local", note="默认本地LM配置", prompt=prompt, system_prompt=system_prompt, api_base=url, api_path="/v1/chat/completions", mode="openai")
            self.configs.append(cfg)
            self.selected_id = cfg.id
            self._save_configs()
            self._audit("default_init", cfg.to_dict())
            self._notify()

    def _save_configs(self):
        data = {"items": [c.to_dict() for c in self.configs], "selected_id": self.selected_id}
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _audit(self, action: str, payload: dict):
        rec = {"ts": int(time.time()*1000), "role": self.role, "action": action, "payload": payload}
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def register_listener(self, fn: Callable):
        self.listeners.append(fn)

    def _notify(self):
        for fn in self.listeners:
            try:
                fn()
            except Exception:
                pass

    def encrypt_key(self, key_plain: str) -> str:
        if not key_plain:
            return ""
        return self._fernet.encrypt(key_plain.encode("utf-8")).decode("ascii")

    def decrypt_key(self, key_enc: str) -> str:
        if not key_enc:
            return ""
        try:
            return self._fernet.decrypt(key_enc.encode("ascii")).decode("utf-8")
        except Exception:
            return ""

    def list_configs(self) -> List[APIConfig]:
        return list(self.configs)

    def search(self, text: str) -> List[APIConfig]:
        t = text.lower().strip()
        if not t:
            return list(self.configs)
        r = []
        for c in self.configs:
            s = " ".join([c.name, c.model, c.url, c.group, c.note]).lower()
            if t in s:
                r.append(c)
        return r

    def add_config(self, cfg: APIConfig):
        self.configs.append(cfg)
        self._save_configs()
        self._audit("add", cfg.to_dict())
        self._notify()

    def update_config(self, cfg: APIConfig):
        for i, c in enumerate(self.configs):
            if c.id == cfg.id:
                self.configs[i] = cfg
                break
        self._save_configs()
        self._audit("update", cfg.to_dict())
        self._notify()

    def delete_config(self, id: str):
        self.configs = [c for c in self.configs if c.id != id]
        if self.selected_id == id:
            self.selected_id = None
        self._save_configs()
        self._audit("delete", {"id": id})
        self._notify()

    def select(self, id: Optional[str]):
        self.selected_id = id
        self._save_configs()
        self._audit("select", {"id": id})
        self._notify()

    def get_selected(self) -> Optional[APIConfig]:
        if not self.selected_id:
            return None
        for c in self.configs:
            if c.id == self.selected_id:
                return c
        return None

    def export_configs(self, path: str):
        data = {"items": [c.to_dict() for c in self.configs], "selected_id": self.selected_id}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._audit("export", {"path": path})

    def import_configs(self, path: str):
        j = json.load(open(path, "r", encoding="utf-8"))
        self.configs = [APIConfig.from_dict(x) for x in j.get("items", [])]
        self.selected_id = j.get("selected_id")
        self._save_configs()
        self._audit("import", {"path": path})
        self._notify()
