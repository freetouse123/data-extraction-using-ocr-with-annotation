from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date


# ============================================================================
# 1) ANALYSINSTRUKTION (Analysis Instruction) — Header & Metadata
# ============================================================================

class SignatureBlock(BaseModel):
    """Signature block for various sections"""
    name: Optional[str] = None
    Date: Optional[date] = None
    signature: Optional[str] = None


class AnalysisInstructionHeader(BaseModel):
    """Header section of the analysis instruction"""
    provnr: Optional[str] = Field(None, description="Sample/Batch number")
    test_location: Optional[str] = None
    fardig_datum: Optional[date] = Field(None, description="Completion date")
    lot_nummer: Optional[str] = Field(None, description="Lot number")
    lot_namn: Optional[str] = Field(None, description="Lot name")
    benamning: Optional[str] = Field(None, description="Designation")
    produkt: Optional[str] = Field(None, description="Product")
    forvaring: Optional[str] = Field(None, description="Storage conditions")
    lot_kommentar: Optional[str] = Field(None, description="Lot comment")
    analys: Optional[str] = Field(None, description="Analysis type")
    krav: Optional[str] = Field(None, description="Requirements/Acceptance criteria")
    test_method_id: Optional[str] = Field(None, description="Test/Method ID (e.g., PIVYA-HALT-1)")
    metod_version: Optional[str] = Field(None, description="Method/version (e.g., P1091/1)")
    bilaga: Optional[str] = Field(None, description="Attachment (e.g., LC 25-324)")
    anteckning: Optional[str] = Field(None, description="Notes")
    analytiker: Optional[SignatureBlock] = None
    granskare: Optional[SignatureBlock] = Field(None, description="Reviewer")
    utskrivet_av: Optional[str] = Field(None, description="Printed by")
    utskrivet: Optional[datetime] = Field(None, description="Print timestamp")
    rapportid: Optional[str] = Field(None, description="Report ID")
    revision: Optional[str] = None
    senast_andrad: Optional[datetime] = Field(None, description="Last modified")
    sida: Optional[str] = Field(None, description="Page X of Y")


# ============================================================================
# 2) LC P1091 — Protocol Header
# ============================================================================

class InstrumentsBlock(BaseModel):
    """Instruments used in the protocol"""
    hplc_system_id: Optional[str] = Field(None, description="HPLC system ID")
    ph_meter_stamp: Optional[str] = Field(None, description="pH meter stamp")
    ph_meter_valid_until: Optional[date] = Field(None, description="pH meter valid until")
    vag_stamp: Optional[str] = Field(None, description="Balance stamp")
    vag_valid_until: Optional[date] = Field(None, description="Balance valid until")
    timer: Optional[str] = None
    timer_valid_until: Optional[date] = Field(None, description="Timer valid until")
    ultraljudsbad: Optional[str] = Field(None, description="Ultrasound bath")
    ultraljudsbad_valid_until: Optional[date] = Field(None, description="Ultrasound bath valid until")
    kolonn_nr: Optional[str] = Field(None, description="Column number")


class ProtocolHeader(BaseModel):
    """LC P1091 Protocol header information"""
    protokollnr: Optional[str] = Field(None, description="Protocol number (e.g., LC25-324)")
    utlamnad_av: Optional[str] = Field(None, description="Released by")
    datum: Optional[date] = None
    analytiker: Optional[str] = None
    anvand_metod: Optional[str] = Field(None, description="Method used (e.g., P1091)")
    produkt: Optional[str] = Field(None, description="Product (e.g., Pirmecillinam)")
    analys: Optional[str] = Field(None, description="Analysis type (e.g., Halt och nedbrytning)")
    uppskattad_tid_analys: Optional[str] = Field(None, description="Estimated time - analysis")
    uppskattad_tid_sammanstallning: Optional[str] = Field(None, description="Estimated time - compilation")
    uppskattad_tid_granskning: Optional[str] = Field(None, description="Estimated time - review")
    instruments: Optional[InstrumentsBlock] = None
    ej_tillampligt: Optional[bool] = Field(None, description="Not applicable marker")
    granskad_av: Optional[SignatureBlock] = Field(None, description="Reviewed by")


# ============================================================================
# 3) REAGENS (Reagents I–XV) — Inventory & Attributes
# ============================================================================

