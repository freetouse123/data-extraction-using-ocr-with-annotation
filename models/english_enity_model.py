from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ============================================================================
# 1) ANALYSIS INSTRUCTION — Header & Metadata
# ============================================================================

class SignatureBlock(BaseModel):
    """Signature block for various sections"""
    name: Optional[str] = None
    date: Optional[date] = None
    signature: Optional[str] = None


class AnalysisInstructionHeader(BaseModel):
    """Header section of the analysis instruction"""
    sample_or_batch_number: Optional[str] = Field(None, description="Sample or batch number")
    test_location: Optional[str] = None
    completion_date: Optional[date] = Field(None, description="Completion date")
    lot_number: Optional[str] = Field(None, description="Lot number")
    lot_name: Optional[str] = Field(None, description="Lot name")
    designation: Optional[str] = Field(None, description="Designation")
    product: Optional[str] = Field(None, description="Product")
    storage_conditions: Optional[str] = Field(None, description="Storage conditions")
    lot_comment: Optional[str] = Field(None, description="Lot comment")
    analysis_type: Optional[str] = Field(None, description="Analysis type")
    acceptance_criteria: Optional[str] = Field(None, description="Requirements / acceptance criteria")
    test_method_id: Optional[str] = Field(None, description="Test / Method ID (e.g., PIVYA-HALT-1)")
    method_version: Optional[str] = Field(None, description="Method / version")
    attachment_reference: Optional[str] = Field(None, description="Attachment reference")
    notes: Optional[str] = Field(None, description="Notes")
    analyst: Optional[SignatureBlock] = None
    reviewer: Optional[SignatureBlock] = None
    printed_by: Optional[str] = Field(None, description="Printed by")
    printed_at: Optional[datetime] = Field(None, description="Print timestamp")
    report_id: Optional[str] = Field(None, description="Report ID")
    revision: Optional[str] = None
    last_modified: Optional[datetime] = Field(None, description="Last modified")
    page_info: Optional[str] = Field(None, description="Page X of Y")


# ============================================================================
# 2) LC P1091 — Protocol Header
# ============================================================================

class InstrumentsBlock(BaseModel):
    """Instruments used in the protocol"""
    hplc_system_id: Optional[str] = None
    ph_meter_id: Optional[str] = None
    ph_meter_valid_until: Optional[date] = None
    balance_id: Optional[str] = None
    balance_valid_until: Optional[date] = None
    timer_id: Optional[str] = None
    timer_valid_until: Optional[date] = None
    ultrasonic_bath_id: Optional[str] = None
    ultrasonic_bath_valid_until: Optional[date] = None
    column_number: Optional[str] = None


class ProtocolHeader(BaseModel):
    """LC P1091 protocol header information"""
    protocol_number: Optional[str] = None
    released_by: Optional[str] = None
    date: Optional[date] = None
    analyst: Optional[str] = None
    method_used: Optional[str] = None
    product: Optional[str] = None
    analysis_type: Optional[str] = None
    estimated_analysis_time: Optional[str] = None
    estimated_compilation_time: Optional[str] = None
    estimated_review_time: Optional[str] = None
    instruments: Optional[InstrumentsBlock] = None
    not_applicable: Optional[bool] = None
    reviewed_by: Optional[SignatureBlock] = None


# ============================================================================
# 3) REAGENTS — Inventory & Attributes
# ============================================================================

class Reagent(BaseModel):
    """Individual reagent information"""
    reagent_id: Optional[str] = None
    name: Optional[str] = None
    standard_number: Optional[str] = None
    expiry_date: Optional[date] = None
    assay_content: Optional[str] = None
    tapping_date: Optional[date] = None
    catalog_number: Optional[str] = None
    reagent_number: Optional[str] = None
    manufacturer: Optional[str] = None
    lot_number: Optional[str] = None


