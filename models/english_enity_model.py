from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date


class AnalysisInstruction(BaseModel):
    test_id: str = Field(..., description="Test or analysis number")
    test_location: Optional[str]
    completion_date: Optional[date]

    lot_number: Optional[str]
    lot_name: Optional[str]
    product_name: Optional[str]
    product_code: Optional[str]

    storage_conditions: Optional[str]
    lot_comment: Optional[str]


class Specification(BaseModel):
    analyte: str
    specification_range: str
    unit: Optional[str]


class ProtocolInfo(BaseModel):
    protocol_number: str
    protocol_version: str
    attachment_reference: Optional[str]

    issued_by: Optional[str]
    issue_date: Optional[date]

    analyst_name: Optional[str]
    analysis_method: Optional[str]
    analysis_type: Optional[str]

    sample_preparation_date: Optional[date]
    approval_date: Optional[date]


class Instrument(BaseModel):
    instrument_type: str
    instrument_id: Optional[str]
    valid_until: Optional[date]


class Instrumentation(BaseModel):
    hplc_system: Optional[str]
    pH_meter: Optional[Instrument]
    balance_1: Optional[Instrument]
    balance_2: Optional[Instrument]
    ultrasonic_bath: Optional[Instrument]
    column_number: Optional[str]


class Reagent(BaseModel):
    name: str
    grade_or_description: Optional[str]
    reference_number: Optional[str]
    preparation_date: Optional[date]
    expiry_date: Optional[date]
    reagent_id: Optional[str]


class Consumable(BaseModel):
    name: str
    manufacturer: Optional[str]
    lot_number: Optional[str]


class SignOff(BaseModel):
    analyst_signature: Optional[str]
    analyst_date: Optional[date]
    reviewer_signature: Optional[str]
    reviewer_date: Optional[date]


class EnityExtractionResponse(BaseModel):
    analysis_instruction: AnalysisInstruction

    specifications: List[Specification]

    protocol_info: ProtocolInfo

    instrumentation: Instrumentation

    reagents: List[Reagent]

    consumables: List[Consumable]

    sign_off: SignOff

    company_name: Optional[str]
    document_version: Optional[str]
    page_number: Optional[str]
