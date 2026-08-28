from pathlib import Path
from datetime import datetime
import json, re
BASE = Path(__file__).resolve().parent / "templates"
BASE.mkdir(exist_ok=True)
class TemplateStore:
    def list(self):
        items=[]
        for p in BASE.glob("*.json"):
            try: items.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception: pass
        return sorted(items,key=lambda x:x.get("created_at",""))
    def save(self,name,plan,sql):
        safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+","_",name).strip("_") or "template"
        payload={"template_name":name,"created_at":datetime.now().isoformat(timespec="seconds"),"plan":plan,"sql":sql}
        path=BASE/f"{safe}.json"
        path.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
        return path
