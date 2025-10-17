from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    project_name: str = Field(..., description="Repository/project name to create")
    description: str = Field(..., description="High-level description of the app to generate")
    requirements: Optional[List[str]] = Field(default=None, description="Optional bullet requirements")
    metadata: Optional[Dict[str, str]] = Field(default=None, description="Arbitrary key/value metadata to send to evaluator")
    notify_url: Optional[str] = Field(default=None, description="Override evaluation server URL; defaults to env EVAL_SERVER_URL")
    notify_email: Optional[str] = Field(default=None, description="If provided, send an email notification to this address")
    secret_key: Optional[str] = Field(default=None, description="Optional shared secret; validated against env SECRET_KEY if present")


class GenerateAcceptedResponse(BaseModel):
    status: str
    project_name: str
    message: str
    expected_repo_html: Optional[str] = None

