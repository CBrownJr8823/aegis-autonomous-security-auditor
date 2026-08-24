from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, HttpUrl, model_validator

from backend.security_engine import SecurityEngine, nvd_connectivity_check

engine = SecurityEngine()

@asynccontextmanager
async def lifespan(_: FastAPI):
    yield

app = FastAPI(title="Aegis Autonomous Security Auditor API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AuditRequest(BaseModel):
    repository_url: HttpUrl | None = None
    code_payload: str | None = Field(default=None, max_length=1_000_000)

    @model_validator(mode="after")
    def validate_source(self) -> "AuditRequest":
        if not self.repository_url and not self.code_payload:
            raise ValueError("Provide repository_url or code_payload.")
        return self

class PatchRequest(BaseModel):
    vulnerability_id: str = Field(min_length=3, max_length=128)
    finding: dict | None = None

@app.get("/api/v1/health")
async def health() -> dict:
    nvd_reachable = await nvd_connectivity_check()
    return {"status": "healthy", "agent_engine": "ready", "vulnerability_database": "connected" if nvd_reachable else "offline-fallback", "active_jobs": sum(job.status == "running" for job in engine.jobs.values())}

@app.post("/api/v1/audit-repo", status_code=202)
async def audit_repository(request: AuditRequest) -> dict:
    job = engine.create_job(str(request.repository_url) if request.repository_url else None, request.code_payload)
    asyncio.create_task(engine.run_job(job.job_id))
    return {"job_id": job.job_id, "status": job.status}

@app.get("/api/v1/audit-status/{job_id}")
async def audit_status(job_id: str) -> dict:
    job = engine.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Audit job not found.")
    return job.as_dict()

@app.post("/api/v1/generate-patch")
async def generate_patch(request: PatchRequest) -> dict:
    for job in engine.jobs.values():
        for finding in job.findings:
            if finding.id == request.vulnerability_id:
                return {"vulnerability_id": finding.id, "patch": engine.generate_patch(finding), "manual_remediation_required": engine.generate_patch(finding) is None}
    if request.finding:
        from backend.security_engine import Finding
        finding = Finding(**request.finding)
        patch = engine.generate_patch(finding)
        return {"vulnerability_id": finding.id, "patch": patch, "manual_remediation_required": patch is None}
    raise HTTPException(status_code=404, detail="Vulnerability was not found in active audit jobs.")
