from pathlib import Path
from datetime import datetime
import json
import re

BASE = Path(__file__).resolve().parent / "templates"
BASE.mkdir(exist_ok=True)

class TemplateStore:
    def list(self):
        out = []
        for path in BASE.glob("*.json"):
            try:
                item = json.loads(path.read_text(encoding="utf-8"))
                item["_file_name"] = path.name
                out.append(item)
            except Exception:
                pass
        return sorted(out, key=lambda x: x.get("created_at", ""))

    def _safe_name(self, name: str) -> str:
        safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", name).strip("_")
        return safe or "template"

    def save(self, name, plan, sql):
        safe = self._safe_name(name)
        payload = {
            "template_name": name,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "plan": plan,
            "sql": sql,
        }
        path = BASE / f"{safe}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def delete(self, file_name: str) -> bool:
        path = BASE / Path(file_name).name
        if not path.exists():
            return False
        path.unlink()
        return True

    def rename(self, file_name: str, new_name: str):
        old = BASE / Path(file_name).name
        if not old.exists():
            raise FileNotFoundError(old)

        payload = json.loads(old.read_text(encoding="utf-8"))
        payload["template_name"] = new_name

        new = BASE / f"{self._safe_name(new_name)}.json"
        new.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        if new.resolve() != old.resolve():
            old.unlink()

        return new
