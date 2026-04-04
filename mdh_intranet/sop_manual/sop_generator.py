"""
SOP Generator Engine — Intelligent template-based SOP content generation.

Generates structured, professional SOP documents by:
  1. Selecting the right template for the SOP type
  2. Pulling relevant data from incidents, CAPAs, and existing SOPs
  3. Building a complete document with proper sections, tables, and formatting
"""
from django.utils import timezone
from django.db.models import Q, Count


# ── SOP SECTION TEMPLATES ──────────────────────────────────────
# Each template is a dict of section_key → (heading, content_generator_fn)

SOP_TEMPLATES = {
    'clinical_procedure': {
        'label': 'Clinical Procedure',
        'icon': 'fas fa-heartbeat',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'prerequisites', 'equipment', 'procedure_steps',
            'safety_considerations', 'documentation_requirements',
            'quality_control', 'references', 'revision_history',
        ],
    },
    'infection_control': {
        'label': 'Infection Control',
        'icon': 'fas fa-shield-virus',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'standard_precautions', 'ppe_requirements', 'procedure_steps',
            'waste_disposal', 'exposure_management',
            'documentation_requirements', 'references', 'revision_history',
        ],
    },
    'medication_management': {
        'label': 'Medication Management',
        'icon': 'fas fa-pills',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'storage_requirements', 'dispensing_procedure',
            'administration_procedure', 'adverse_reaction_protocol',
            'documentation_requirements', 'references', 'revision_history',
        ],
    },
    'equipment_operation': {
        'label': 'Equipment Operation',
        'icon': 'fas fa-cogs',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'equipment_description', 'safety_precautions',
            'startup_procedure', 'operation_steps', 'shutdown_procedure',
            'troubleshooting', 'maintenance_schedule',
            'documentation_requirements', 'references', 'revision_history',
        ],
    },
    'emergency_response': {
        'label': 'Emergency Response',
        'icon': 'fas fa-ambulance',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'activation_criteria', 'immediate_actions',
            'communication_protocol', 'evacuation_procedure',
            'post_incident_actions', 'drill_schedule',
            'documentation_requirements', 'references', 'revision_history',
        ],
    },
    'administrative': {
        'label': 'Administrative / General',
        'icon': 'fas fa-file-alt',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'procedure_steps', 'documentation_requirements',
            'quality_control', 'references', 'revision_history',
        ],
    },
    'patient_care': {
        'label': 'Patient Care',
        'icon': 'fas fa-user-nurse',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'patient_assessment', 'procedure_steps',
            'post_procedure_care', 'patient_education',
            'documentation_requirements', 'quality_control',
            'references', 'revision_history',
        ],
    },
    'laboratory': {
        'label': 'Laboratory',
        'icon': 'fas fa-flask',
        'sections': [
            'header_block', 'purpose', 'scope', 'responsibilities',
            'specimen_requirements', 'equipment', 'reagents',
            'procedure_steps', 'quality_control',
            'result_interpretation', 'safety_considerations',
            'documentation_requirements', 'references', 'revision_history',
        ],
    },
}


# ── SECTION CONTENT BUILDERS ───────────────────────────────────

def _header_block(title, category, author, version, date_str):
    return f"""<div class="sop-header-block mb-4">
    <table class="table table-bordered mb-0">
        <thead>
            <tr>
                <th colspan="2" class="text-center" style="background-color: #0d6efd; color: white;">
                    MBUYA DORCAS HOSPITAL — STANDARD OPERATING PROCEDURE
                </th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td class="fw-bold" style="width: 30%; background-color: #f8f9fa;">SOP Title</td>
                <td>{title}</td>
            </tr>
            <tr>
                <td class="fw-bold" style="background-color: #f8f9fa;">Department / Category</td>
                <td>{category}</td>
            </tr>
            <tr>
                <td class="fw-bold" style="background-color: #f8f9fa;">Author</td>
                <td>{author}</td>
            </tr>
            <tr>
                <td class="fw-bold" style="background-color: #f8f9fa;">Version / Date</td>
                <td>v{version} | Effective: {date_str}</td>
            </tr>
        </tbody>
    </table>
</div>"""