class Reagent(BaseModel):
    """Individual reagent information"""
    reagent_id: Optional[str] = Field(None, description="Reagent identifier (I-XV)")
    name: Optional[str] = Field(None, description="Reagent name")
    standardnr: Optional[str] = Field(None, description="Standard number")
    utg_datum: Optional[date] = Field(None, description="Expiry date")
    halt: Optional[str] = Field(None, description="Assay/content")
    tappningsdatum: Optional[date] = Field(None, description="Tapping date")
    knr: Optional[str] = Field(None, description="Catalog number")
    reagensnr: Optional[str] = Field(None, description="Reagent number")
    fabrikat: Optional[str] = Field(None, description="Manufacturer")
    lot_nr: Optional[str] = Field(None, description="Lot number")
    tillverkare: Optional[str] = Field(None, description="Manufacturer")


class ReagentsList(BaseModel):
    """Collection of all reagents (I-XV)"""
    reagent_i_pivmecillinam_ws: Optional[Reagent] = None
    reagent_ii_imp_c: Optional[Reagent] = None
    reagent_iii_milliq_water: Optional[Reagent] = None
    reagent_iv_acetonitril: Optional[Reagent] = None
    reagent_v_kh2po4: Optional[Reagent] = None
    reagent_vi_phosphoric_acid: Optional[Reagent] = None
    reagent_vii_teahs: Optional[Reagent] = None
    reagent_viii_tmahs: Optional[Reagent] = None
    reagent_ix_1m_phosphoric_acid: Optional[Reagent] = None
    reagent_x_phosphate_buffer: Optional[Reagent] = None
    reagent_xi_solvent_mixture_mobile: Optional[Reagent] = None
    reagent_xii_mobilfas: Optional[Reagent] = None
    reagent_xiii_solvent_mixture_samples: Optional[Reagent] = None
    reagent_xiv_membrane_filter: Optional[Reagent] = None
    reagent_xv_syringe_filter: Optional[Reagent] = None


# ============================================================================
# 4) PREPARATION RECORDS — Buffers & Mobile Phases
# ============================================================================

class WeighingProtocol(BaseModel):
    """Embedded weighing slip data"""
    balance_id: Optional[str] = None
    sample_id: Optional[str] = None
    datetime_stamp: Optional[datetime] = None
    weight_g: Optional[float] = Field(None, description="Weight in grams")


class pHMeterLog(BaseModel):
    """pH meter reading log"""
    device_label: Optional[str] = None
    datetime: Optional[datetime] = None
    run_number: Optional[str] = None
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    recorded_ph: Optional[float] = Field(None, description="Recorded pH value")


class PhosphoricAcidPreparation(BaseModel):
    """IX — 1.0 M Fosforsyra preparation"""
    volume_acid_ml: Optional[float] = Field(None, description="Volume of acid in ml")
    volume_milliq_ml: Optional[float] = Field(None, description="Volume of MilliQ water in ml")
    date_sign: Optional[SignatureBlock] = None


class PhosphateBufferPreparation(BaseModel):
    """X — Fosfatbuffert pH 3.0 preparation"""
    mass_kh2po4_g: Optional[float] = Field(None, description="Mass of KH2PO4 in grams")
    volume_water_ml: Optional[float] = Field(None, description="Volume of water in ml")
    final_volume_ml: Optional[float] = Field(None, description="Final volume in ml")
    ph_target: Optional[float] = Field(None, description="Target pH")
    ph_actual: Optional[float] = Field(None, description="Actual pH measured")
    filtration_performed: Optional[bool] = None
    weighing_protocol: Optional[WeighingProtocol] = None
    ph_meter_log: Optional[pHMeterLog] = None
    date_sign: Optional[SignatureBlock] = None


class SolventMixtureMobilePhase(BaseModel):
    """XI — Solvent mixture for mobile phase (38:62)"""
    volume_acetonitril_ml: Optional[float] = Field(None, description="Volume of acetonitrile in ml")
    volume_buffer_ml: Optional[float] = Field(None, description="Volume of buffer in ml")
    date_sign: Optional[SignatureBlock] = None


class MobileFasPreparation(BaseModel):
    """XII — Mobilfas (final mobile phase) preparation"""
    mass_teahs_g: Optional[float] = Field(None, description="Mass of TEAHS in grams")
    mass_tmahs_g: Optional[float] = Field(None, description="Mass of TMAHS in grams")
    final_volume_ml: Optional[float] = Field(None, description="Final volume in ml")
    degassing_time_min: Optional[float] = Field(None, description="Degassing time in minutes")
    weighing_slips: Optional[List[WeighingProtocol]] = None
    date_sign: Optional[SignatureBlock] = None


