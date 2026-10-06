import logging, re, zipfile
from datetime import datetime
from docx import Document
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from .. import models
from .storage_service import storage

ORGS = {"acm": ("Faculty Coordinator", "Secretary"), "nss": ("Programme Officer", "Secretary"),
        "ieee": ("Faculty Advisor", "Chair"), "csi": ("Faculty Coordinator", "Secretary")}
REQUIRED_TAGS = ["signature_left_name", "signature_right_name", "subject", "body"]

def ensure_columns(engine):
    """Tiny in-place migration so existing dev DBs gain new columns (Alembic replaces this later)."""
    insp = inspect(engine)
    want = {"templates": {"description": "VARCHAR(300)", "preview_image": "VARCHAR(300)", "signature_slots": "INTEGER DEFAULT 2",
                          "default_left_role": "VARCHAR(120)", "default_right_role": "VARCHAR(120)", "updated_at": "DATETIME"},
            "letters": {"salutation": "VARCHAR(40) DEFAULT 'Respected Sir'", "font_size": "INTEGER DEFAULT 11", "font_name": "VARCHAR(40) DEFAULT 'Calibri'"}}
    with engine.begin() as c:
        for table, adds in want.items():
            cols = {x["name"] for x in insp.get_columns(table)}
            for n, t in adds.items():
                if n not in cols: c.execute(text(f"ALTER TABLE {table} ADD COLUMN {n} {t}"))

def is_v2(key: str) -> bool:
    try:
        with zipfile.ZipFile(storage.path(key)) as z:
            xml = "".join(z.read(n).decode("utf8", "ignore") for n in z.namelist() if n.endswith(".xml"))
        text_ = re.sub(r"<[^>]+>", "", xml)  # join text across runs, ignore XML
        return all(t in text_ for t in REQUIRED_TAGS)
    except Exception:
        return False

def tighten_margins(d, side: float = 0.75):
    """Narrower side margins; scales the header letterhead image so it still spans the text width."""
    from docx.shared import Inches
    for sec in d.sections:
        old = sec.page_width - sec.left_margin - sec.right_margin
        sec.left_margin = sec.right_margin = Inches(side)
        k = (sec.page_width - sec.left_margin - sec.right_margin) / old
        for el in sec.header._element.xpath(".//wp:extent | .//a:ext"):
            if el.get("cx"): el.set("cx", str(int(int(el.get("cx")) * k))); el.set("cy", str(int(int(el.get("cy")) * k)))

def fill_template_body(d):
    """Writes the letter layout into an open Document: body (From, Through, To, Date, Subject,
    salutation, body, Thank You) and a FIXED 3-slot signature table in the page FOOTER.
    The header/letterhead, margins and styles of the document are left untouched."""
    from docx.shared import Inches, Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_ROW_HEIGHT_RULE
    for p in list(d.paragraphs): p._element.getparent().remove(p._element)
    def P(text, bold=False, align=None, after=8):
        p = d.add_paragraph(); p.add_run(text).bold = bold
        p.paragraph_format.space_after = Pt(after)
        if align is not None: p.alignment = align
    P("From:\n{{ from_name }}\n{{ from_position }}\n{{ from_organization }}")
    P("{%p if has_through %}", after=0); P("Through:\n{{ through_name }}\n{{ through_position }}\n{{ through_organization }}"); P("{%p endif %}", after=0)
    P("To:\n{{ to_name }}\n{{ to_position }}\n{{ to_organization }}", after=10)
    P("Date: {{ date }}", after=10)
    P("Subject: {{ subject }}", bold=True, after=10)
    P("{{ salutation }},", after=6)
    P("{%p for para in body_paragraphs %}", after=0)
    P("{{ para }}", align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=8)
    P("{%p endfor %}", after=0)
    P("Thank You.", after=0)
    t = d.sections[0].footer.add_table(rows=4, cols=3, width=Inches(6.77))
    for i, field in enumerate(("image", "name", "position", "organization")):
        for c, side in enumerate(("left", "center", "right")):
            par = t.cell(i, c).paragraphs[0]; par.paragraph_format.space_after = Pt(0)
            run = par.add_run("{{ signature_%s_%s }}" % (side, field)); run.bold = (field == "name")
    t.rows[0].height = Inches(0.8); t.rows[0].height_rule = WD_ROW_HEIGHT_RULE.AT_LEAST

