from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date


class ReagentItem(BaseModel):   
    reagent_index: Optional[str] = Field( None, description="Reagent identifier (Roman numeral I–XV)." )
    reagent_name: Optional[str] = Field( None, description="Name of the reagent." )
    standard_number: Optional[str] = Field( None, description="Standard number (Standardnr)." )
    reagent_number: Optional[str] = Field( None, description="Reagent number (Reagensnr)." )
    catalog_number: Optional[str] = Field( None, description="Catalog number (Knr)." )
    manufacturer: Optional[str] = Field( None, description="Manufacturer or supplier." )
    brand: Optional[str] = Field( None, description="Brand or product line (e.g., Pall, Fisher)." )
    lot_number: Optional[str] = Field( None, description="Lot or batch number." )
    expiry_date: Optional[date] = Field( None, description="Expiry date (Utg.datum)." )
    dispensing_date: Optional[date] = Field( None, description="Dispensing or tapping date (Tappningsdatum)." )
    assay: Optional[str] = Field( None, description="Assay or concentration (Halt)." )
    notes: Optional[str] = Field( None, description="Additional reagent-related remarks." )


class ReagentsInventory(BaseModel): 
    reagents: List[ReagentItem] = Field( ..., description="List of reagents (I–XV) used in the analysis." )
