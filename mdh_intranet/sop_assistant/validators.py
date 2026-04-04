"""
SOP Validation Engine
===========================
Validates SOP drafts against OpsHub formatting rules, required section checks,
and ICD-11 terminology compliance.
"""

import re
from django.utils import timezone


# ─── Formatting Rules ───────────────────────────────────────
MDH_RULES = [
    {
        'code': 'MDH-FMT-001',
        'name': 'Title Required',
        'description': 'SOP must have a descriptive title',
        'check': 'check_title',
    },
    {
        'code': 'MDH-FMT-002',
        'name': 'Title Length',
        'description': 'Title should be between 10 and 150 characters',
        'check': 'check_title_length',
    },
    {
        'code': 'MDH-FMT-003',
        'name': 'Version Format',
        'description': 'Version must follow semantic format (e.g. 1.0, 2.1)',
        'check': 'check_version_format',
    },
    {
        'code': 'MDH-FMT-004',
        'name': 'Required Sections',
        'description': 'All required template sections must be completed',
        'check': 'check_required_sections',
    },
    {
        'code': 'MDH-FMT-005',
        'name': 'Minimum Content Length',
        'description': 'Each section must have meaningful content (>20 characters)',
        'check': 'check_section_content_length',
    },
    {
        'code': 'MDH-FMT-006',
        'name': 'Target Category',
        'description': 'A target SOP Manual category must be selected',
        'check': 'check_target_category',
    },
    {
        'code': 'MDH-FMT-007',
        'name': 'SOP Numbering Convention',
        'description': 'Title should include SOP reference number (e.g. SOP-CLN-001)',
        'check': 'check_sop_numbering',
    },
    {
        'code': 'MDH-FMT-008',
        'name': 'No Placeholder Text',
        'description': 'Content should not contain placeholder text like [TBD], [TODO], [INSERT]',
        'check': 'check_no_placeholders',
    },
]

ICD_RULES = [
    {
        'code': 'ICD-REQ-001',
        'name': 'ICD-11 Codes Required',
        'description': 'Clinical SOPs must reference at least one ICD-11 code',
        'check': 'check_icd_codes_present',
    },
    {
        'code': 'ICD-VAL-001',
        'name': 'ICD-11 Code Validity',
        'description': 'All referenced ICD-11 codes must exist in the system',
        'check': 'check_icd_codes_valid',
    },
    {
        'code': 'ICD-FMT-001',
        'name': 'ICD-11 Code Format',
        'description': 'ICD-11 codes must follow the standard alphanumeric format',
        'check': 'check_icd_code_format',
    },
]

CONTENT_RULES = [
    {
        'code': 'CNT-QTY-001',
        'name': 'Procedure Steps',
        'description': 'Procedure section should contain numbered steps',
        'check': 'check_procedure_steps',
    },
    {
        'code': 'CNT-QTY-002',
        'name': 'Overall Content Volume',
        'description': 'Total draft content should be at least 200 characters',
        'check': 'check_total_content_volume',
    },
]


