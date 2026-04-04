import openpyxl
import logging
from django.db import transaction
from .models import ICDCode
from mdh_intranet.documents.models import Document

logger = logging.getLogger(__name__)

def index_icd_document(document_id):
    """
    Parse an Excel document and index its contents into ICDCode model.
    Expected format (Simple Tabulation):
    Column A: ICD-11 Code
    Column B: Description / Title
    Column C: Chapter (Optional)
    """
    try:
        doc_record = Document.objects.get(pk=document_id)
        if not doc_record.file.name.endswith(('.xlsx', '.xls')):
            return False, "Unsupported file format. Please upload an Excel file."

        # Load workbook
        wb = openpyxl.load_workbook(doc_record.file.path, read_only=True, data_only=True)
        sheet = wb.active
        
        codes_to_create = []
        codes_to_update = []
        existing_codes = {c.code: c for c in ICDCode.objects.all()}
        
        count = 0
        # Iterate rows (skip header if it looks like one)
        for row in sheet.iter_rows(min_row=1, values_only=True):
            if not any(row):
                continue
               
            code_val = str(row[0]).strip() if row[0] else None
            desc_val = str(row[1]).strip() if row[1] else ""
            
            # Skip header or invalid codes
            if not code_val or code_val.lower() in ['code', 'icd', 'icd-11']:
                continue
                
            chapter_val = str(row[2]).strip() if len(row) > 2 and row[2] else ""
            
            if code_val in existing_codes:
                # Update if changed
                obj = existing_codes[code_val]
                if obj.description != desc_val or obj.chapter != chapter_val:
                    obj.description = desc_val
                    obj.chapter = chapter_val
                    codes_to_update.append(obj)
            else:
                codes_to_create.append(ICDCode(
                    code=code_val,
                    description=desc_val,
                    chapter=chapter_val
                ))
            
            count += 1
            if count > 20000: # Safety cap for very large files
                break

        # Execute DB changes in transaction
        with transaction.atomic():
            if codes_to_create:
                ICDCode.objects.bulk_create(codes_to_create, batch_size=1000)
            if codes_to_update:
                ICDCode.objects.bulk_update(codes_to_update, ['description', 'chapter'], batch_size=1000)

        return True, f"Successfully indexed {len(codes_to_create)} new codes and updated {len(codes_to_update)} existing codes."

    except Exception as e:
        logger.error(f"Error indexing ICD document: {e}")
        return False, f"Error during indexing: {str(e)}"
