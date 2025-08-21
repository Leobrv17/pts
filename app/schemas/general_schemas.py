from pydantic import BaseModel


class HttpResponseDeleteStatus(BaseModel):
    """General schema for deletion status."""
    status: bool
    msg: str