SECTION_BUILDERS = {
    'purpose': (
        'Purpose',
        '<p>This Standard Operating Procedure (SOP) establishes the guidelines and requirements for {title_lower}. '
        'It ensures consistent, safe, and compliant practices across all relevant departments and personnel.</p>'
    ),
    'scope': (
        'Scope',
        '<p>This SOP applies to all staff members involved in {title_lower} at Mbuya Dorcas Hospital. '
        'It covers all aspects of the procedure from initiation through completion and documentation.</p>'
        '<p><strong>In scope:</strong></p>'
        '<ul>'
        '<li>All clinical and support staff performing this procedure</li>'
        '<li>All departments where this procedure may be carried out</li>'
        '<li>Training and competency requirements</li>'
        '</ul>'
        '<p><strong>Out of scope:</strong></p>'
        '<ul>'
        '<li>[Define any exclusions]</li>'
        '</ul>'
    ),
    'responsibilities': (
        'Roles & Responsibilities',
        '<table class="table table-bordered">'
        '<thead><tr><th>Role</th><th>Responsibility</th></tr></thead>'
        '<tbody>'
        '<tr><td><strong>Department Head</strong></td><td>Overall accountability; approve SOP changes; ensure staff training</td></tr>'
        '<tr><td><strong>Supervisor / Charge Nurse</strong></td><td>Day-to-day oversight; monitor compliance; report deviations</td></tr>'
        '<tr><td><strong>Clinical Staff</strong></td><td>Execute procedure per this SOP; report issues immediately</td></tr>'
        '<tr><td><strong>Quality Officer</strong></td><td>Audit compliance; review incident reports; recommend improvements</td></tr>'
        '<tr><td><strong>Training Coordinator</strong></td><td>Ensure all staff are trained and competencies are documented</td></tr>'
        '</tbody></table>'
    ),
    'prerequisites': (
        'Prerequisites',
        '<p>Before commencing this procedure, ensure the following prerequisites are met:</p>'
        '<ol>'
        '<li>Staff member has completed required training and competency assessment</li>'
        '<li>All necessary equipment and supplies are available and functional</li>'
        '<li>Patient identification has been verified (if applicable)</li>'
        '<li>Informed consent has been obtained (if applicable)</li>'
        '<li>Relevant patient history and allergies have been reviewed</li>'
        '<li>Work area is clean and prepared</li>'
        '</ol>'
    ),
    'equipment': (
        'Equipment & Supplies Required',
        '<table class="table table-bordered">'
        '<thead><tr><th>Item</th><th>Specification</th><th>Quantity</th></tr></thead>'
        '<tbody>'
        '<tr><td>[Equipment 1]</td><td>[Specification]</td><td>[Qty]</td></tr>'
        '<tr><td>[Equipment 2]</td><td>[Specification]</td><td>[Qty]</td></tr>'
        '<tr><td>[Consumable 1]</td><td>[Specification]</td><td>[Qty]</td></tr>'
        '<tr><td>[PPE Required]</td><td>[Specification]</td><td>[As needed]</td></tr>'
        '</tbody></table>'
        '<p><em><strong>Note:</strong> Verify all equipment is calibrated and within service date before use.</em></p>'
    ),
    'procedure_steps': (
        'Procedure',
        '<h6>Preparation</h6>'
        '<ol>'
        '<li>Verify patient identification using two identifiers (if applicable)</li>'
        '<li>Gather all required equipment and supplies</li>'
        '<li>Perform hand hygiene per WHO guidelines</li>'
        '<li>Don appropriate PPE as required</li>'
        '</ol>'
        '<h6>Execution</h6>'
        '<ol start="5">'
        '<li>[Step 5 — describe action]</li>'
        '<li>[Step 6 — describe action]</li>'
        '<li>[Step 7 — describe action]</li>'
        '<li>[Step 8 — describe action]</li>'
        '</ol>'
        '<h6>Completion</h6>'
        '<ol start="9">'
        '<li>Dispose of waste materials per waste management protocol</li>'
        '<li>Remove PPE and perform hand hygiene</li>'
        '<li>Document procedure in patient record / logbook</li>'
        '<li>Report any deviations or adverse events immediately</li>'
        '</ol>'
    ),
    'safety_considerations': (
        'Safety Considerations',
        '<div class="alert alert-warning">'
        '<strong><i class="fas fa-exclamation-triangle me-2"></i>Critical Safety Points:</strong>'
        '<ul>'
        '<li>Always follow standard precautions</li>'
        '<li>Verify patient identity before any intervention</li>'
        '<li>Report sharps injuries immediately per the Needlestick Injury Protocol</li>'
        '<li>In case of chemical exposure, consult the Safety Data Sheet (SDS)</li>'
        '<li>Emergency equipment must be accessible at all times</li>'
        '<li>Do not proceed if you are unsure — escalate to supervisor</li>'
        '</ul>'
        '</div>'
    ),
    'documentation_requirements': (
        'Documentation Requirements',
        '<p>The following documentation must be completed:</p>'
        '<ol>'
        '<li><strong>Patient Record:</strong> Document the procedure, findings, and any complications</li>'
        '<li><strong>Logbook:</strong> Record date, time, staff involved, and outcome</li>'
        '<li><strong>Incident Report:</strong> Complete if any adverse event or deviation occurs</li>'
        '<li><strong>Equipment Log:</strong> Record equipment used and any issues</li>'
        '<li><strong>Consent Form:</strong> File signed consent (if applicable)</li>'
        '</ol>'
        '<p><em>All records must be legible, signed, and dated.</em></p>'
    ),
    'quality_control': (
        'Quality Control & Monitoring',
        '<table class="table table-bordered">'
        '<thead><tr><th>Metric</th><th>Target</th><th>Frequency</th><th>Responsible</th></tr></thead>'
        '<tbody>'
        '<tr><td>Compliance rate</td><td>&ge; 95%</td><td>Monthly</td><td>Quality Officer</td></tr>'
        '<tr><td>Adverse event rate</td><td>&lt; 1%</td><td>Monthly</td><td>Department Head</td></tr>'
        '<tr><td>Staff competency</td><td>100% current</td><td>Quarterly</td><td>Training Coordinator</td></tr>'
        '<tr><td>Documentation accuracy</td><td>&ge; 98%</td><td>Monthly</td><td>Supervisor</td></tr>'
        '</tbody></table>'
        '<p>Non-conformances must be reported via the Incident Log and may trigger a CAPA review.</p>'
    ),
    'references': (
        'References',
        '<ul>'
        '<li>WHO Guidelines — [Relevant guideline]</li>'
        '<li>Ministry of Health and Child Care — [Relevant regulation]</li>'
        '<li>Mbuya Dorcas Hospital Policy Manual</li>'
        '<li>Previous version of this SOP</li>'
        '<li>[Additional references as applicable]</li>'
        '</ul>'
    ),
    'revision_history': (
        'Revision History',
        '<table class="table table-bordered">'
        '<thead><tr><th>Version</th><th>Date</th><th>Author</th><th>Changes Made</th></tr></thead>'
        '<tbody>'
        '<tr><td>1.0</td><td>{date_str}</td><td>{author}</td><td>Initial release</td></tr>'
        '<tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>'
        '</tbody></table>'
    ),
    # ── Specialised sections ──
    'standard_precautions': (
        'Standard Precautions',
        '<p>The following standard precautions apply at all times:</p>'
        '<ol>'
        '<li><strong>Hand Hygiene:</strong> Before and after patient contact, before aseptic procedures, '
        'after body fluid exposure, after touching patient surroundings</li>'
        '<li><strong>Gloves:</strong> Wear when touching blood, body fluids, mucous membranes, or non-intact skin</li>'
        '<li><strong>Gowns:</strong> Wear during procedures likely to generate splashes</li>'
        '<li><strong>Masks & Eye Protection:</strong> Wear during procedures that may generate respiratory droplets</li>'
        '<li><strong>Sharps Safety:</strong> Use safety-engineered devices; never recap needles</li>'
        '<li><strong>Respiratory Hygiene:</strong> Cover coughs and sneezes; offer masks to symptomatic patients</li>'
        '</ol>'
    ),
    'ppe_requirements': (
        'PPE Requirements',
        '<table class="table table-bordered">'
        '<thead><tr><th>PPE Item</th><th>When Required</th><th>Standard</th></tr></thead>'
        '<tbody>'
        '<tr><td>Disposable gloves</td><td>All patient contact</td><td>EN 455</td></tr>'
        '<tr><td>Surgical mask</td><td>Droplet precautions</td><td>EN 14683 Type IIR</td></tr>'
        '<tr><td>N95 respirator</td><td>Airborne precautions</td><td>NIOSH N95</td></tr>'
        '<tr><td>Eye protection</td><td>Splash risk</td><td>EN 166</td></tr>'
        '<tr><td>Gown / Apron</td><td>Body fluid exposure risk</td><td>EN 13795</td></tr>'
        '</tbody></table>'
        '<p><strong>Donning order:</strong> Gown &rarr; Mask &rarr; Eye protection &rarr; Gloves</p>'
        '<p><strong>Doffing order:</strong> Gloves &rarr; Eye protection &rarr; Gown &rarr; Mask &rarr; Hand hygiene</p>'
    ),
    'waste_disposal': (
        'Waste Disposal',
        '<table class="table table-bordered">'
        '<thead><tr><th>Waste Type</th><th>Container</th><th>Colour</th><th>Disposal Method</th></tr></thead>'
        '<tbody>'
        '<tr><td>Infectious clinical waste</td><td>Biohazard bag</td><td>Yellow</td><td>Incineration</td></tr>'
        '<tr><td>Sharps</td><td>Puncture-proof container</td><td>Yellow</td><td>Incineration</td></tr>'
        '<tr><td>Pharmaceutical waste</td><td>Designated container</td><td>Blue</td><td>Chemical treatment</td></tr>'
        '<tr><td>General waste</td><td>Bin liner</td><td>Black</td><td>Landfill</td></tr>'
        '</tbody></table>'
        '<p><strong>Never</strong> overfill sharps containers beyond the fill line.</p>'
    ),
    'exposure_management': (
        'Exposure / Needlestick Management',
        '<p><strong>If exposure to blood or body fluids occurs:</strong></p>'
        '<ol>'
        '<li><strong>Immediately:</strong> Wash the affected area with soap and water (flush eyes with clean water)</li>'
        '<li><strong>Do not</strong> squeeze the wound</li>'
        '<li><strong>Report</strong> to supervisor immediately</li>'
        '<li><strong>Complete</strong> an Incident Report within 1 hour</li>'
        '<li><strong>Attend</strong> Occupational Health for baseline bloods within 2 hours</li>'
        '<li><strong>PEP:</strong> If indicated, commence within 72 hours (ideally within 2 hours)</li>'
        '<li><strong>Follow-up:</strong> Attend scheduled follow-up blood tests at 6 weeks, 3 months, and 6 months</li>'
        '</ol>'
    ),
    'storage_requirements': (
        'Storage Requirements',
        '<table class="table table-bordered">'
        '<thead><tr><th>Condition</th><th>Requirement</th></tr></thead>'
        '<tbody>'
        '<tr><td>Temperature</td><td>As per manufacturer specifications</td></tr>'
        '<tr><td>Light</td><td>Protected from direct sunlight</td></tr>'
        '<tr><td>Access</td><td>Restricted; locked storage for controlled substances</td></tr>'
        '<tr><td>Monitoring</td><td>Temperature log checked twice daily</td></tr>'
        '<tr><td>Expiry</td><td>First-expiry, first-out (FEFO) system</td></tr>'
        '</tbody></table>'
        '<p>All storage areas must be clean, dry, and well-ventilated.</p>'
    ),
    'dispensing_procedure': (
        'Dispensing Procedure',
        '<ol>'
        '<li>Receive and verify prescription / order</li>'
        '<li>Check patient identity, allergies, and contraindications</li>'
        '<li>Select correct medication, strength, and formulation</li>'
        '<li>Perform independent double-check for high-alert medications</li>'
        '<li>Label medication with patient name, drug, dose, route, date, and time</li>'
        '<li>Record dispensing in the Medication Register</li>'
        '<li>Counsel patient on administration, side effects, and storage</li>'
        '</ol>'
    ),
    'administration_procedure': (
        'Administration Procedure',
        '<p><strong>The 7 Rights of Medication Administration:</strong></p>'
        '<ul>'
        '<li>&check; Right <strong>Patient</strong> — verify using two identifiers</li>'
        '<li>&check; Right <strong>Medication</strong> — compare with order</li>'
        '<li>&check; Right <strong>Dose</strong> — calculate and verify</li>'
        '<li>&check; Right <strong>Route</strong> — confirm appropriate route</li>'
        '<li>&check; Right <strong>Time</strong> — administer within scheduled window</li>'
        '<li>&check; Right <strong>Documentation</strong> — record immediately after</li>'
        '<li>&check; Right <strong>Reason</strong> — confirm indication</li>'
        '</ul>'
    ),
    'adverse_reaction_protocol': (
        'Adverse Reaction Protocol',
        '<p><strong>If an adverse drug reaction (ADR) occurs:</strong></p>'
        '<ol>'
        '<li><strong>Stop</strong> the medication immediately</li>'
        '<li><strong>Assess</strong> the patient — airway, breathing, circulation</li>'
        '<li><strong>Call</strong> for help if severe reaction (anaphylaxis protocol)</li>'
        '<li><strong>Treat</strong> per clinical protocol</li>'
        '<li><strong>Document</strong> in patient notes with date, time, drug, reaction</li>'
        '<li><strong>Report</strong> via Incident Log within 24 hours</li>'
        '<li><strong>Notify</strong> prescriber and pharmacy</li>'
        '<li><strong>Submit</strong> ADR form to MCAZ (Medicines Control Authority of Zimbabwe)</li>'
        '</ol>'
    ),
    'equipment_description': (
        'Equipment Description',
        '<table class="table table-bordered">'
        '<thead><tr><th>Component</th><th>Description</th><th>Notes</th></tr></thead>'
        '<tbody>'
        '<tr><td>[Main unit]</td><td>[Description]</td><td>[Model/Serial]</td></tr>'
        '<tr><td>[Display/Controls]</td><td>[Description]</td><td>&nbsp;</td></tr>'
        '<tr><td>[Accessories]</td><td>[Description]</td><td>&nbsp;</td></tr>'
        '<tr><td>[Power supply]</td><td>[Voltage/Battery]</td><td>&nbsp;</td></tr>'
        '</tbody></table>'
        '<p><strong>Location:</strong> [Where the equipment is located]<br>'
        '<strong>Manufacturer contact:</strong> [Support details]</p>'
    ),
    'safety_precautions': (
        'Safety Precautions',
        '<div class="alert alert-danger">'
        '<strong><i class="fas fa-exclamation-circle me-2"></i>Before operating this equipment:</strong>'
        '<ul>'
        '<li>Read and understand this SOP completely</li>'
        '<li>Inspect equipment for visible damage</li>'
        '<li>Verify electrical connections and grounding</li>'
        '<li>Ensure emergency stop is accessible and functional</li>'
        '<li>Wear required PPE</li>'
        '<li>Never operate equipment in wet conditions (unless rated)</li>'
        '<li>Do not modify or bypass safety interlocks</li>'
        '</ul>'
        '</div>'
    ),
    'startup_procedure': (
        'Startup Procedure',
        '<ol>'
        '<li>Perform visual inspection of equipment</li>'
        '<li>Verify power supply is connected and stable</li>'
        '<li>Switch on main power</li>'
        '<li>Allow self-test / warm-up period to complete</li>'
        '<li>Verify calibration status (if applicable)</li>'
        '<li>Run quality control check (if applicable)</li>'
        '<li>Confirm equipment is ready for use</li>'
        '</ol>'
    ),
    'operation_steps': (
        'Operation Steps',
        '<ol>'
        '<li>[Step 1 — Load sample / position patient / prepare materials]</li>'
        '<li>[Step 2 — Select appropriate program / settings]</li>'
        '<li>[Step 3 — Initiate process]</li>'
        '<li>[Step 4 — Monitor operation]</li>'
        '<li>[Step 5 — Review results / completion]</li>'
        '<li>Record all results in the equipment logbook</li>'
        '</ol>'
    ),
    'shutdown_procedure': (
        'Shutdown Procedure',
        '<ol>'
        '<li>Complete all pending operations</li>'
        '<li>Remove samples / materials</li>'
        '<li>Clean equipment surfaces per manufacturer instructions</li>'
        '<li>Run shutdown / cleaning cycle (if applicable)</li>'
        '<li>Switch off equipment</li>'
        '<li>Cover equipment (if applicable)</li>'
        '<li>Record usage in equipment logbook</li>'
        '</ol>'
    ),
    'troubleshooting': (
        'Troubleshooting',
        '<table class="table table-bordered">'
        '<thead><tr><th>Problem</th><th>Possible Cause</th><th>Action</th></tr></thead>'
        '<tbody>'
        '<tr><td>Equipment won\'t start</td><td>Power issue</td><td>Check connections, circuit breaker</td></tr>'
        '<tr><td>Error code displayed</td><td>Various</td><td>Refer to manufacturer manual</td></tr>'
        '<tr><td>Abnormal readings</td><td>Calibration drift</td><td>Run QC; recalibrate if needed</td></tr>'
        '<tr><td>Unusual noise/smell</td><td>Mechanical issue</td><td>Stop use; contact Biomedical</td></tr>'
        '</tbody></table>'
        '<p><strong>If in doubt:</strong> Remove from service, tag "Out of Order", and contact Biomedical Engineering.</p>'
    ),
    'maintenance_schedule': (
        'Maintenance Schedule',
        '<table class="table table-bordered">'
        '<thead><tr><th>Task</th><th>Frequency</th><th>Responsible</th><th>Record</th></tr></thead>'
        '<tbody>'
        '<tr><td>Visual inspection</td><td>Daily (before use)</td><td>Operator</td><td>Equipment log</td></tr>'
        '<tr><td>Cleaning</td><td>After each use</td><td>Operator</td><td>Equipment log</td></tr>'
        '<tr><td>Calibration check</td><td>Weekly / Monthly</td><td>Biomedical</td><td>Calibration log</td></tr>'
        '<tr><td>Preventive maintenance</td><td>Per manufacturer</td><td>Biomedical</td><td>Service record</td></tr>'
        '<tr><td>Electrical safety test</td><td>Annually</td><td>Biomedical</td><td>Safety certificate</td></tr>'
        '</tbody></table>'
    ),
    'activation_criteria': (
        'Activation Criteria',
        '<p>This emergency response procedure shall be activated when:</p>'
        '<ul>'
        '<li>[Specific trigger condition 1]</li>'
        '<li>[Specific trigger condition 2]</li>'
        '<li>Any situation that poses an immediate threat to life, health, or safety</li>'
        '<li>Direction from the Incident Commander or Hospital Administrator</li>'
        '</ul>'
        '<p><strong>Activation authority:</strong> Charge Nurse, Department Head, or any staff member in an immediate emergency</p>'
    ),
    'immediate_actions': (
        'Immediate Actions',
        '<p><strong>FIRST RESPONDER actions (first 5 minutes):</strong></p>'
        '<ol>'
        '<li><span class="text-danger">&bull;</span> Ensure personal safety first</li>'
        '<li><span class="text-danger">&bull;</span> Call for help — activate emergency code</li>'
        '<li><span class="text-danger">&bull;</span> Assess the situation and number of casualties</li>'
        '<li><span class="text-danger">&bull;</span> Provide immediate first aid / life support</li>'
        '<li><span class="text-danger">&bull;</span> Restrict access to the affected area</li>'
        '<li><span class="text-danger">&bull;</span> Brief arriving emergency team</li>'
        '</ol>'
    ),
    'communication_protocol': (
        'Communication Protocol',
        '<p><strong>Use SBAR format for handover:</strong></p>'
        '<table class="table table-bordered">'
        '<thead><tr><th>Component</th><th>Content</th></tr></thead>'
        '<tbody>'
        '<tr><td><strong>S</strong>ituation</td><td>What is happening right now?</td></tr>'
        '<tr><td><strong>B</strong>ackground</td><td>What is the context?</td></tr>'
        '<tr><td><strong>A</strong>ssessment</td><td>What do you think the problem is?</td></tr>'
        '<tr><td><strong>R</strong>ecommendation</td><td>What do you need?</td></tr>'
        '</tbody></table>'
        '<p><strong>Emergency contact numbers:</strong></p>'
        '<ul>'
        '<li>Internal emergency: [Extension]</li>'
        '<li>Ambulance: [Number]</li>'
        '<li>Fire department: [Number]</li>'
        '<li>Hospital administrator (after hours): [Number]</li>'
        '</ul>'
    ),
    'evacuation_procedure': (
        'Evacuation Procedure',
        '<ol>'
        '<li>Sound the evacuation alarm</li>'
        '<li>Evacuate patients — prioritise those who can\'t self-evacuate</li>'
        '<li>Follow designated evacuation routes (see posted maps)</li>'
        '<li>Assemble at designated muster point</li>'
        '<li>Conduct head count using ward register</li>'
        '<li>Report to Incident Commander</li>'
        '<li>Do NOT re-enter the building until cleared</li>'
        '</ol>'
    ),
    'post_incident_actions': (
        'Post-Incident Actions',
        '<ol>'
        '<li>Ensure all patients and staff are accounted for</li>'
        '<li>Provide psychological first aid as needed</li>'
        '<li>Complete Incident Report within 24 hours</li>'
        '<li>Conduct debrief with all involved staff within 48 hours</li>'
        '<li>Initiate CAPA process if systemic issues identified</li>'
        '<li>Review and update this SOP based on lessons learned</li>'
        '</ol>'
    ),
    'drill_schedule': (
        'Drill Schedule',
        '<table class="table table-bordered">'
        '<thead><tr><th>Drill Type</th><th>Frequency</th><th>Participants</th><th>Coordinator</th></tr></thead>'
        '<tbody>'
        '<tr><td>Fire evacuation</td><td>Quarterly</td><td>All staff</td><td>Safety Officer</td></tr>'
        '<tr><td>Code Blue (cardiac arrest)</td><td>Monthly</td><td>Clinical staff</td><td>Resuscitation Officer</td></tr>'
        '<tr><td>Mass casualty</td><td>Bi-annually</td><td>All departments</td><td>Hospital Administrator</td></tr>'
        '<tr><td>Chemical spill</td><td>Annually</td><td>Laboratory, Maintenance</td><td>Safety Officer</td></tr>'
        '</tbody></table>'
        '<p><em>All drills must be documented and findings addressed via CAPA if needed.</em></p>'
    ),
    'patient_assessment': (
        'Patient Assessment',
        '<p><strong>Before the procedure, assess the patient for:</strong></p>'
        '<ol>'
        '<li>Identity verification (two identifiers)</li>'
        '<li>Relevant medical history and current condition</li>'
        '<li>Allergies and sensitivities</li>'
        '<li>Current medications</li>'
        '<li>Baseline vital signs</li>'
        '<li>Informed consent obtained and documented</li>'
        '<li>Specific contraindications for this procedure</li>'
        '<li>Patient understanding and readiness</li>'
        '</ol>'
    ),
    'post_procedure_care': (
        'Post-Procedure Care',
        '<ol>'
        '<li>Monitor patient vital signs per protocol</li>'
        '<li>Assess for complications or adverse reactions</li>'
        '<li>Manage pain per pain management protocol</li>'
        '<li>Provide clear post-procedure instructions</li>'
        '<li>Schedule follow-up as appropriate</li>'
        '<li>Document all post-procedure care in patient notes</li>'
        '<li>Ensure patient / caregiver understands warning signs to watch for</li>'
        '</ol>'
    ),
    'patient_education': (
        'Patient Education',
        '<p>Before discharge / departure, ensure the patient understands:</p>'
        '<ul>'
        '<li>What procedure was performed and why</li>'
        '<li>Expected outcomes and recovery timeline</li>'
        '<li>Warning signs that require immediate medical attention</li>'
        '<li>Medication instructions (if applicable)</li>'
        '<li>Follow-up appointment details</li>'
        '<li>Who to contact with questions or concerns</li>'
        '</ul>'
        '<p><em>Document that education was provided and understood.</em></p>'
    ),
    'specimen_requirements': (
        'Specimen Requirements',
        '<table class="table table-bordered">'
        '<thead><tr><th>Specimen</th><th>Container</th><th>Volume</th><th>Transport</th><th>Stability</th></tr></thead>'
        '<tbody>'
        '<tr><td>[Type 1]</td><td>[Container]</td><td>[mL]</td><td>[Temp/Time]</td><td>[Hours]</td></tr>'
        '<tr><td>[Type 2]</td><td>[Container]</td><td>[mL]</td><td>[Temp/Time]</td><td>[Hours]</td></tr>'
        '</tbody></table>'
        '<p><strong>Rejection criteria:</strong> Unlabelled, insufficient volume, wrong container, haemolysed, expired.</p>'
    ),
    'reagents': (
        'Reagents & Consumables',
        '<table class="table table-bordered">'
        '<thead><tr><th>Reagent</th><th>Catalogue #</th><th>Storage</th><th>Expiry Check</th></tr></thead>'
        '<tbody>'
        '<tr><td>[Reagent 1]</td><td>[Cat #]</td><td>[Temp]</td><td>Before each use</td></tr>'
        '<tr><td>[Reagent 2]</td><td>[Cat #]</td><td>[Temp]</td><td>Before each use</td></tr>'
        '</tbody></table>'
        '<p><em>Do not use expired reagents. Record lot numbers in the QC log.</em></p>'
    ),
    'result_interpretation': (
        'Result Interpretation',
        '<table class="table table-bordered">'
        '<thead><tr><th>Parameter</th><th>Reference Range</th><th>Critical Values</th></tr></thead>'
        '<tbody>'
        '<tr><td>[Test 1]</td><td>[Range]</td><td>[Critical low / high]</td></tr>'
        '<tr><td>[Test 2]</td><td>[Range]</td><td>[Critical low / high]</td></tr>'
        '</tbody></table>'
        '<p><strong>Critical values</strong> must be reported to the requesting clinician immediately and documented.</p>'
    ),
}


