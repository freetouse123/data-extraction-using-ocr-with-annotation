from pydantic import BaseModel
from typing import Literal

class InputParameter(BaseModel):
    language: Literal["English", "Swedish"]

