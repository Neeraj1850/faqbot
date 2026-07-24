import pdfplumber
from io import BytesIO

def parse_pdf_qa(pdf_bytes: bytes):
    faq_pairs = []
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    blocks = text.split("Q:")
    current_section = "General"

    for block in blocks[1:]:
        lines = block.strip().split("\n")
        question = lines[0].strip()
        answer_lines = []
        for line in lines[1:]:
            if line.startswith("Section:"):
                current_section = line.replace("Section:", "").strip()
            else:
                answer_lines.append(line)
        answer = " ".join(answer_lines).strip()

        faq_pairs.append({
            "section": current_section,
            "question": question,
            "answer": answer
        })
    return faq_pairs
