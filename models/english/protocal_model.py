from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime



class LCProtocolHeader(BaseModel):
    protocol_number: Optional[str] = Field( None, description="Protocol number (e.g., LC25-324).")
    issued_by: Optional[str] = Field( None, description="Person or department that issued the protocol.")
    Date: Optional[date] = Field( None, description="Date when the protocol was issued.")
    analyst: Optional[str] = Field( None, description="Name of the analyst.")
    method_used: Optional[str] = Field( None, description="Analytical method used (e.g., P1091).")
    product: Optional[str] = Field( None, description="Product under analysis (e.g., Pivmecillinam).")
    analysis_description: Optional[str] = Field( None, description="Type of analysis performed (e.g., assay and degradation).")
    estimated_analysis_time: Optional[str] = Field( None, description="Estimated time required for analysis.")
    estimated_compilation_time: Optional[str] = Field( None, description="Estimated time required for result compilation.")
    estimated_review_time: Optional[str] = Field( None, description="Estimated time required for review.")



class InstrumentsBlock(BaseModel):
    hplc_system_id: Optional[str] = Field( None, description="HPLC system identifier.")
    ph_meter_valid_until: Optional[date] = Field( None, description="pH meter calibration valid until date.")
    balance_valid_until: Optional[date] = Field( None, description="Balance calibration valid until date.")
    timer_valid_until: Optional[date] = Field( None, description="Timer calibration valid until date.")
    ultrasonic_bath_valid_until: Optional[date] = Field( None, description="Ultrasonic bath calibration valid until date.")
    column_number: Optional[str] = Field( None, description="HPLC column number or identifier.")



class ProtocolSignatures(BaseModel):
    not_applicable: Optional[bool] = Field( None, description="Indicates if signatures are marked as not applicable.")
    reviewed_by: Optional[str] = Field( None, description="Name of the reviewer.")
    review_date: Optional[date] = Field( None, description="Date of review.")
    reviewer_signature: Optional[str] = Field( None, description="Reviewer signature or initials.")



class LCProtocolDocument(BaseModel):
    protocol_header: LCProtocolHeader
    instruments: InstrumentsBlock
    signatures: ProtocolSignatures
