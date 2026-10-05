import uuid
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas
from .services import ai_service as ai, document_service, template_service, signature_service
from .db import Base, engine, get_db, SessionLocal
from .services.storage_service import storage

app = FastAPI(title="LetterForge")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
def startup():
    # Dev convenience; use `alembic upgrade head` in production.
    Base.metadata.create_all(engine)
    template_service.ensure_columns(engine)
    with SessionLocal() as db:
        template_service.seed(db)
        if not db.query(models.Contact).count():  # starter saved details
            db.add_all([models.Contact(name="Pratheeksha", position="Chairperson", organization="ACM,NMAMIT"),
                        models.Contact(name="Mr Krishnaraj Rao", position="Faculty Coordinator", organization="ACM,NMAMIT")])
            db.commit()

# ---- Templates (upload route = hook for future custom/OCR templates)
@app.get("/api/templates", response_model=list[schemas.TemplateOut])
def list_templates(db: Session = Depends(get_db)):
    return db.query(models.Template).all()

@app.post("/api/templates", response_model=schemas.TemplateOut)
async def upload_template(name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    data = await file.read()
    try: template_service.validate_upload(data)
    except Exception as e: raise HTTPException(400, str(e))
    key = storage.save(f"templates/{uuid.uuid4().hex}.docx", data)
    t = models.Template(name=name, file_path=key); db.add(t); db.commit(); db.refresh(t); return t

# ---- Signatories
@app.get("/api/signatories", response_model=list[schemas.SignatoryOut])
def list_sigs(db: Session = Depends(get_db)):
    return db.query(models.Signatory).order_by(models.Signatory.sort_order).all()

async def _save_sig(s: models.Signatory, image: UploadFile | None):
    if image:
        try: new = signature_service.save_signature(await image.read())
        except ValueError as e: raise HTTPException(400, str(e))
        signature_service.delete_signature(s.signature_path); s.signature_path = new

@app.post("/api/signatories", response_model=schemas.SignatoryOut)
async def add_sig(name: str = Form(...), position: str = Form(...), organization: str = Form(...),
                  image: UploadFile | None = File(None), db: Session = Depends(get_db)):
    s = models.Signatory(name=name, position=position, organization=organization,
                         sort_order=db.query(models.Signatory).count())
    await _save_sig(s, image); db.add(s); db.commit(); db.refresh(s); return s

@app.put("/api/signatories/reorder")
def reorder(body: schemas.ReorderIn, db: Session = Depends(get_db)):
    for i, sid in enumerate(body.ids):
        s = db.get(models.Signatory, sid)
        if s: s.sort_order = i
    db.commit(); return {"ok": True}

@app.put("/api/signatories/{sid}", response_model=schemas.SignatoryOut)
async def edit_sig(sid: int, name: str = Form(...), position: str = Form(...), organization: str = Form(...),
                   image: UploadFile | None = File(None), db: Session = Depends(get_db)):
    s = db.get(models.Signatory, sid)
    if not s: raise HTTPException(404)
    s.name, s.position, s.organization = name, position, organization
    await _save_sig(s, image); db.commit(); db.refresh(s); return s

@app.delete("/api/signatories/{sid}")
def del_sig(sid: int, db: Session = Depends(get_db)):
    s = db.get(models.Signatory, sid)
    if not s: raise HTTPException(404)
    signature_service.delete_signature(s.signature_path); db.delete(s); db.commit(); return {"ok": True}

# ---- AI + letters
@app.post("/api/generate", response_model=schemas.GenerateOut)
async def generate(body: schemas.GenerateIn):
    try: return await ai.generate(body.prompt, body.style)
    except Exception as e: raise HTTPException(502, f"AI generation failed: {e}")

@app.post("/api/letters", response_model=schemas.LetterOut)
def save_letter(body: schemas.LetterIn, db: Session = Depends(get_db)):
    if not db.get(models.Template, body.template_id): raise HTTPException(404, "Template not found")
    l = models.Letter(**body.model_dump()); db.add(l); db.commit(); db.refresh(l); return l

@app.get("/api/letters", response_model=list[schemas.LetterOut])
def list_letters(db: Session = Depends(get_db)):
    return db.query(models.Letter).order_by(models.Letter.created_at.desc()).all()

@app.get("/api/letters/{lid}/export")
def export(lid: int, format: str = "pdf", db: Session = Depends(get_db)):
    l = db.get(models.Letter, lid)
    if not l: raise HTTPException(404)
    try: t = template_service.get_or_404(db, l.template_id)
    except LookupError: raise HTTPException(404, "Template file missing")
    sigs = [s for i in l.signatory_ids if (s := db.get(models.Signatory, i))]
    if format == "docx":
        return Response(document_service.render_docx(l, t, sigs), headers={"Content-Disposition": f"attachment; filename=letter_{lid}.docx"},
                        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    pdf, exact = document_service.render_pdf(l, t, sigs)
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": f"attachment; filename=letter_{lid}.pdf", "X-PDF-Fidelity": "exact" if exact else "basic",
        "Access-Control-Expose-Headers": "X-PDF-Fidelity"})

