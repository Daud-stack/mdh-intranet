"""
Management command to seed default SOP templates.
"""
import json
from django.core.management.base import BaseCommand
from mdh_intranet.sop_assistant.models import SOPTemplate


DEFAULT_TEMPLATES = [
    {
        'name': 'Clinical Procedure SOP',
        'description': 'Standard template for documenting clinical procedures including patient care protocols, diagnostic processes, and treatment workflows.',
        'category': 'clinical',
        'icon': 'fas fa-heartbeat',
        'is_clinical': True,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose / Objective', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the purpose and objective of this SOP...',
             'help_text': 'Clearly state why this procedure exists and what it aims to achieve.', 'rows': 4},
            {'key': 'scope', 'label': 'Scope', 'type': 'textarea', 'required': True,
             'placeholder': 'Define the scope and applicability...',
             'help_text': 'Who does this apply to? Which departments/units?', 'rows': 3},
            {'key': 'definitions', 'label': 'Definitions & Abbreviations', 'type': 'textarea', 'required': False,
             'placeholder': 'List key terms and abbreviations used...',
             'help_text': 'Define any medical terminology or abbreviations.', 'rows': 4},
            {'key': 'responsibilities', 'label': 'Responsibilities', 'type': 'textarea', 'required': True,
             'placeholder': 'List responsible personnel and their roles...',
             'help_text': 'Who is responsible for each aspect of this procedure?', 'rows': 4},
            {'key': 'equipment', 'label': 'Equipment & Materials', 'type': 'textarea', 'required': True,
             'placeholder': 'List all required equipment, supplies, and materials...',
             'help_text': 'Include specific brands, sizes, or specifications if applicable.', 'rows': 4},
            {'key': 'procedure', 'label': 'Procedure (Step-by-Step)', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...\n3. Step three...',
             'help_text': 'Provide clear, numbered steps. Be specific and unambiguous.', 'rows': 10},
            {'key': 'safety', 'label': 'Safety / Infection Control', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe safety precautions and infection control measures...',
             'help_text': 'Include PPE requirements, biohazard handling, and waste disposal.', 'rows': 4},
            {'key': 'documentation', 'label': 'Documentation Requirements', 'type': 'textarea', 'required': False,
             'placeholder': 'What must be documented? Where?',
             'help_text': 'Describe any documentation, charting, or record-keeping requirements.', 'rows': 3},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'List references, guidelines, or protocols...',
             'help_text': 'Include WHO guidelines, national protocols, or internal references.', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
            'requires_icd_codes': True,
            'requires_numbered_steps': True,
        },
    },
    {
        'name': 'Nursing Protocol',
        'description': 'Template for nursing-specific care protocols, patient assessment procedures, and ward management guidelines.',
        'category': 'nursing',
        'icon': 'fas fa-user-nurse',
        'is_clinical': True,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True,
             'placeholder': 'State the purpose of this nursing protocol...', 'rows': 3},
            {'key': 'scope', 'label': 'Scope & Applicability', 'type': 'textarea', 'required': True,
             'placeholder': 'Which wards, units, and staff does this apply to?', 'rows': 3},
            {'key': 'patient_criteria', 'label': 'Patient Criteria', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe patient inclusion/exclusion criteria...',
             'help_text': 'Which patients does this protocol apply to?', 'rows': 4},
            {'key': 'assessment', 'label': 'Assessment / Observation', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe assessment steps and observations required...', 'rows': 5},
            {'key': 'procedure', 'label': 'Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...', 'rows': 8},
            {'key': 'complications', 'label': 'Complications & Escalation', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe potential complications and escalation pathways...',
             'help_text': 'When should staff escalate to a doctor or senior nurse?', 'rows': 4},
            {'key': 'documentation', 'label': 'Documentation', 'type': 'textarea', 'required': True,
             'placeholder': 'What must be documented in the patient chart?', 'rows': 3},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'List any references...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
            'requires_icd_codes': True,
        },
    },
    {
        'name': 'Laboratory Procedure',
        'description': 'Template for laboratory testing procedures, sample handling protocols, and quality control standards.',
        'category': 'laboratory',
        'icon': 'fas fa-flask',
        'is_clinical': True,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the purpose of this laboratory procedure...', 'rows': 3},
            {'key': 'scope', 'label': 'Scope', 'type': 'textarea', 'required': True,
             'placeholder': 'Define the scope...', 'rows': 3},
            {'key': 'principle', 'label': 'Principle / Method', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the scientific principle or analytical method...',
             'help_text': 'Explain the methodology or test principle.', 'rows': 4},
            {'key': 'specimen', 'label': 'Specimen Requirements', 'type': 'textarea', 'required': True,
             'placeholder': 'Type of specimen, collection method, volume, container, transport conditions...',
             'rows': 4},
            {'key': 'reagents', 'label': 'Reagents & Equipment', 'type': 'textarea', 'required': True,
             'placeholder': 'List all reagents, chemicals, and equipment needed...', 'rows': 4},
            {'key': 'procedure', 'label': 'Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...', 'rows': 8},
            {'key': 'quality_control', 'label': 'Quality Control', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe QC procedures, acceptable ranges, calibration...', 'rows': 4},
            {'key': 'results', 'label': 'Results Interpretation', 'type': 'textarea', 'required': True,
             'placeholder': 'How should results be interpreted and reported?', 'rows': 4},
            {'key': 'safety', 'label': 'Safety & Waste Disposal', 'type': 'textarea', 'required': True,
             'placeholder': 'Safety precautions and waste disposal procedures...', 'rows': 4},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'List references...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
            'requires_icd_codes': True,
            'requires_numbered_steps': True,
        },
    },
    {
        'name': 'Administrative Procedure',
        'description': 'Template for non-clinical administrative processes such as patient registration, billing, records management, and HR procedures.',
        'category': 'admin',
        'icon': 'fas fa-briefcase',
        'is_clinical': False,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the purpose of this administrative procedure...', 'rows': 3},
            {'key': 'scope', 'label': 'Scope', 'type': 'textarea', 'required': True,
             'placeholder': 'Which departments and staff does this apply to?', 'rows': 3},
            {'key': 'responsibilities', 'label': 'Responsibilities', 'type': 'textarea', 'required': True,
             'placeholder': 'Assign responsibilities to specific roles or departments...', 'rows': 4},
            {'key': 'procedure', 'label': 'Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...', 'rows': 8},
            {'key': 'forms', 'label': 'Required Forms / Documents', 'type': 'textarea', 'required': False,
             'placeholder': 'List any forms, templates, or documents needed...', 'rows': 3},
            {'key': 'compliance', 'label': 'Compliance & Audit', 'type': 'textarea', 'required': False,
             'placeholder': 'Describe compliance requirements and audit processes...', 'rows': 3},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'List references...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
        },
    },
    {
        'name': 'Infection Control Protocol',
        'description': 'Template for infection prevention and control procedures including hand hygiene, isolation protocols, and decontamination.',
        'category': 'infection_control',
        'icon': 'fas fa-shield-virus',
        'is_clinical': True,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the infection control objective...', 'rows': 3},
            {'key': 'scope', 'label': 'Scope', 'type': 'textarea', 'required': True,
             'placeholder': 'All staff, visitors, patients?', 'rows': 3},
            {'key': 'risk_assessment', 'label': 'Risk Assessment', 'type': 'textarea', 'required': True,
             'placeholder': 'Identify infection risks and transmission routes...',
             'help_text': 'Describe the risk categories and transmission pathways.', 'rows': 4},
            {'key': 'precautions', 'label': 'Standard Precautions', 'type': 'textarea', 'required': True,
             'placeholder': 'Hand hygiene, PPE, respiratory hygiene...', 'rows': 5},
            {'key': 'procedure', 'label': 'Specific Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...', 'rows': 8},
            {'key': 'surveillance', 'label': 'Surveillance & Reporting', 'type': 'textarea', 'required': True,
             'placeholder': 'How to monitor and report infections...', 'rows': 4},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'WHO guidelines, CDC recommendations...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
            'requires_icd_codes': True,
        },
    },
    {
        'name': 'Emergency Response SOP',
        'description': 'Template for emergency response procedures including code blue, fire response, mass casualty, and disaster management.',
        'category': 'emergency',
        'icon': 'fas fa-ambulance',
        'is_clinical': True,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the emergency scenario and response objective...', 'rows': 3},
            {'key': 'activation', 'label': 'Activation Criteria', 'type': 'textarea', 'required': True,
             'placeholder': 'When should this emergency procedure be activated?',
             'help_text': 'Define clear triggers or criteria.', 'rows': 4},
            {'key': 'roles', 'label': 'Roles & Responsibilities', 'type': 'textarea', 'required': True,
             'placeholder': 'Team leader, first responders, support staff...', 'rows': 5},
            {'key': 'procedure', 'label': 'Response Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Immediate actions...\n2. Assessment...\n3. Intervention...', 'rows': 10},
            {'key': 'equipment', 'label': 'Equipment & Location', 'type': 'textarea', 'required': True,
             'placeholder': 'Emergency equipment, crash cart location, AED...', 'rows': 4},
            {'key': 'communication', 'label': 'Communication Protocol', 'type': 'textarea', 'required': True,
             'placeholder': 'Who to call, SBAR format, notification chain...', 'rows': 4},
            {'key': 'post_event', 'label': 'Post-Event Actions', 'type': 'textarea', 'required': True,
             'placeholder': 'Debriefing, documentation, equipment restocking...', 'rows': 4},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'ACLS guidelines, institutional protocols...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
            'requires_icd_codes': True,
            'requires_numbered_steps': True,
        },
    },
    {
        'name': 'Pharmacy Protocol',
        'description': 'Template for pharmacy operations including medication dispensing, storage, compounding, and drug interaction protocols.',
        'category': 'pharmacy',
        'icon': 'fas fa-pills',
        'is_clinical': True,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the pharmacy procedure objective...', 'rows': 3},
            {'key': 'scope', 'label': 'Scope', 'type': 'textarea', 'required': True,
             'placeholder': 'Pharmacy staff, ward pharmacists, dispensary...', 'rows': 3},
            {'key': 'medications', 'label': 'Medication Details', 'type': 'textarea', 'required': True,
             'placeholder': 'List medications, dosage forms, strengths...',
             'help_text': 'Include generic names, brand names, and formulations.', 'rows': 5},
            {'key': 'procedure', 'label': 'Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...', 'rows': 8},
            {'key': 'storage', 'label': 'Storage & Handling', 'type': 'textarea', 'required': True,
             'placeholder': 'Temperature, light sensitivity, expiry management...', 'rows': 4},
            {'key': 'safety', 'label': 'Safety & Adverse Effects', 'type': 'textarea', 'required': True,
             'placeholder': 'Contraindications, drug interactions, adverse event reporting...', 'rows': 4},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'Pharmacopeia, manufacturer guidelines...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
            'requires_icd_codes': True,
        },
    },
    {
        'name': 'General Operations SOP',
        'description': 'Flexible general-purpose template for any standard operating procedure that does not fit into the specialized categories above.',
        'category': 'general',
        'icon': 'fas fa-cogs',
        'is_clinical': False,
        'sections': [
            {'key': 'purpose', 'label': 'Purpose / Objective', 'type': 'textarea', 'required': True,
             'placeholder': 'Describe the purpose...', 'rows': 4},
            {'key': 'scope', 'label': 'Scope', 'type': 'textarea', 'required': True,
             'placeholder': 'Define who and what this applies to...', 'rows': 3},
            {'key': 'responsibilities', 'label': 'Responsibilities', 'type': 'textarea', 'required': True,
             'placeholder': 'Assign responsibilities...', 'rows': 4},
            {'key': 'procedure', 'label': 'Procedure', 'type': 'textarea', 'required': True,
             'placeholder': '1. Step one...\n2. Step two...', 'rows': 8},
            {'key': 'references', 'label': 'References', 'type': 'textarea', 'required': False,
             'placeholder': 'List any references...', 'rows': 3},
        ],
        'formatting_rules': {
            'requires_header_table': True,
            'requires_version': True,
        },
    },
]


class Command(BaseCommand):
    help = 'Seed default SOP templates for the SOP Drafting Assistant'

    def handle(self, *args, **options):
        created = 0
        skipped = 0

        for tpl_data in DEFAULT_TEMPLATES:
            name = tpl_data['name']
            if SOPTemplate.objects.filter(name=name).exists():
                skipped += 1
                self.stdout.write(self.style.WARNING(f'  Skipped (exists): {name}'))
                continue

            SOPTemplate.objects.create(
                name=name,
                description=tpl_data['description'],
                category=tpl_data['category'],
                icon=tpl_data['icon'],
                is_clinical=tpl_data['is_clinical'],
                sections_json=json.dumps(tpl_data['sections']),
                formatting_rules_json=json.dumps(tpl_data['formatting_rules']),
            )
            created += 1
            self.stdout.write(self.style.SUCCESS(f'  Created: {name}'))

        self.stdout.write(self.style.SUCCESS(
            f'\nDone! Created {created} templates, skipped {skipped}.'
        ))
