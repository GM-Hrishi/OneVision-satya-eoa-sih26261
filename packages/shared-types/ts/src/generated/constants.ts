// GENERATED from packages/shared-types/schemas by scripts/generate.mjs. Do not edit.

export const EVENT_SPEC = "satya.event/1" as const;

export const VERIFICATION_LABELS = [
  "verified",
  "mismatch_detected",
  "expired",
  "verification_pending",
  "source_unavailable",
  "manual_review_required"
] as const;

export const LABEL_PRECEDENCE = [
  "mismatch_detected",
  "expired",
  "manual_review_required",
  "source_unavailable",
  "verification_pending",
  "verified"
] as const;

export const INBOUND_EVENT_TYPES = [
  "application.precheck_requested",
  "application.submitted",
  "application.reopened",
  "committee.scrutiny_constituted",
  "committee.rescrutiny_constituted",
  "deficiency.posted",
  "evc.selection_round_opened",
  "evc.selection_recorded",
  "evc.scheduled",
  "evc.media_submitted",
  "hearing.scheduled",
  "compliance.submitted",
  "decision.recorded",
  "eoa.letter_issued",
  "enrolment.uploaded",
  "faculty.record_changed",
  "complaint.referred"
] as const;

export const OUTBOUND_EVENT_TYPES = [
  "precheck.completed",
  "case.validation_completed",
  "case.evidence_pack_ready",
  "evc.selection_proposal_ready",
  "evc.checklist_ready",
  "evc.media_check_completed",
  "case.dossier_ready",
  "document.status_changed",
  "alert.raised",
  "observation.recorded",
  "observation.withdrawn",
  "clarification.requested",
  "referral.recommended",
  "deficiency.candidates_proposed",
  "ingest.failed"
] as const;

export const EVENT_TYPES = [
  "application.precheck_requested",
  "application.submitted",
  "application.reopened",
  "committee.scrutiny_constituted",
  "committee.rescrutiny_constituted",
  "deficiency.posted",
  "evc.selection_round_opened",
  "evc.selection_recorded",
  "evc.scheduled",
  "evc.media_submitted",
  "hearing.scheduled",
  "compliance.submitted",
  "decision.recorded",
  "eoa.letter_issued",
  "enrolment.uploaded",
  "faculty.record_changed",
  "complaint.referred",
  "precheck.completed",
  "case.validation_completed",
  "case.evidence_pack_ready",
  "evc.selection_proposal_ready",
  "evc.checklist_ready",
  "evc.media_check_completed",
  "case.dossier_ready",
  "document.status_changed",
  "alert.raised",
  "observation.recorded",
  "observation.withdrawn",
  "clarification.requested",
  "referral.recommended",
  "deficiency.candidates_proposed",
  "ingest.failed"
] as const;

export const DISPOSITION_ACTIONS = [
  "accept",
  "override",
  "escalate_clarify",
  "escalate_refer",
  "escalate_manual"
] as const;

export const RISK_BANDS = [
  "high",
  "medium",
  "low"
] as const;

export const YOY_VERDICTS = [
  "explained",
  "discrepancy"
] as const;

export const ROLES = [
  "RB",
  "SC",
  "EV",
  "HC",
  "RA",
  "AU",
  "INS"
] as const;

export const ALERT_TYPES = [
  "missing_info",
  "expired",
  "pending_source",
  "suspected_anomaly",
  "unresolved",
  "role"
] as const;

export const ALERT_SUBTYPES = {
  "missing_info": [
    "document_missing",
    "field_missing",
    "category_line_missing",
    "uploader_dsc_missing"
  ],
  "expired": [
    "document_expired",
    "expiring_soon",
    "partial_oc_limit_reached",
    "signing_cert_expired"
  ],
  "pending_source": [
    "source_pending_overdue",
    "source_unavailable",
    "trust_anchor_revalidation"
  ],
  "suspected_anomaly": [
    "affidavit_diff",
    "signature_integrity",
    "signature_image_only",
    "stamp_chronology",
    "identity_graph",
    "yoy_discrepancy",
    "document_misclassified",
    "media_reuse"
  ],
  "unresolved": [
    "flag_undisposed_overdue",
    "manual_task_overdue",
    "clarification_overdue",
    "compliance_window_expiring",
    "compliance_window_lapsed"
  ],
  "role": [
    "case_assigned",
    "sitting_scheduled",
    "evc_scheduled",
    "hearing_scheduled",
    "selection_round_opened"
  ]
} as const;