# ---- Serve stored files (signature images for the preview)
from pathlib import Path
from fastapi.responses import FileResponse
from .config import settings

@app.get("/api/files/{key:path}")
def get_file(key: str):
    root = Path(settings.storage_dir).resolve(); p = (root / key).resolve()
    if root not in p.parents or not p.is_file(): raise HTTPException(404)
    return FileResponse(p)


# ---- Live preview: the REAL template rendered to PDF (same pipeline as export)
from types import SimpleNamespace

@app.post("/api/preview")
def preview(body: schemas.LetterIn, db: Session = Depends(get_db)):
    try: t = template_service.get_or_404(db, body.template_id)
    except LookupError: raise HTTPException(404, "Template file missing")
    sigs = [s for i in body.signatory_ids if (s := db.get(models.Signatory, i))]
    letter = SimpleNamespace(**body.model_dump(), created_at=None)
    pdf, exact = document_service.render_pdf(letter, t, sigs)
    return Response(pdf, media_type="application/pdf", headers={
        "Content-Disposition": "inline", "X-PDF-Fidelity": "exact" if exact else "basic",
        "Access-Control-Expose-Headers": "X-PDF-Fidelity"})


# ---- Letterhead image straight from the template's header (works without LibreOffice/Word)
import re, zipfile

@app.get("/api/templates/{tid}/letterhead")
def letterhead(tid: int, db: Session = Depends(get_db)):
    t = db.get(models.Template, tid)
    if not t: raise HTTPException(404, "Template not found")
    try:
        with zipfile.ZipFile(storage.path(t.file_path)) as z:
            for rel in sorted(n for n in z.namelist() if re.match(r"word/_rels/header\d*\.xml\.rels$", n)):
                for target in re.findall(r'Target="(media/[^"]+)"', z.read(rel).decode("utf8")):
                    ext = target.rsplit(".", 1)[-1].lower()
                    mt = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}.get(ext, "application/octet-stream")
                    return Response(z.read("word/" + target), media_type=mt)
    except Exception:
        pass
    raise HTTPException(404, "No letterhead image in template header")


# ---- Saved contacts (autofill for From / Through / To)
@app.get("/api/contacts", response_model=list[schemas.ContactOut])
def list_contacts(db: Session = Depends(get_db)):
    return db.query(models.Contact).order_by(models.Contact.name).all()

@app.post("/api/contacts", response_model=schemas.ContactOut)
def add_contact(body: schemas.Party, db: Session = Depends(get_db)):
    c = db.query(models.Contact).filter_by(**body.model_dump()).first()  # no duplicates
    if not c:
        c = models.Contact(**body.model_dump()); db.add(c); db.commit(); db.refresh(c)
    return c

@app.delete("/api/contacts/{cid}")
def del_contact(cid: int, db: Session = Depends(get_db)):
    c = db.get(models.Contact, cid)
    if not c: raise HTTPException(404)
    db.delete(c); db.commit(); return {"ok": True}

# ---- Optional password (HTTP Basic) for when the app is hosted online
import base64, secrets

@app.middleware("http")
async def basic_auth(request, call_next):
    if settings.app_password:
        ok = False
        h = request.headers.get("authorization", "")
        if h.startswith("Basic "):
            try: ok = secrets.compare_digest(base64.b64decode(h[6:]).decode().partition(":")[2], settings.app_password)
            except Exception: pass
        if not ok: return Response(status_code=401, headers={"WWW-Authenticate": 'Basic realm="LetterForge"'})
    return await call_next(request)

# ---- Serve the built frontend (single-service hosting). Must stay LAST.
from fastapi.staticfiles import StaticFiles
WEB = Path("static")
if (WEB / "index.html").is_file():
    app.mount("/assets", StaticFiles(directory=WEB / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        f = (WEB / path).resolve()
        return FileResponse(f if path and f.is_file() and WEB.resolve() in f.parents else WEB / "index.html")