class SolventMixtureSamples(BaseModel):
    """XIII — Solvent mixture for samples"""
    volume_acetonitril_ml: Optional[float] = Field(None, description="Volume of acetonitrile in ml")
    volume_milliq_ml: Optional[float] = Field(None, description="Volume of MilliQ water in ml")
    date_sign: Optional[SignatureBlock] = None


class PreparationRecords(BaseModel):
    """All buffer and mobile phase preparations"""
    ix_phosphoric_acid: Optional[PhosphoricAcidPreparation] = None
    x_phosphate_buffer: Optional[PhosphateBufferPreparation] = None
    xi_solvent_mixture_mobile: Optional[SolventMixtureMobilePhase] = None
    xii_mobilfas: Optional[MobileFasPreparation] = None
    xiii_solvent_mixture_samples: Optional[SolventMixtureSamples] = None


# ============================================================================
# 5) STANDARDER (Standards / Reference Solutions)
# ============================================================================

class ReferenceSolutionA(BaseModel):
    """3.1.1 — Reference solution a (a1, a2)"""
    mass_api_mg: Optional[float] = Field(None, description="Mass of API in mg")
    final_volume_ml: Optional[float] = Field(None, description="Final volume in ml")
    balance_id: Optional[str] = None
    sample_ids: Optional[List[str]] = None
    datetime_stamps: Optional[List[datetime]] = None
    weighing_protocol: Optional[WeighingProtocol] = None
    date_sign: Optional[SignatureBlock] = None


class ReferenceSolutionB(BaseModel):
    """3.1.2 — Reference solution b (b1, b2)"""
    aliquot_volumes_ml: Optional[List[float]] = Field(None, description="Aliquot volumes in ml")
    dilution_final_volumes_ml: Optional[List[float]] = Field(None, description="Dilution final volumes in ml")
    date_sign: Optional[SignatureBlock] = None


class ReferenceSolutionC(BaseModel):
    """3.1.3 — Reference solution c"""
    mass_api_mg: Optional[float] = Field(None, description="Mass of API in mg")
    mass_imp_c_mg: Optional[float] = Field(None, description="Mass of Imp C in mg")
    final_volume_ml: Optional[float] = Field(None, description="Final volume in ml")
    vial_preparation_note: Optional[str] = None
    date_sign: Optional[SignatureBlock] = None


class ReferenceSolutionD(BaseModel):
    """3.1.4 — Reference solution d"""
    aliquot_volumes_ml: Optional[List[float]] = Field(None, description="Aliquot volumes in ml")
    final_volume_ml: Optional[float] = Field(None, description="Final volume in ml")
    date_sign: Optional[SignatureBlock] = None


class Standards(BaseModel):
    """All reference solutions"""
    reference_solution_a: Optional[ReferenceSolutionA] = None
    reference_solution_b: Optional[ReferenceSolutionB] = None
    reference_solution_c: Optional[ReferenceSolutionC] = None
    reference_solution_d: Optional[ReferenceSolutionD] = None


# ============================================================================
# 6) TEST SOLUTIONS (Samples) — 3.2.1/3.2.2 & 3.2.3/3.2.4
# ============================================================================

class TestSolutionA(BaseModel):
    """3.2.1/3.2.2 — Test solution a"""
    provnummer: Optional[str] = Field(None, description="Sample ID")
    antal_tabletter: Optional[int] = Field(None, description="Number of tablets")
    volym_solvent_mixture_ml: Optional[float] = Field(None, description="Volume of solvent mixture in ml")
    volym_prov_ml: Optional[float] = Field(None, description="Sample volume in ml")
    additional_solvent_volume_ml: Optional[float] = Field(None, description="Additional solvent volume in ml")
    prover_upparbetades_av: Optional[SignatureBlock] = Field(None, description="Samples prepared by")


class TestSolutionB(BaseModel):
    """3.2.3/3.2.4 — Test solution b"""
    provnummer: Optional[str] = Field(None, description="Sample ID")
    antal_tabletter: Optional[int] = Field(None, description="Number of tablets")
    volym_solvent_ml_entries: Optional[List[float]] = Field(None, description="Solvent volume entries in ml")
    prover_upparbetades_av: Optional[SignatureBlock] = Field(None, description="Samples prepared by")
    dubbelkontroll_vialplacering: Optional[SignatureBlock] = Field(None, description="Double check of vial placement")


