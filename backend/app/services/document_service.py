import io, logging, os, shutil, subprocess, sys, tempfile
from datetime import date
from pathlib import Path
from docxtpl import DocxTemplate, InlineImage
from docx import Document
from docx.shared import Inches, Pt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from .storage_service import storage

def _ctx(letter, tpl: DocxTemplate, sigs) -> dict:
    """All content goes through placeholders. Two FIXED slots: left=1st signatory, right=2nd."""
    t = letter.through or {}
    ctx = {
        "date": (letter.created_at or date.today()).strftime("%d %B %Y").lstrip("0"),
        "from_name": letter.sender["name"], "from_position": letter.sender["position"], "from_organization": letter.sender["organization"],
        "has_through": bool(letter.through),
        "through_name": t.get("name", ""), "through_position": t.get("position", ""), "through_organization": t.get("organization", ""),
        "to_name": letter.recipient["name"], "to_position": letter.recipient["position"], "to_organization": letter.recipient["organization"],
        "subject": letter.subject, "body": letter.body, "salutation": getattr(letter, "salutation", "Respected Sir"),
        "body_paragraphs": [x.strip() for x in letter.body.split("\n\n") if x.strip()] or [letter.body],
    }
    # FIXED slots: 1 signatory -> left; 2 -> left+right; 3 -> left+center+right.
    order = {0: [], 1: ["left"], 2: ["left", "right"], 3: ["left", "center", "right"]}[min(len(sigs), 3)]
    by_side = dict(zip(order, sigs))
    for side in ("left", "center", "right"):
        s = by_side.get(side)
        img = ""  # missing image -> blank space, details still shown
        if s and s.signature_path and os.path.exists(storage.path(s.signature_path)):
            img = InlineImage(tpl, storage.path(s.signature_path), width=Inches(1.3))
        ctx.update({f"signature_{side}_image": img, f"signature_{side}_name": s.name if s else "",
                    f"signature_{side}_position": s.position if s else "", f"signature_{side}_organization": s.organization if s else ""})
    return ctx

def apply_font(docx: bytes, name: str, size: int) -> bytes:
    """Sets font + size on the letter body only. Header (letterhead) and footer (signatures) stay as designed."""
    d = Document(io.BytesIO(docx))
    for p in d.paragraphs:
        for r in p.runs:
            r.font.name = name; r.font.size = Pt(size)
    buf = io.BytesIO(); d.save(buf); return buf.getvalue()

def render_docx(letter, template, sigs) -> bytes:
    tpl = DocxTemplate(storage.path(template.file_path))
    tpl.render(_ctx(letter, tpl, sigs))
    buf = io.BytesIO(); tpl.save(buf); out = buf.getvalue()
    name, size = getattr(letter, "font_name", "Calibri"), getattr(letter, "font_size", 11)
    return out if (name, size) == ("Calibri", 11) else apply_font(out, name, size)  # default = template untouched