def get_template_choices():
    """Return list of (key, label) tuples for template selection."""
    return [(k, v['label']) for k, v in SOP_TEMPLATES.items()]


def get_template_info():
    """Return list of dicts with template key, label, and icon."""
    return [
        {'key': k, 'label': v['label'], 'icon': v['icon']}
        for k, v in SOP_TEMPLATES.items()
    ]


def gather_context_data(topic='', category_name='', incident_ids=None, capa_ids=None):
    """
    Pull relevant data from the system to enrich the SOP.
    Returns a dict with incidents, capas, and related SOPs.
    """
    from mdh_intranet.incident_log.models import Incident
    from mdh_intranet.capa.models import CAPARecord
    from mdh_intranet.sop_manual.models import SOP

    context = {
        'incidents': [],
        'capas': [],
        'related_sops': [],
    }

    # Pull selected incidents
    if incident_ids:
        context['incidents'] = list(
            Incident.objects.filter(pk__in=incident_ids)
            .values('pk', 'title', 'category', 'severity', 'description',
                    'immediate_action', 'corrective_actions', 'status')
        )

    # Pull selected CAPAs
    if capa_ids:
        context['capas'] = list(
            CAPARecord.objects.filter(pk__in=capa_ids)
            .values('pk', 'title', 'capa_type', 'root_cause_summary',
                    'corrective_action_plan', 'preventive_action_plan', 'status')
        )

    # Find related SOPs by topic keywords
    if topic:
        words = [w for w in topic.split() if len(w) > 3]
        q = Q()
        for word in words[:5]:
            q |= Q(title__icontains=word)
        if q:
            context['related_sops'] = list(
                SOP.objects.filter(q, status='Published')
                .values('pk', 'title', 'version', 'category__name')[:5]
            )

    return context