def build_placeholder(path: str, title: str):
    """Placeholder letterhead for clubs without an official .docx yet."""
    d = Document()
    h = d.sections[0].header.paragraphs[0]; h.text = title; h.alignment = 1
    fill_template_body(d); tighten_margins(d); d.save(path)

def _has_header_image(path) -> bool:
    """True if the .docx header references an image (i.e. a real letterhead, not a text-only placeholder)."""
    try:
        with zipfile.ZipFile(path) as z:
            return any(re.match(r"word/_rels/header\d*\.xml\.rels$", n) and b"media/" in z.read(n) for n in z.namelist())
    except Exception:
        return False

def copy_default_templates():
    """First start with an empty /data volume: copy the official templates shipped inside the image.
    Existing files are never overwritten."""
    import shutil
    from pathlib import Path
    src = Path(__file__).resolve().parents[2] / "storage" / "templates"
    dst = Path(storage.path("templates"))
    if src.is_dir() and src.resolve() != dst.resolve():
        for f in src.glob("*.docx"):
            d = dst / f.name
            # copy when missing, or upgrade a placeholder (no header image) to the shipped letterhead that has one
            if not d.exists() or (_has_header_image(f) and not _has_header_image(d)): shutil.copy2(f, d)

def seed(db: Session):
    copy_default_templates()
    for org, (left, right) in ORGS.items():
        name, key = f"{org.upper()} Letterhead", f"templates/{org}.docx"
        row = db.query(models.Template).filter_by(name=name).first()
        import os
        os.makedirs(os.path.dirname(storage.path(key)), exist_ok=True)
        if not os.path.exists(storage.path(key)):
            build_placeholder(storage.path(key), name)  # only ever create; never overwrite a user's template
        elif not is_v2(key):
            logging.getLogger("uvicorn.error").warning("%s may be missing placeholders (subject/body/signature_*); check it in Word.", key)
        if not row:
            row = models.Template(name=name, file_path=key); db.add(row)
        row.signature_slots = 3
        row.default_left_role = row.default_left_role or left
        row.default_right_role = row.default_right_role or right
        row.description = row.description or f"{name} (placeholder – replace with official .docx)"
        row.updated_at = datetime.utcnow()
    db.commit()

def get_or_404(db: Session, tid: int) -> models.Template:
    t = db.get(models.Template, tid)
    if not t or not __import__("os").path.exists(storage.path(t.file_path)): raise LookupError("Template not found")
    return t

def validate_upload(data: bytes):
    """Reject uploads missing the required placeholders so a bad template fails early."""
    import io
    try: xml = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile: raise ValueError("Not a valid .docx file")
    if "word/document.xml" not in xml.namelist(): raise ValueError("Not a valid .docx file")
    text_ = "".join(xml.read(n).decode("utf8", "ignore") for n in xml.namelist() if n.endswith(".xml"))
    missing = [t for t in ("subject", "body") if t not in text_]
    if missing: raise ValueError(f"Template is missing placeholders: {missing}")


def letterhead_image(key: str) -> bytes | None:
    """First image referenced by the template's header (the letterhead), or None."""
    try:
        with zipfile.ZipFile(storage.path(key)) as z:
            for rel in sorted(n for n in z.namelist() if re.match(r"word/_rels/header\d*\.xml\.rels$", n)):
                for target in re.findall(r'Target="(media/[^"]+)"', z.read(rel).decode("utf8")):
                    return z.read("word/" + target)
    except Exception:
        pass
    return None
