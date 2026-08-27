import os
import io
from typing import List, Dict, Any

class DocumentProcessor:
    @staticmethod
    def process_file(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        """
        Parses PDF, DOCX, or TXT file bytes into structured page/section records.
        Returns a list of dicts: [{"text": str, "page": int, "section": str, "source": str}]
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            return DocumentProcessor._process_pdf(file_content, filename)
        elif ext in [".docx", ".doc"]:
            return DocumentProcessor._process_docx(file_content, filename)
        elif ext == ".txt":
            return DocumentProcessor._process_txt(file_content, filename)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats are PDF, DOCX, TXT.")

    @staticmethod
    def _process_pdf(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        records = []
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_content))
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    records.append({
                        "text": text,
                        "page": page_num,
                        "section": f"Page {page_num}",
                        "source": filename
                    })
        except Exception as e:
            print(f"[DocumentProcessor] PyPDF error for {filename}: {e}")
            # Fallback text extraction if pdf is raw text or corrupted
            text_attempt = file_content.decode("utf-8", errors="ignore").strip()
            if text_attempt:
                records.append({
                    "text": text_attempt[:5000],
                    "page": 1,
                    "section": "Extracted Text",
                    "source": filename
                })
        return records

    @staticmethod
    def _process_docx(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        records = []
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_content))
            current_section = "Document Content"
            section_text = []
            
            for para in doc.paragraphs:
                p_text = para.text.strip()
                if not p_text:
                    continue
                if para.style.name.startswith("Heading"):
                    if section_text:
                        records.append({
                            "text": "\n".join(section_text),
                            "page": 1,
                            "section": current_section,
                            "source": filename
                        })
                        section_text = []
                    current_section = p_text
                else:
                    section_text.append(p_text)
                    
            if section_text:
                records.append({
                    "text": "\n".join(section_text),
                    "page": 1,
                    "section": current_section,
                    "source": filename
                })
        except Exception as e:
            print(f"[DocumentProcessor] Docx error for {filename}: {e}")
            text_attempt = file_content.decode("utf-8", errors="ignore").strip()
            if text_attempt:
                records.append({
                    "text": text_attempt[:5000],
                    "page": 1,
                    "section": "Raw Text",
                    "source": filename
                })
        return records

    @staticmethod
    def _process_txt(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
        text = file_content.decode("utf-8", errors="ignore").strip()
        if not text:
            return []
        
        # Split into reasonable section blocks (e.g. double newlines)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        records = []
        for idx, p in enumerate(paragraphs, start=1):
            records.append({
                "text": p,
                "page": 1,
                "section": f"Paragraph {idx}",
                "source": filename
            })
        return records
