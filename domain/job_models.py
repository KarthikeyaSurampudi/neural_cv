# JobRequirements

from pydantic import BaseModel


class JobRequirements(BaseModel):
    text: str