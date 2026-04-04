
import os
import django
import pandas as pd
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mdh_intranet.settings')
django.setup()

from mdh_intranet.icd11_tools.models import ICDCode

FILE_PATH = r"c:\Users\HomePC\mdh_intranet\media\documents\2026\02\SimpleTabulation-ICD-11-MMS-en.xlsx"

def import_data():
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return

    print("Reading Excel file...")
    try:
        df = pd.read_excel(FILE_PATH)
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("Columns found:", df.columns.tolist())
    
    # Normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    
    # Map columns
    col_code = next((c for c in df.columns if 'code' in c), None)
    col_title = next((c for c in df.columns if 'title' in c or 'description' in c), None)
    col_block = next((c for c in df.columns if 'block' in c), None)
    col_chapter = next((c for c in df.columns if 'chapter' in c or 'classkind' in c), None) # Fallback?

    if not col_code or not col_title:
        print("Could not identify 'Code' and 'Title' columns.")
        return

    print(f"Using columns - Code: {col_code}, Title: {col_title}, Block: {col_block}, Chapter: {col_chapter}")

    # Clear existing?
    print("Clearing existing codes...")
    ICDCode.objects.all().delete()

    print("Importing codes...")
    codes_to_create = []
    
    # Iterate
    count = 0 
    for index, row in df.iterrows():
        code_val = str(row[col_code]).strip()
        if not code_val or code_val.lower() == 'nan' or code_val == '-':
            continue
            
        title_val = str(row[col_title]).strip()
        
        block_val = ""
        if col_block:
            block_val = str(row[col_block]).strip()
            if block_val.lower() == 'nan': block_val = ""
            
        chapter_val = "Unknown"
        if col_chapter:
             chapter_val = str(row[col_chapter]).strip()
        # Try to infer chapter from block or code if missing?
        # For simple tabulation, often the first few chars or a 'ChapterNo' column exists.
        # If 'BlockId' is usually like 'BlockL1-...'
        
        codes_to_create.append(
            ICDCode(
                code=code_val,
                description=title_val,
                chapter=chapter_val,
                block=block_val
            )
        )
        
        if len(codes_to_create) >= 1000:
            ICDCode.objects.bulk_create(codes_to_create, ignore_conflicts=True)
            count += len(codes_to_create)
            codes_to_create = []
            print(f"Imported {count} codes...")

    if codes_to_create:
        ICDCode.objects.bulk_create(codes_to_create, ignore_conflicts=True)
        count += len(codes_to_create)

    print(f"Total imported: {count}")

if __name__ == "__main__":
    import_data()