def generate_sop_content(
    title,
    template_key,
    category_name='',
    author_name='',
    additional_context='',
    incident_ids=None,
    capa_ids=None,
):
    """
    Generate complete SOP content using the selected template and system data.
    Returns HTML-formatted content ready for the SOP content field.
    """
    template = SOP_TEMPLATES.get(template_key, SOP_TEMPLATES['administrative'])
    date_str = timezone.now().strftime('%d %B %Y')
    title_lower = title.lower() if title else 'the procedure'

    # Gather system data
    ctx = gather_context_data(
        topic=title,
        category_name=category_name,
        incident_ids=incident_ids,
        capa_ids=capa_ids,
    )

    format_vars = {
        'title': title,
        'title_lower': title_lower,
        'category': category_name or '[Department]',
        'author': author_name or '[Author]',
        'version': '1.0',
        'date_str': date_str,
    }

    parts = []

    for section_key in template['sections']:
        # We handle header_block separately at the end for clean wrapping
        if section_key == 'header_block':
            continue

        if section_key in SECTION_BUILDERS:
            heading, content_tmpl = SECTION_BUILDERS[section_key]
            try:
                content = content_tmpl.format(**format_vars)
            except (KeyError, IndexError):
                content = content_tmpl
            parts.append(
                f'<h5 class="text-primary fw-bold mt-4 mb-3">'
                f'<i class="fas fa-chevron-right me-2"></i>{heading}</h5>\n\n{content}'
            )

    # ── Append data-driven sections ──

    # Incidents referenced
    if ctx['incidents']:
        incident_rows = ''
        lessons = []
        for inc in ctx['incidents']:
            incident_rows += (
                f"<tr><td>INC-{inc['pk']:03d}</td><td>{inc['title']}</td>"
                f"<td>{inc['severity']}</td><td>{inc['status']}</td></tr>"
            )
            if inc.get('corrective_actions'):
                lessons.append(f"<li><strong>INC-{inc['pk']:03d}:</strong> {inc['corrective_actions'][:200]}</li>")
            if inc.get('immediate_action'):
                lessons.append(f"<li><strong>INC-{inc['pk']:03d} (Immediate):</strong> {inc['immediate_action'][:200]}</li>")

        parts.append(
            '<h5 class="text-primary fw-bold mt-4 mb-3">'
            '<i class="fas fa-exclamation-triangle me-2"></i>'
            'Referenced Incidents</h5>'
            '<p>The following incidents informed the development of this SOP:</p>'
            '<table class="table table-bordered">'
            '<thead><tr><th>ID</th><th>Title</th><th>Severity</th><th>Status</th></tr></thead>'
            f'<tbody>{incident_rows}</tbody></table>'
        )
        if lessons:
            parts.append(
                '<p><strong>Lessons learned incorporated into this SOP:</strong></p>'
                '<ul>' + ''.join(lessons) + '</ul>'
            )

    # CAPAs referenced
    if ctx['capas']:
        capa_rows = ''
        preventive_actions = []
        for c in ctx['capas']:
            capa_rows += (
                f"<tr><td>CAPA-{c['pk']:04d}</td><td>{c['title']}</td>"
                f"<td>{c['capa_type'].title()}</td><td>{c['status'].title()}</td></tr>"
            )
            if c.get('root_cause_summary'):
                preventive_actions.append(f"<li><strong>Root Cause (CAPA-{c['pk']:04d}):</strong> {c['root_cause_summary']}</li>")
            if c.get('preventive_action_plan'):
                preventive_actions.append(
                    f"<li><strong>Preventive Action (CAPA-{c['pk']:04d}):</strong> "
                    f"{c['preventive_action_plan'][:200]}</li>"
                )

        parts.append(
            '<h5 class="text-primary fw-bold mt-4 mb-3">'
            '<i class="fas fa-clipboard-check me-2"></i>'
            'Referenced CAPA Records</h5>'
            '<p>The following CAPA findings were incorporated:</p>'
            '<table class="table table-bordered">'
            '<thead><tr><th>ID</th><th>Title</th><th>Type</th><th>Status</th></tr></thead>'
            f'<tbody>{capa_rows}</tbody></table>'
        )
        if preventive_actions:
            parts.append(
                '<p><strong>Root causes and preventive actions addressed:</strong></p>'
                '<ul>' + ''.join(preventive_actions) + '</ul>'
            )

    # Related SOPs
    if ctx['related_sops']:
        sop_rows = ''
        for s in ctx['related_sops']:
            sop_rows += (
                f"<tr><td>{s['title']}</td><td>v{s['version']}</td>"
                f"<td>{s.get('category__name', '—')}</td></tr>"
            )
        parts.append(
            '<h5 class="text-primary fw-bold mt-4 mb-3">'
            '<i class="fas fa-book me-2"></i>'
            'Related SOPs</h5>'
            '<table class="table table-bordered">'
            '<thead><tr><th>Title</th><th>Version</th><th>Category</th></tr></thead>'
            f'<tbody>{sop_rows}</tbody></table>'
        )

    # Additional context from user
    if additional_context and additional_context.strip():
        parts.append(
            '<h5 class="text-primary fw-bold mt-4 mb-3">'
            '<i class="fas fa-info-circle me-2"></i>'
            'Additional Notes</h5>\n\n'
            f'{additional_context.strip()}'
        )

    # Final assembly with wrapper
    header = ''
    if 'header_block' in template['sections']:
        header = _header_block(
            title, format_vars['category'],
            format_vars['author'], '1.0', date_str
        )

    # Wrap the rest in the formatting div
    content_html = '\n\n'.join(parts)
    return f'{header}\n\n<div class="sop-content-formatted">\n{content_html}\n</div>'
