from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

"""
Analysi Instuction Extraction from the documents where in the english language 
"""


class AnalysisInstructionHeader(BaseModel):
    sample_batch_number: Optional[str] = Field(None, description="Sample or batch number.")
    test_location: Optional[str] = Field( None, description="Location where the test or analysis was performed.")
    completion_date: Optional[date] = Field( None, description="Date when the analysis was completed.")
    lot_number: Optional[str] = Field( None, description="Lot number.")
    lot_name: Optional[str] = Field( None, description="Lot name.")
    designation: Optional[str] = Field( None, description="Designation or description of the item.")
    product: Optional[str] = Field( None, description="Product name.")
    storage_conditions: Optional[str] = Field( None, description="Storage conditions.")
    lot_comment: Optional[str] = Field( None, description="Comments related to the lot.")
    analysis: Optional[str] = Field( None, description="Analysis performed.")
    requirements: Optional[str] = Field( None, description="Requirements or acceptance criteria.")
    test_method_id: Optional[str] = Field( None, description="Test or method identifier (e.g., PIVYA-HALT).")
    method_version: Optional[str] = Field( None, description="Method and version (e.g., P1091).")
    attachment: Optional[str] = Field( None, description="Attachment or appendix reference.")
    notes: Optional[str] = Field( None, description="Additional notes.")


class SignatureBlock(BaseModel):
    analyst: Optional[str] = Field( None, description="Name or signature of the analyst." )
    reviewer: Optional[str] = Field( None, description="Name or signature of the reviewer.")



class DocumentFooter(BaseModel):
    printed_by: Optional[str] = Field( None, description="Person or system that printed the document.")
    printed_timestamp: Optional[datetime] = Field( None, description="Date and time when the document was printed.")
    report_id: Optional[str] = Field( None, description="Unique report identifier.")
    revision: Optional[str] = Field( None, description="Document revision.")
    last_modified: Optional[datetime] = Field( None, description="Date and time when the document was last modified.")
    page_info: Optional[str] = Field( None, description="Page numbering information (e.g., 'Page X of Y').")



class AnalysisInstructionDocument(BaseModel):
    header: AnalysisInstructionHeader
    signatures: SignatureBlock
    footer: DocumentFooter
