import uuid 
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class RepoCreate(BaseModel):
    """Payload for registering a Github repo under an org"""
    
    github_repo_id : str 
    full_name : str 
    default_branch : str = "main"


class RepoResponse(BaseModel):
    """Public representation of a synced repo"""

    id : uuid.UUID
    org_id : uuid.UUID
    github_repo_id : str
    full_name : str 
    default_branch : str 
    last_synced_at : Optional[datetime]

    model_config = {"from_attributes" : True} 


