from enum import Enum
import yaml

from typing import Annotated, Any, Dict, List, Optional, Union
from pydantic import Field, BaseModel

class Normalized(BaseModel):
    x: Annotated[float, Field(default=0, ge=-1, le=1)]
    y: Annotated[float, Field(default=0, ge=-1, le=1)]

class Perc(BaseModel):
     val: Annotated[int, Field(default=0, ge=0, le=100)]

# In millimeters
class Position(BaseModel):
    x: float
    y: float
    z: float

class Angle(BaseModel):
    deg: Annotated[float, Field(default=0, ge=-360.0, le=360.0)]
    def toEncodedAngle(self):
        return EncodedAngle(
            enc=(round(self.deg * (4096 / 360)) % 4096),
        )

class EncodedAngle(BaseModel):
    enc: Annotated[int, Field(default=2048, ge=0, le=4096)]
    def toAngle(self):
        return Angle(
            deg=(self.enc * (360 / 4096)) % 360,
        )

class Constraint(BaseModel):
    min: Annotated[float, Field(default=0, ge=-360.0, le=360.0)]
    max: Annotated[float, Field(default=0, ge=-360.0, le=360.0)]

class Configuration(BaseModel):
    offsets: Annotated[dict[str, Angle], Field(default={})]
    constraints: Annotated[dict[str, Constraint], Field(default={})]
    # Loading configuration
    @staticmethod
    def load(path):
        try:
            with open(path, "r") as file:
                config = yaml.safe_load(file)

            return Configuration(**config)
        except:
            conf = Configuration(offsets={
                "bras_horizontal": Angle(),
                "bras1": Angle(),
                "bras2": Angle(),
                "cone": Angle()
            }, constraints={
                "bras_horizontal": Constraint(),
                "bras1": Constraint(),
                "bras2": Constraint(),
                "cone": Constraint()
            })

            conf.save(path)
            return conf

    # Saving configuration
    def save(self, path):
        with open(path, "w+") as file:
            yaml.dump(self.model_dump(), file)

class LightActionArgs(BaseModel):
    perc: Annotated[int, Field(ge=0, le=100)]

class TrackingModeEnum(str, Enum):
    IDLE = "idle"
    OBJECT = "object"
    FACE = "face"

class Emote(Enum):
    IDLE = 0
    NO = 1
    YES = 2
    SAD = 3
    HAPPY = 4

class LightActionArgs(BaseModel):
    perc: Annotated[int, Field(ge=0, le=100)]

class TrackingModeEnum(str, Enum):
    IDLE = "idle"
    OBJECT = "object"
    FACE = "face"

class TrackingSubjects(BaseModel):
    bbox: Annotated[List[float], Field(description="2D normalized space (x, y, w, h)")]
    name: str
    confidence: float

class TrackingModeArgs(BaseModel):
    type: TrackingModeEnum
    subjects: Optional[TrackingSubjects] = None

class AiResponse(BaseModel):
    text: Annotated[str, Field(default="...")]
    emote: Annotated[Emote, Field(default=Emote.IDLE)]
    action: Optional[Dict[str, Union[LightActionArgs, TrackingModeArgs]]] = None