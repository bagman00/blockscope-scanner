from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.core.database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, index=True)
    contract_address = Column(String, nullable=True, index=True)  # Optional: if scanning deployed contract
    contract_name = Column(String, nullable=True)
    source_code = Column(Text, nullable=True)  # Full Solidity code
    vulnerabilities = Column(JSON, nullable=False, default=list)  # List of detected vulns
    score = Column(Integer, default=0)  # Risk score (e.g., number of critical vulns)
    scanned_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String, default="completed")  # completed, failed, etc.