export const SNAPSHOT_FIELD_HANDLING = {
  "ay": "K",
  "captured_at": "K",
  "basic": "K",
  "basic.application_id": "K",
  "basic.permanent_id": "K",
  "basic.institution_type": "K",
  "basic.status": "K",
  "basic.application_date": "K",
  "basic.submission_date": "K",
  "basic.regional_office": "K",
  "basic.overall_deficiency": "K",
  "trust": "K",
  "trust.name": "K",
  "trust.registration_ref": "K",
  "trustees": "K",
  "trustees[].name": "T",
  "trustees[].role": "K",
  "trustees[].tenure_from": "K",
  "trustees[].tenure_to": "K",
  "authorised_signatory": "K",
  "authorised_signatory.name": "T",
  "authorised_signatory.designation": "K",
  "courses": "K",
  "courses[].programme": "K",
  "courses[].level": "K",
  "courses[].course": "K",
  "courses[].intake_approved": "K",
  "courses[].intake_approved[].ay": "K",
  "courses[].intake_approved[].intake": "K",
  "courses[].intake_applied": "K",
  "courses[].faculty_required": "K",
  "courses[].faculty_actual": "K",
  "courses[].nri_status": "K",
  "courses[].international_students_status": "K",
  "courses[].nba_status": "K",
  "land": "K",
  "land.total_area": "K",
  "land.unit": "K",
  "land.pieces": "K",
  "land.max_distance_km": "K",
  "land.land_use_certificate_issuer": "K",
  "land.land_use_certificate_date": "K",
  "land.coordinates": "K",
  "land.coordinates.lat": "K",
  "land.coordinates.lat.deg": "K",
  "land.coordinates.lat.min": "K",
  "land.coordinates.lat.sec": "K",
  "land.coordinates.lat.hemisphere": "K",
  "land.coordinates.lon": "K",
  "land.coordinates.lon.deg": "K",
  "land.coordinates.lon.min": "K",
  "land.coordinates.lon.sec": "K",
  "land.coordinates.lon.hemisphere": "K",
  "land.deeds": "K",
  "land.deeds[].holder": "T",
  "land.deeds[].document_no": "T",
  "land.deeds[].registration_date": "K",
  "land.deeds[].plot_no": "K",
  "land.deeds[].village_district": "K",
  "land.deeds[].area_acre": "K",
  "buildings": "K",
  "buildings[].block": "K",
  "buildings[].sanctioned_area_m2": "K",
  "buildings[].constructed_area_m2": "K",
  "buildings[].approving_authority": "K",
  "buildings[].approval_date": "K",
  "rooms": "K",
  "rooms.administrative": "K",
  "rooms.administrative[].room_id": "K",
  "rooms.administrative[].room_type": "K",
  "rooms.administrative[].carpet_area_m2": "K",
  "rooms.administrative[].flooring": "K",
  "rooms.administrative[].walls_painting": "K",
  "rooms.administrative[].electrification": "K",
  "rooms.amenities": "K",
  "rooms.amenities[].room_id": "K",
  "rooms.amenities[].room_type": "K",
  "rooms.amenities[].carpet_area_m2": "K",
  "rooms.amenities[].flooring": "K",
  "rooms.amenities[].walls_painting": "K",
  "rooms.amenities[].electrification": "K",
  "rooms.instructional": "K",
  "rooms.instructional[].room_id": "K",
  "rooms.instructional[].room_type": "K",
  "rooms.instructional[].carpet_area_m2": "K",
  "rooms.instructional[].flooring": "K",
  "rooms.instructional[].walls_painting": "K",
  "rooms.instructional[].electrification": "K",
  "rooms.instructional_common": "K",
  "rooms.instructional_common[].room_id": "K",
  "rooms.instructional_common[].room_type": "K",
  "rooms.instructional_common[].carpet_area_m2": "K",
  "rooms.instructional_common[].flooring": "K",
  "rooms.instructional_common[].walls_painting": "K",
  "rooms.instructional_common[].electrification": "K",
  "facilities": "R",
  "facilities.items": "R",
  "facilities.items[].name": "R",
  "facilities.items[].value": "R",
  "committees": "R",
  "committees.items": "R",
  "committees.items[].name": "R",
  "committees.items[].value": "R",
  "bank": "K",
  "bank.bank_name": "K",
  "bank.ifsc": "K",
  "finance": "K",
  "finance.fy": "K",
  "finance.income_total_paise": "K",
  "finance.expenditure_total_paise": "K",
  "finance.heads": "K",
  "finance.heads[].head": "K",
  "finance.heads[].income_paise": "K",
  "finance.heads[].expenditure_paise": "K",
  "declaration": "K",
  "declaration.items": "K",
  "declaration.items.a": "K",
  "declaration.items.b": "K",
  "declaration.items.c": "K",
  "declaration.items.d": "K",
  "declaration.items.e": "K",
  "declaration.items.f": "K",
  "declaration.category_list": "K",
  "faculty": "K",
  "faculty[].faculty_id": "T",
  "faculty[].designation": "K",
  "faculty[].appointment_type": "K",
  "faculty[].programme": "K",
  "faculty[].department": "K",
  "faculty[].date_of_joining": "K",
  "faculty[].highest_qualification_level": "K",
  "faculty[].relieved_date": "K",
  "faculty[].is_duplicate": "R",
  "faculty[].pan_validation": "R",
  "faculty[].record_status": "R",
  "deficiency_report": "R",
  "deficiency_report.template_year": "R",
  "deficiency_report.sections": "R",
  "deficiency_report.sections[].section": "R",
  "deficiency_report.sections[].deficiency": "R",
  "deficiency_report.overall": "R",
  "deficiency_report.principal_eligibility": "R"
} as const;

export const SNAPSHOT_TOKEN_FIELDS = {
  "trustees[].name": "trustee_token",
  "authorised_signatory.name": "signatory_token",
  "land.deeds[].holder": "holder_token",
  "land.deeds[].document_no": "deed_token",
  "faculty[].faculty_id": "faculty_token"
} as const;

export const SNAPSHOT_REJECTED_FIELDS = [
  "hoi",
  "hoi.name",
  "hoi.dob",
  "hoi.contact",
  "hoi.pan",
  "hoi.address",
  "bank.account_number",
  "faculty[].pan",
  "faculty[].dob",
  "faculty[].name",
  "faculty[].mobile",
  "faculty[].email"
] as const;

export const SCHEMA_TITLES = [
  "AffidavitDiff",
  "Alert",
  "ApplicationSnapshot",
  "CaseVerification",
  "Disposition",
  "Document",
  "EventEnvelope",
  "Flag",
  "RiskBand",
  "VerificationLabel",
  "VerificationResult",
  "YoyVerdict"
] as const;
