import os
import pyzipper
from tqdm import tqdm

# Paths
# base_dir = r"C:\Users\User\Documents\검수\20250828-김기양\1페이지-테이블 삽입4\29"
base_dir = input("경로를 입력해주세요.")
out_dir = os.path.join(base_dir, "extracted_pdfs")

# Ensure output directory exists
os.makedirs(out_dir, exist_ok=True)

# List all zip files
zip_files = [f for f in os.listdir(base_dir) if f.endswith('.zip')]

for zip_name in tqdm(zip_files, desc="Extracting PDFs"):
    zip_path = os.path.join(base_dir, zip_name)
    with pyzipper.AESZipFile(zip_path) as zf:
        for member in zf.namelist():
            # Only extract PDFs inside 'original/' folder
            if member.startswith('original/') and member.lower().endswith('.pdf'):
                # Output filename: zipname(without .zip) + _ + pdfname
                pdf_name = os.path.basename(member)
                out_pdf = os.path.join(out_dir, f"{pdf_name}")
                with zf.open(member) as source, open(out_pdf, 'wb') as target:
                    target.write(source.read())
print("PDF extraction complete.")