class ReagentsList(BaseModel):
    """Collection of all reagents"""
    reagent_i_api_standard: Optional[Reagent] = None
    reagent_ii_impurity_c: Optional[Reagent] = None
    reagent_iii_milliq_water: Optional[Reagent] = None
    reagent_iv_acetonitrile: Optional[Reagent] = None
    reagent_v_kh2po4: Optional[Reagent] = None
    reagent_vi_phosphoric_acid: Optional[Reagent] = None
    reagent_vii_teahs: Optional[Reagent] = None
    reagent_viii_tmahs: Optional[Reagent] = None
    reagent_ix_phosphoric_acid_1m: Optional[Reagent] = None
    reagent_x_phosphate_buffer: Optional[Reagent] = None
    reagent_xi_mobile_phase_solvent_mixture: Optional[Reagent] = None
    reagent_xii_mobile_phase: Optional[Reagent] = None
    reagent_xiii_sample_solvent_mixture: Optional[Reagent] = None
    reagent_xiv_membrane_filter: Optional[Reagent] = None
    reagent_xv_syringe_filter: Optional[Reagent] = None


# ============================================================================
# 4) PREPARATION RECORDS
# ============================================================================

class WeighingRecord(BaseModel):
    """Embedded weighing record"""
    balance_id: Optional[str] = None
    sample_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    weight_g: Optional[float] = None


class pHMeterRecord(BaseModel):
    """pH meter reading record"""
    device_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    run_number: Optional[str] = None
    temperature_c: Optional[float] = None
    measured_ph: Optional[float] = None


class PhosphoricAcidPreparation(BaseModel):
    """1.0 M Phosphoric Acid preparation"""
    acid_volume_ml: Optional[float] = None
    water_volume_ml: Optional[float] = None
    signed_by: Optional[SignatureBlock] = None


class PhosphateBufferPreparation(BaseModel):
    """Phosphate buffer pH 3.0 preparation"""
    kh2po4_mass_g: Optional[float] = None
    water_volume_ml: Optional[float] = None
    final_volume_ml: Optional[float] = None
    target_ph: Optional[float] = None
    measured_ph: Optional[float] = None
    filtration_performed: Optional[bool] = None
    weighing_record: Optional[WeighingRecord] = None
    ph_meter_record: Optional[pHMeterRecord] = None
    signed_by: Optional[SignatureBlock] = None


class SolventMixtureMobilePhase(BaseModel):
    """Solvent mixture for mobile phase"""
    acetonitrile_volume_ml: Optional[float] = None
    buffer_volume_ml: Optional[float] = None
    signed_by: Optional[SignatureBlock] = None


class MobilePhasePreparation(BaseModel):
    """Final mobile phase preparation"""
    teahs_mass_g: Optional[float] = None
    tmahs_mass_g: Optional[float] = None
    final_volume_ml: Optional[float] = None
    degassing_time_min: Optional[float] = None
    weighing_records: Optional[List[WeighingRecord]] = None
    signed_by: Optional[SignatureBlock] = None


class SolventMixtureSamples(BaseModel):
    """Solvent mixture for samples"""
    acetonitrile_volume_ml: Optional[float] = None
    water_volume_ml: Optional[float] = None
    signed_by: Optional[SignatureBlock] = None


class PreparationRecords(BaseModel):
    """All preparation records"""
    phosphoric_acid_1m: Optional[PhosphoricAcidPreparation] = None
    phosphate_buffer_ph3: Optional[PhosphateBufferPreparation] = None
    solvent_mixture_mobile_phase: Optional[SolventMixtureMobilePhase] = None
    mobile_phase: Optional[MobilePhasePreparation] = None
    solvent_mixture_samples: Optional[SolventMixtureSamples] = None


# ============================================================================
# 5) STANDARDS
# ============================================================================

class ReferenceSolutionA(BaseModel):
    mass_api_mg: Optional[float] = None
    final_volume_ml: Optional[float] = None
    balance_id: Optional[str] = None
    sample_ids: Optional[List[str]] = None
    timestamps: Optional[List[datetime]] = None
    weighing_record: Optional[WeighingRecord] = None
    signed_by: Optional[SignatureBlock] = None


class ReferenceSolutionB(BaseModel):
    aliquot_volumes_ml: Optional[List[float]] = None
    final_volumes_ml: Optional[List[float]] = None
    signed_by: Optional[SignatureBlock] = None


