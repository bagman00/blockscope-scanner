from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from pathlib import Path
import subprocess
import json
import os

from app.core.logging import logger
from app.models.scan import Scan
from app.core.database import SessionLocal

router = APIRouter(prefix="/scan", tags=["Scan"])

# =========================
# Pydantic Models
# =========================

class ScanRequest(BaseModel):
    source_code: str = Field(default="", description="Full Solidity source code to analyze")
    contract_name: Optional[str] = Field(default="UntitledContract", description="Main contract name")


class Vulnerability(BaseModel):
    type: str
    severity: str
    description: str
    line: Optional[int] = None


class ScanResponse(BaseModel):
    scan_id: int
    status: str
    vulnerabilities: List[Vulnerability]
    score: int
    message: str


# =========================
# API Endpoint
# =========================

@router.post("/", response_model=ScanResponse)
async def scan_contract(request: ScanRequest):
    if not request.source_code.strip():
        raise HTTPException(status_code=422, detail="source_code cannot be empty")

    logger.info("New scan request received")

    # 1. Setup stable file path
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    CONTRACTS_DIR = BASE_DIR / "contracts"
    CONTRACTS_DIR.mkdir(exist_ok=True)
    contract_path = CONTRACTS_DIR / "uploaded.sol"

    # 2. Write Solidity code to file
    try:
        with open(contract_path, "w", encoding="utf-8") as f:
            f.write(request.source_code)
    except Exception as e:
        logger.error(f"File write failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to write contract file")

    # 3. Run Slither
    try:
        result = subprocess.run(
            ["slither", str(contract_path), "--json", "-"],
            capture_output=True,
            text=True
        )

        if "Compilation failed" in result.stderr and not result.stdout:
            logger.error(f"Slither compilation failed: {result.stderr}")
            raise HTTPException(
                status_code=500, 
                detail="Solidity compilation failed. Ensure your pragma version is supported."
            )

        logger.info("Slither analysis completed successfully")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Slither execution error: {e}")
        raise HTTPException(status_code=500, detail="Slither execution failed")

    # --------------------------------------------------
    # 4️⃣ Parsing Slither JSON Output (Improved Line Mapping)
    # --------------------------------------------------
    vulns: List[Vulnerability] = []
    
    try:
        if result.stdout:
            raw_data = json.loads(result.stdout)
            if "results" in raw_data and "detectors" in raw_data["results"]:
                for issue in raw_data["results"]["detectors"]:
                    # Improved line number extraction
                    mapping = issue.get("source_mapping", {})
                    lines = mapping.get("lines", [])
                    bug_line = lines[0] if lines else 0 # Get the starting line number

                    vuln = Vulnerability(
                        type=issue.get("check", "unknown"),
                        severity=issue.get("impact", "low"),
                        description=issue.get("description", ""),
                        line=bug_line
                    )
                    vulns.append(vuln)

        # Calculate a basic risk score
        severity_map = {"High": 10, "Medium": 5, "Low": 2, "Informational": 1}
        score = sum(severity_map.get(v.severity, 0) for v in vulns)
        score = min(score, 100)
        
    except Exception as e:
        logger.warning(f"Failed to parse Slither output: {e}")

    # --------------------------------------------------
    # 5️⃣ Save scan result to database
    # --------------------------------------------------
    db = SessionLocal()
    try:
        db_scan = Scan(
            contract_name=request.contract_name,
            source_code=request.source_code,
            vulnerabilities=[v.model_dump() for v in vulns],
            score=score,
            status="completed"
        )
        db.add(db_scan)
        db.commit()
        db.refresh(db_scan)
        scan_id = db_scan.id
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail=f"DB Save Failed: {str(e)}")
    finally:
        db.close()
        
    # 6. Final Response
    return ScanResponse(
        scan_id=scan_id,
        status="completed",
        vulnerabilities=vulns,
        score=score,
        message="Scan completed successfully"
    )