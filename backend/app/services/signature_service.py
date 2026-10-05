import io, uuid
from PIL import Image
from .storage_service import storage

ALLOWED = {"PNG": "png", "JPEG": "jpg"}

def save_signature(data: bytes) -> str:
    """Validate (PNG/JPG/JPEG), downscale to <=600px wide, store, return key."""
    try: img = Image.open(io.BytesIO(data)); fmt = img.format
    except Exception: raise ValueError("Signature must be a valid PNG or JPG image")
    if fmt not in ALLOWED: raise ValueError("Signature must be PNG or JPG")
    if img.width > 600: img = img.resize((600, int(img.height * 600 / img.width)))
    buf = io.BytesIO(); img.save(buf, format=fmt)
    return storage.save(f"signatures/{uuid.uuid4().hex}.{ALLOWED[fmt]}", buf.getvalue())

def delete_signature(key: str | None):
    if key: storage.delete(key)