class SOPValidator:
    """Validates an SOPDraft against standard rules, ICD standards, and content quality."""

    def __init__(self, draft):
        self.draft = draft
        self.results = []

    def validate_all(self):
        """Run all validation rules and save results."""
        from .models import ValidationResult

        # Clear previous validations
        self.draft.validations.all().delete()
        self.results = []

        # Run formatting rules
        for rule in MDH_RULES:
            method = getattr(self, rule['check'], None)
            if method:
                method(rule)

        # Run ICD rules only for clinical SOPs
        if self.draft.is_clinical:
            for rule in ICD_RULES:
                method = getattr(self, rule['check'], None)
                if method:
                    method(rule)

        # Run content quality rules
        for rule in CONTENT_RULES:
            method = getattr(self, rule['check'], None)
            if method:
                method(rule)

        # Bulk create validation results
        validation_objects = []
        for r in self.results:
            validation_objects.append(ValidationResult(
                draft=self.draft,
                rule_code=r['code'],
                severity=r['severity'],
                field_name=r.get('field', ''),
                message=r['message'],
                suggestion=r.get('suggestion', ''),
            ))
        ValidationResult.objects.bulk_create(validation_objects)

        # Calculate score
        score = self._calculate_score()
        self.draft.validation_score = score
        self.draft.last_validated_at = timezone.now()

        # Update status based on score
        if score >= 80:
            self.draft.status = 'validated'
        else:
            self.draft.status = 'needs_revision'

        self.draft.save()
        return score

    def _calculate_score(self):
        """Calculate a 0-100 validation score."""
        if not self.results:
            return 100

        total_rules = len(self.results)
        errors = sum(1 for r in self.results if r['severity'] == 'error')
        warnings = sum(1 for r in self.results if r['severity'] == 'warning')
        passed = sum(1 for r in self.results if r['severity'] == 'success')

        # Deduct points: errors=-15, warnings=-5
        score = 100 - (errors * 15) - (warnings * 5)
        return max(0, min(100, score))

    def _add_result(self, code, severity, message, field='', suggestion=''):
        self.results.append({
            'code': code,
            'severity': severity,
            'message': message,
            'field': field,
            'suggestion': suggestion,
        })

    # ─── Formatting Checks ───────────────────────────────────

    def check_title(self, rule):
        if not self.draft.title or not self.draft.title.strip():
            self._add_result(rule['code'], 'error', 'SOP title is missing.', 'title',
                             'Provide a clear, descriptive title for the SOP.')
        else:
            self._add_result(rule['code'], 'success', 'Title is present.', 'title')

    def check_title_length(self, rule):
        title = self.draft.title or ''
        length = len(title.strip())
        if length < 10:
            self._add_result(rule['code'], 'warning',
                             f'Title is too short ({length} chars). Minimum recommended: 10.',
                             'title', 'Use a more descriptive title, e.g. "SOP-CLN-001: Hand Hygiene Protocol for Clinical Staff"')
        elif length > 150:
            self._add_result(rule['code'], 'warning',
                             f'Title is too long ({length} chars). Maximum recommended: 150.',
                             'title', 'Shorten the title to be more concise.')
        else:
            self._add_result(rule['code'], 'success', f'Title length is appropriate ({length} chars).', 'title')

    def check_version_format(self, rule):
        version = self.draft.version or ''
        if not re.match(r'^\d+\.\d+$', version.strip()):
            self._add_result(rule['code'], 'warning',
                             f'Version "{version}" does not follow semantic format.',
                             'version', 'Use format like 1.0, 1.1, 2.0')
        else:
            self._add_result(rule['code'], 'success', f'Version format is correct ({version}).', 'version')

    def check_required_sections(self, rule):
        sections = self.draft.sections.all()
        missing = []
        for section in sections:
            if section.is_required and not section.content.strip():
                missing.append(section.section_label)

        if missing:
            self._add_result(rule['code'], 'error',
                             f'Missing required sections: {", ".join(missing)}.',
                             'sections',
                             'Complete all required sections before validation.')
        else:
            self._add_result(rule['code'], 'success', 'All required sections are completed.', 'sections')

    def check_section_content_length(self, rule):
        sections = self.draft.sections.filter(content__gt='')
        short_sections = []
        for section in sections:
            if len(section.content.strip()) < 20:
                short_sections.append(section.section_label)

        if short_sections:
            self._add_result(rule['code'], 'warning',
                             f'Sections with insufficient content: {", ".join(short_sections)}.',
                             'sections',
                             'Each section should contain at least 20 characters of meaningful content.')
        else:
            self._add_result(rule['code'], 'success', 'All filled sections have adequate content.', 'sections')

    def check_target_category(self, rule):
        if not self.draft.target_category:
            self._add_result(rule['code'], 'error',
                             'No target SOP Manual category selected.',
                             'target_category',
                             'Select a category from the SOP Manual where this will be published.')
        else:
            self._add_result(rule['code'], 'success',
                             f'Target category: {self.draft.target_category.name}.',
                             'target_category')

    def check_sop_numbering(self, rule):
        title = self.draft.title or ''
        # Check for patterns like SOP-XXX-000 or MDH-SOP-000
        if re.search(r'SOP[-\s]?\w{2,5}[-\s]?\d{2,4}', title, re.IGNORECASE):
            self._add_result(rule['code'], 'success',
                             'SOP reference number found in title.', 'title')
        else:
            self._add_result(rule['code'], 'info',
                             'No SOP reference number detected in title.',
                             'title',
                             'Consider adding an SOP reference (e.g. SOP-CLN-001) for easy identification.')

    def check_no_placeholders(self, rule):
        placeholders = [r'\[TBD\]', r'\[TODO\]', r'\[INSERT', r'\[PLACEHOLDER\]', r'XXXX', r'\[FILL IN\]']
        found_in = []

        for section in self.draft.sections.all():
            for pattern in placeholders:
                if re.search(pattern, section.content, re.IGNORECASE):
                    found_in.append(section.section_label)
                    break

        if found_in:
            self._add_result(rule['code'], 'error',
                             f'Placeholder text found in: {", ".join(found_in)}.',
                             'sections',
                             'Replace all placeholder text with actual content before publishing.')
        else:
            self._add_result(rule['code'], 'success', 'No placeholder text detected.', 'sections')

    # ─── ICD-11 Checks ───────────────────────────────────────────

    def check_icd_codes_present(self, rule):
        codes = self.draft.icd_codes
        if not codes:
            self._add_result(rule['code'], 'error',
                             'Clinical SOP must reference at least one ICD-11 code.',
                             'icd_codes',
                             'Use the ICD-11 lookup to add relevant diagnosis or procedure codes.')
        else:
            self._add_result(rule['code'], 'success',
                             f'{len(codes)} ICD-11 code(s) referenced.', 'icd_codes')

    def check_icd_codes_valid(self, rule):
        from mdh_intranet.icd11_tools.models import ICDCode

        codes = self.draft.icd_codes
        invalid = []
        for entry in codes:
            code_str = entry.get('code', '')
            if not ICDCode.objects.filter(code=code_str).exists():
                invalid.append(code_str)

        if invalid:
            self._add_result(rule['code'], 'warning',
                             f'Unrecognized ICD-11 codes: {", ".join(invalid)}.',
                             'icd_codes',
                             'Verify codes against the ICD-11 reference in the system.')
        elif codes:
            self._add_result(rule['code'], 'success',
                             'All ICD-11 codes verified against the database.', 'icd_codes')

    def check_icd_code_format(self, rule):
        codes = self.draft.icd_codes
        bad_format = []
        # ICD-11 codes generally follow patterns like: 1A00, 1A00.0, BA00, etc.
        icd_pattern = re.compile(r'^[A-Z0-9]{2,6}(\.\d{1,4})?$', re.IGNORECASE)

        for entry in codes:
            code_str = entry.get('code', '')
            if not icd_pattern.match(code_str):
                bad_format.append(code_str)

        if bad_format:
            self._add_result(rule['code'], 'warning',
                             f'ICD-11 code format issues: {", ".join(bad_format)}.',
                             'icd_codes',
                             'ICD-11 codes typically follow alphanumeric patterns (e.g. 1A00, BA01.2).')
        elif codes:
            self._add_result(rule['code'], 'success',
                             'All ICD-11 codes follow standard format.', 'icd_codes')

    # ─── Content Quality Checks ──────────────────────────────────

    def check_procedure_steps(self, rule):
        """Check if procedure/steps section contains numbered items."""
        procedure_sections = self.draft.sections.filter(
            section_key__in=['procedure', 'steps', 'procedure_steps', 'method']
        )
        for section in procedure_sections:
            # Look for numbered steps (1. or 1), bullet points, or HTML list items <li>
            if re.search(r'(\d+[\.\)]\s|\•|\-\s|<li\b)', section.content, re.IGNORECASE):
                self._add_result(rule['code'], 'success',
                                 'Procedure section contains structured steps.',
                                 section.section_key)
                return

            self._add_result(rule['code'], 'info',
                             'Procedure section may benefit from numbered steps.',
                             section.section_key,
                             'Use numbered steps (1. Step one, 2. Step two) or the list tool for clarity.')
            return

        # No procedure section found at all
        self._add_result(rule['code'], 'info',
                         'No procedure/steps section found.',
                         'sections',
                         'Most SOPs should include a step-by-step procedure section.')

    def check_total_content_volume(self, rule):
        # Remove HTML tags for meaningful character count
        clean_text = re.sub(r'<[^>]+>', '', "".join(s.content for s in self.draft.sections.all()))
        total = len(clean_text)
        if total < 200:
            self._add_result(rule['code'], 'warning',
                             f'Total content is quite brief ({total} chars).',
                             'sections',
                             'A comprehensive SOP typically has more detailed content. Aim for at least 200 characters total.')
        else:
            self._add_result(rule['code'], 'success',
                             f'Content volume is adequate ({total} chars).', 'sections')