class TestSolutions(BaseModel):
    """All test solutions"""
    test_solution_a_runs: Optional[List[TestSolutionA]] = Field(None, description="Test solution a for multiple runs")
    test_solution_b_runs: Optional[List[TestSolutionB]] = Field(None, description="Test solution b for multiple runs")


# ============================================================================
# 7) SYSTEMTEST (System Suitability Tests, SST) — Criteria & Status
# ============================================================================

class SSTCriterion(BaseModel):
    """Individual SST criterion with status"""
    criterion_name: Optional[str] = None
    requirement: Optional[str] = Field(None, description="Requirement or tolerance")
    status: Optional[str] = Field(None, description="Godkänd (Approved) / Icke godkänd (Not approved)")
    rt_tolerance_min: Optional[float] = Field(None, description="Retention time tolerance in minutes")
    rsd_limit_percent: Optional[float] = Field(None, description="RSD limit in percent")
    resolution_limit: Optional[float] = Field(None, description="Resolution limit (Rs)")
    signal_to_noise_limit: Optional[float] = Field(None, description="Signal to noise limit (S/N)")


class SystemSuitabilityTest(BaseModel):
    """Complete SST record"""
    blank_no_interfering_peaks: Optional[SSTCriterion] = None
    stability_ref_solution_b1_first_4: Optional[SSTCriterion] = None
    stability_ref_solution_a1_first_6: Optional[SSTCriterion] = None
    repeatability_b1_first_4: Optional[SSTCriterion] = None
    repeatability_a1_first_6: Optional[SSTCriterion] = None
    repeatability_b1_full_sequence: Optional[SSTCriterion] = None
    repeatability_a1_full_sequence: Optional[SSTCriterion] = None
    resolution_ref_solution_c: Optional[SSTCriterion] = None
    loq_ref_solution_d: Optional[SSTCriterion] = None
    sst_summary_status: Optional[str] = Field(None, description="SST Godkänd / SST Icke godkänd")
    systemtest_sammanstallad_av: Optional[SignatureBlock] = Field(None, description="SST compiled by")
    provnummer_confirmed: Optional[bool] = Field(None, description="Confirmation that sample numbers filled in column binder")
    radata_arkiverat: Optional[str] = Field(None, description="Raw data archived reference")
    radata_arkiverat_date_sign: Optional[SignatureBlock] = None
    granskad_av: Optional[SignatureBlock] = Field(None, description="Reviewed by")


# ============================================================================
# 8) SIGN-OFFS & TRACEABILITY
# ============================================================================

class DocumentTraceability(BaseModel):
    """Document-wide traceability and versioning"""
    version: Optional[str] = Field(None, description="Document version (e.g., Version 1)")
    site: Optional[str] = Field(None, description="Site (e.g., Recipharm Strängnäs AB)")
    ej_tillampligt_markers: Optional[List[str]] = Field(None, description="Not applicable (NA) markers throughout document")


# ============================================================================
# MAIN DOCUMENT MODEL
# ============================================================================

class LCAnalyticalDocumentSwedish(BaseModel):
    """
    Complete Pydantic model for LC analytical raw data document extraction.
    Captures all sections from analysis instruction through system suitability testing.
    """
    
    # Section 1: Analysis Instruction
    analysis_instruction: Optional[AnalysisInstructionHeader] = None
    
    # Section 2: Protocol Header
    protocol_header: Optional[ProtocolHeader] = None
    
    # Section 3: Reagents
    reagents: Optional[ReagentsList] = None
    
    # Section 4: Preparation Records
    preparation_records: Optional[PreparationRecords] = None
    
    # Section 5: Standards
    standards: Optional[Standards] = None
    
    # Section 6: Test Solutions
    test_solutions: Optional[TestSolutions] = None
    
    # Section 7: System Suitability Test
    system_suitability_test: Optional[SystemSuitabilityTest] = None
    
    # Section 8: Document Traceability
    traceability: Optional[DocumentTraceability] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "analysis_instruction": {
                    "provnr": "2024-001",
                    "test_location": "Lab A",
                    "produkt": "Pirmecillinam",
                    "analys": "Halt och nedbrytning"
                },
                "protocol_header": {
                    "protokollnr": "LC25-324",
                    "anvand_metod": "P1091",
                    "produkt": "Pirmecillinam"
                }
            }
        }