def _soffice() -> str | None:
    for c in (shutil.which("soffice"), shutil.which("libreoffice"), r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if c and os.path.exists(c): return c

def docx_to_pdf(docx: bytes) -> bytes | None:
    """DOCX -> PDF via LibreOffice (Linux/Docker path) or MS Word/docx2pdf on Windows dev machines.
    Returns None if conversion is unavailable or fails, so callers can fall back."""
    log = logging.getLogger("uvicorn.error")
    with tempfile.TemporaryDirectory(prefix="lf-") as d:  # unique per request, removed on success AND failure
        src, out = Path(d) / "letter.docx", Path(d) / "letter.pdf"; src.write_bytes(docx)
        exe = _soffice()
        try:
            if exe:
                profile = (Path(d) / "lo-profile").as_uri()  # private profile: no lock clashes between requests, works as non-root
                r = subprocess.run([exe, f"-env:UserInstallation={profile}", "--headless", "--norestore",
                                    "--convert-to", "pdf", "--outdir", d, str(src)], timeout=120, capture_output=True)
                if r.returncode != 0 or not out.exists():
                    raise RuntimeError(r.stderr.decode("utf8", "ignore")[-300:] or "soffice produced no output")
            elif sys.platform == "win32":
                import pythoncom; pythoncom.CoInitialize()
                from docx2pdf import convert; convert(str(src), str(out))
            else:
                raise RuntimeError("LibreOffice (soffice) not found on PATH")
            return out.read_bytes()
        except Exception as e:
            log.warning("PDF conversion unavailable (%s). Using basic fallback PDF.", e)
            return None

def basic_pdf(letter, template, sigs) -> bytes:
    """Fallback when no converter is installed: rebuilds the same layout with reportlab
    (letterhead image, date, From/Through/To, subject, justified body, 2-slot signature table).
    Close to the template but not guaranteed pixel-identical like the DOCX->PDF path."""
    from reportlab.lib.enums import TA_JUSTIFY
    from reportlab.lib.units import inch
    from reportlab.lib.utils import ImageReader
    from reportlab.platypus import Table, TableStyle
    from . import template_service
    fs = getattr(letter, "font_size", 11)
    fn = "Times-Roman" if getattr(letter, "font_name", "") == "Times New Roman" else "Helvetica"  # reportlab built-ins
    st = ParagraphStyle("b", parent=getSampleStyleSheet()["BodyText"], fontName=fn, fontSize=fs, leading=fs * 1.4, spaceAfter=8)
    just = ParagraphStyle("j", parent=st, alignment=TA_JUSTIFY)
    br = lambda x: x.replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br/>")
    blk = lambda label, x: Paragraph(f"{label}<br/>{br(x['name'])}<br/>{br(x['position'])}<br/>{br(x['organization'])}", st)
    W = 6.77 * inch
    el = []
    head = template_service.letterhead_image(template.file_path)
    if head:
        w, h = ImageReader(io.BytesIO(head)).getSize()
        el += [Image(io.BytesIO(head), width=W, height=W * h / w), Spacer(1, 14)]
    el.append(blk("From:", letter.sender))
    if letter.through: el.append(blk("Through:", letter.through))
    el += [blk("To:", letter.recipient), Paragraph(f"Date: {_ctx_date(letter)}", st),
           Paragraph(f"<b>Subject: {br(letter.subject)}</b>", st), Paragraph(f"{getattr(letter, 'salutation', 'Respected Sir')},", st)]
    for para in [x.strip() for x in letter.body.split("\n\n") if x.strip()]:
        el.append(Paragraph(br(para), just))
    el.append(Paragraph("Thank You.", st))
    order = {0: [], 1: [0], 2: [0, 2], 3: [0, 1, 2]}[min(len(sigs), 3)]
    slot = {pos: sigs[k] for k, pos in enumerate(order)}
    cells = [[], [], [], []]
    for pos in (0, 1, 2):
        s_ = slot.get(pos); img = ""
        if s_ and s_.signature_path and os.path.exists(storage.path(s_.signature_path)):
            img = Image(storage.path(s_.signature_path), width=1.3 * inch, height=0.7 * inch, kind="proportional", hAlign="LEFT")
        cells[0].append(img)
        cells[1].append(Paragraph(f"<b>{br(s_.name)}</b>" if s_ else "", st))
        cells[2].append(Paragraph(br(s_.position) if s_ else "", st))
        cells[3].append(Paragraph(br(s_.organization) if s_ else "", st))
    t = Table(cells, colWidths=[W / 3] * 3, rowHeights=[0.8 * inch, None, None, None], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("TOPPADDING", (0, 1), (-1, -1), 0), ("BOTTOMPADDING", (0, 1), (-1, -1), 0)]))
    _, th = t.wrap(W, 0)
    def footer(canvas, doc):  # signatures pinned to the bottom of every page, like the DOCX footer
        canvas.saveState(); t.wrapOn(canvas, W, th); t.drawOn(canvas, 0.75 * inch, 0.5 * inch); canvas.restoreState()
    b = io.BytesIO()
    SimpleDocTemplate(b, pagesize=A4, leftMargin=0.75 * inch, rightMargin=0.75 * inch, topMargin=0.6 * inch,
                      bottomMargin=0.5 * inch + th + 0.3 * inch).build(el, onFirstPage=footer, onLaterPages=footer)
    return b.getvalue()

def _ctx_date(letter) -> str:
    return (letter.created_at or date.today()).strftime("%d %B %Y").lstrip("0")

def render_pdf(letter, template, sigs) -> tuple[bytes, bool]:
    """Returns (pdf_bytes, exact). exact=False means the basic fallback was used."""
    pdf = docx_to_pdf(render_docx(letter, template, sigs))
    return (pdf, True) if pdf else (basic_pdf(letter, template, sigs), False)