def compile_sop_html(draft):
    """
    Compile a draft's sections into final standard-formatted HTML content
    ready for the SOP Manual.
    """
    sections = draft.sections.all().order_by('order')
    html_parts = []

    # ── Header Table ──
    html_parts.append(
        '<div class="sop-header-block mb-4">'
        '<table class="table table-bordered mb-0">'
        '<thead><tr>'
        '<th colspan="2" class="text-center">OPSHUB — STANDARD OPERATING PROCEDURE</th>'
        '</tr></thead>'
        '<tbody>'
        f'<tr><td class="fw-bold" style="width:30%;">SOP Title</td><td>{draft.title}</td></tr>'
        f'<tr><td class="fw-bold">Version</td><td>{draft.version}</td></tr>'
        f'<tr><td class="fw-bold">Category</td><td>{draft.target_category.name if draft.target_category else "—"}</td></tr>'
        f'<tr><td class="fw-bold">Author</td><td>{draft.author.get_full_name() or draft.author.username}</td></tr>'
        f'<tr><td class="fw-bold">Effective Date</td><td>{timezone.now().strftime("%d %B %Y")}</td></tr>'
    )

    # Add ICD-11 codes if clinical
    if draft.is_clinical and draft.icd_codes:
        codes_str = ', '.join(f'{c["code"]} — {c.get("description", "")}' for c in draft.icd_codes)
        html_parts.append(
            f'<tr><td class="fw-bold">ICD-11 Reference(s)</td><td>{codes_str}</td></tr>'
        )

    html_parts.append('</tbody></table></div>')

    # ── Section Content ──
    html_parts.append('<div class="sop-content-formatted">')

    for section in sections:
        if section.content.strip():
            html_parts.append(
                f'<h5 class="text-primary fw-bold mt-4 mb-3">'
                f'<i class="fas fa-chevron-right me-2 small"></i>{section.section_label}</h5>'
            )
            # If the content contains HTML tags, we assume it's from the rich text editor
            if '<' in section.content and '>' in section.content:
                html_parts.append(f'<div class="section-html-content">{section.content}</div>')
            else:
                # Fallback for old plain text content: convert newlines to paragraphs
                content = section.content.strip()
                paragraphs = content.split('\n')
                for para in paragraphs:
                    para = para.strip()
                    if para:
                        if re.match(r'^\d+[\.\)]\s', para):
                            html_parts.append(f'<div class="ps-3 mb-1"><span>{para}</span></div>')
                        else:
                            html_parts.append(f'<p>{para}</p>')

    html_parts.append('</div>')

    return '\n'.join(html_parts)
