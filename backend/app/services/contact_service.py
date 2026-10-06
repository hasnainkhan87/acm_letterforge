import json
from pathlib import Path
from sqlalchemy.orm import Session
from .. import models

HODS_FILE = Path(__file__).resolve().parent.parent / "data" / "hods.json"
ORG = "NMAMIT,nitte"

def seed_hods(db: Session):
    """Upserts one HOD contact per department from data/hods.json.
    A department is identified by its position line, so changing a name in the file updates that
    contact instead of adding a duplicate. Contacts you add yourself are never touched."""
    for h in json.loads(HODS_FILE.read_text(encoding="utf8")):
        position = f"Head Of Department,{h['dept']}"
        row = db.query(models.Contact).filter_by(position=position, organization=ORG).first()
        if row: row.name = h["name"]
        else: db.add(models.Contact(name=h["name"], position=position, organization=ORG))
    db.commit()
