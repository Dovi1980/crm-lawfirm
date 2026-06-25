"""Smoke tests for the DOCX/PDF exporters and the markdown parser."""
from app.services.document_export import parse_markdown, to_docx, to_pdf


SAMPLE = """# CARTA DOCUMENTO

**Remitente:** Estudio Jurídico
**Destinatario:** Juan Pérez

## I. Intimación

Por la presente lo intimo a que en el plazo de **48 horas hábiles** abone:

- La suma de $350.000 en concepto de honorarios
- Los intereses devengados desde el 12/03/2025

Bajo apercibimiento de iniciar las acciones legales.

Saluda atentamente,
*Dr. Letrado*
"""


def test_parser_distinguishes_block_kinds():
    blocks = parse_markdown(SAMPLE)
    kinds = [b.kind for b in blocks]
    assert "heading" in kinds
    assert "paragraph" in kinds
    assert "bullets" in kinds
    # First heading is level 1
    headings = [b for b in blocks if b.kind == "heading"]
    assert headings[0].level == 1
    # Bullets parsed
    bullet_block = next(b for b in blocks if b.kind == "bullets")
    assert len(bullet_block.items) == 2


def test_parser_parses_inline_bold_and_italic():
    blocks = parse_markdown("Hola **mundo** y *adios*")
    p = blocks[0]
    assert p.kind == "paragraph"
    types = {(r.text, r.bold, r.italic) for r in p.runs}
    assert ("mundo", True, False) in types
    assert ("adios", False, True) in types


def test_to_docx_produces_zip_envelope():
    data = to_docx(SAMPLE, "Carta documento")
    # DOCX files are ZIPs and start with the PK magic bytes
    assert data[:2] == b"PK"
    assert len(data) > 1000


def test_to_pdf_produces_pdf_envelope():
    data = to_pdf(SAMPLE, "Carta documento")
    assert data.startswith(b"%PDF-")
    assert len(data) > 500
