from pydantic import BaseModel
from .english.Analysis_instruction_model import AnalysisInstructionDocument
from .english.protocal_model import LCProtocolDocument
from .english.Reagents_model import ReagentsInventory



class DataExtractionSchema(BaseModel):
    analysis_instruction: AnalysisInstructionDocument
    lc_protocol: LCProtocolDocument
    reagents_inventory: ReagentsInventory