class ReferenceSolutionC(BaseModel):
    api_mass_mg: Optional[float] = None
    impurity_c_mass_mg: Optional[float] = None
    final_volume_ml: Optional[float] = None
    notes: Optional[str] = None
    signed_by: Optional[SignatureBlock] = None


class ReferenceSolutionD(BaseModel):
    aliquot_volumes_ml: Optional[List[float]] = None
    final_volume_ml: Optional[float] = None
    signed_by: Optional[SignatureBlock] = None


class Standards(BaseModel):
    reference_solution_a: Optional[ReferenceSolutionA] = None
    reference_solution_b: Optional[ReferenceSolutionB] = None
    reference_solution_c: Optional[ReferenceSolutionC] = None
    reference_solution_d: Optional[ReferenceSolutionD] = None


# ============================================================================
# 6) TEST SOLUTIONS
# ============================================================================

class TestSolutionA(BaseModel):
    sample_id: Optional[str] = None
    number_of_tablets: Optional[int] = None
    solvent_mixture_volume_ml: Optional[float] = None
    sample_volume_ml: Optional[float] = None
    additional_solvent_volume_ml: Optional[float] = None
    prepared_by: Optional[SignatureBlock] = None


class TestSolutionB(BaseModel):
    sample_id: Optional[str] = None
    number_of_tablets: Optional[int] = None
    solvent_volumes_ml: Optional[List[float]] = None
    prepared_by: Optional[SignatureBlock] = None
    vial_placement_verified_by: Optional[SignatureBlock] = None


class TestSolutions(BaseModel):
    test_solution_a_runs: Optional[List[TestSolutionA]] = None
    test_solution_b_runs: Optional[List[TestSolutionB]] = None


# ============================================================================
# 7) SYSTEM SUITABILITY TEST (SST)
# ============================================================================

class SSTCriterion(BaseModel):
    criterion_name: Optional[str] = None
    requirement: Optional[str] = None
    status: Optional[str] = None
    retention_time_tolerance_min: Optional[float] = None
    rsd_limit_percent: Optional[float] = None
    resolution_limit: Optional[float] = None
    signal_to_noise_limit: Optional[float] = None


class SystemSuitabilityTest(BaseModel):
    blank_interference_check: Optional[SSTCriterion] = None
    stability_reference_b1_initial: Optional[SSTCriterion] = None
    stability_reference_a1_initial: Optional[SSTCriterion] = None
    repeatability_b1_initial: Optional[SSTCriterion] = None
    repeatability_a1_initial: Optional[SSTCriterion] = None
    repeatability_b1_full_sequence: Optional[SSTCriterion] = None
    repeatability_a1_full_sequence: Optional[SSTCriterion] = None
    resolution_reference_solution_c: Optional[SSTCriterion] = None
    loq_reference_solution_d: Optional[SSTCriterion] = None
    sst_overall_status: Optional[str] = None
    compiled_by: Optional[SignatureBlock] = None
    sample_numbers_confirmed: Optional[bool] = None
    raw_data_archived_reference: Optional[str] = None
    raw_data_archived_signed_by: Optional[SignatureBlock] = None
    reviewed_by: Optional[SignatureBlock] = None


# ============================================================================
# 8) DOCUMENT TRACEABILITY
# ============================================================================

class DocumentTraceability(BaseModel):
    version: Optional[str] = None
    site: Optional[str] = None
    not_applicable_markers: Optional[List[str]] = None


# ============================================================================
# MAIN DOCUMENT MODEL
# ============================================================================

class LCAnalyticalDocumentEnglish(BaseModel):
    """
    Complete Pydantic model for LC analytical raw data document extraction.
    """
    analysis_instruction: Optional[AnalysisInstructionHeader] = None
    protocol_header: Optional[ProtocolHeader] = None
    reagents: Optional[ReagentsList] = None
    preparation_records: Optional[PreparationRecords] = None
    standards: Optional[Standards] = None
    test_solutions: Optional[TestSolutions] = None
    system_suitability_test: Optional[SystemSuitabilityTest] = None
    traceability: Optional[DocumentTraceability] = None
