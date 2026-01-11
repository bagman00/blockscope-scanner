from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from app.core.logging import logger
from app.models.scan import Scan
from app.core.database import SessionLocal
import tempfile
import os
import subprocess
import json

router = APIRouter(prefix="/scan", tags=["scan"])

# ----------- Schemas -----------

class ScanRequest(BaseModel):
    source_code: str = Field(..., description="Full Solidity source code")


class Vulnerability(BaseModel):
    type: str
    severity: str
    description: str
    line: Optional[int] = None


class ScanResponse(BaseModel):
    scan_id: int
    status: str = "completed"
    vulnerabilities: List[Vulnerability]
    score: int
    message: str

# ----------- Constants -----------

# Use local Solidity rules inside Docker container
SEMREGP_RULES_PATHS = [
    "/app/semgrep-rules/solidity/security",
    "/app/semgrep-rules/solidity/best-practice"
]

# ----------- Scan Endpoint -----------

@router.post("/", response_model=ScanResponse)
async def scan_contract(request: ScanRequest):
    logger.info("Received new scan request")

    temp_path = None

    try:
        # 1️⃣ Write Solidity code to temp file
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".sol",
                delete=False,
                encoding="utf-8"
            ) as f:
                f.write(request.source_code)
                temp_path = f.name
        except Exception as e:
            logger.error(f"Temp file creation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to prepare contract file")

        # 2️⃣ Build Semgrep command with multiple rule paths
        cmd = ["semgrep", "scan", "--json", "--quiet"]
        for path in SEMREGP_RULES_PATHS:
            cmd.extend(["--config", path])
        cmd.append(temp_path)

        # 3️⃣ Run Semgrep
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=500, detail="Scan timed out (60s)")
        except FileNotFoundError:
            raise HTTPException(status_code=500, detail="Semgrep not installed or not in PATH")
        except Exception as e:
            logger.error(f"Semgrep execution failed: {e}")
            raise HTTPException(status_code=500, detail="Semgrep execution error")

        # 4️⃣ Validate Semgrep output
        if result.returncode not in (0, 1):
            logger.error(f"Semgrep stderr: {result.stderr}")
            raise HTTPException(
                status_code=500,
                detail="Semgrep failed to run correctly"
            )

        # 5️⃣ Parse Semgrep JSON output
        try:
            data = json.loads(result.stdout)
            findings = data.get("results", [])
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            findings = []

        vulnerabilities = []

        # Severity counters
        critical = high = medium = low = info = 0

        for finding in findings:
            extra = finding.get("extra", {})
            severity = extra.get("severity", "INFO").upper()

            if severity == "CRITICAL":
                critical += 1
            elif severity == "HIGH":
                high += 1
            elif severity == "MEDIUM":
                medium += 1
            elif severity == "LOW":
                low += 1
            else:
                info += 1

            vulnerabilities.append(
                Vulnerability(
                    type=finding.get("check_id", "unknown"),
                    severity=severity,
                    description=extra.get("message", "No description provided"),
                    line=finding.get("start", {}).get("line")
                )
            )

        # 6️⃣ Risk score calculation (higher = more dangerous)
        score = (
            critical * 25 +
            high * 15 +
            medium * 8 +
            low * 3 +
            info * 1
        )
        score = min(score, 100)

        # 7️⃣ Save scan to database
        db = SessionLocal()
        try:
            db_scan = Scan(
                source_code=request.source_code,
                vulnerabilities=[v.dict() for v in vulnerabilities],
                score=score
            )
            db.add(db_scan)
            db.commit()
            db.refresh(db_scan)
        except Exception as e:
            db.rollback()
            logger.error(f"Database save error: {e}")
            raise HTTPException(status_code=500, detail="Failed to save scan results")
        finally:
            db.close()

        # 8️⃣ Response message
        message = (
            "🎉 No vulnerabilities found - Contract looks safe"
            if not vulnerabilities
            else f"⚠️ {len(vulnerabilities)} vulnerabilities detected"
        )

        return ScanResponse(
            scan_id=db_scan.id,
            vulnerabilities=vulnerabilities,
            score=score,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected scan error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during scan")

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Temp file cleanup failed: {e}")
