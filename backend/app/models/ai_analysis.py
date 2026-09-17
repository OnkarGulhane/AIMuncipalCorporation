from sqlalchemy import Column, String, Float, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class AIAnalysis(BaseModel):
    __tablename__ = "ai_analyses"

    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False, index=True)
    suggested_category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    suggested_priority = Column(String(20), nullable=True)
    suggested_severity = Column(String(20), nullable=True)
    confidence_score = Column(Float, default=0.0, nullable=False)
    summary = Column(Text, nullable=True)
    key_details = Column(Text, nullable=True)  # JSON string of extracted facts
    missing_information = Column(Text, nullable=True)  # JSON string of detected missing fields
    recommended_action = Column(Text, nullable=True)
    suggested_team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    risk_insight = Column(Text, nullable=True)
    duplicate_cases = Column(Text, nullable=True)  # JSON string of matched similar cases

    case_rel = relationship("Case", foreign_keys=[case_id], back_populates="ai_analyses")
    suggested_category = relationship("Category", foreign_keys=[suggested_category_id])
    suggested_team = relationship("Team", foreign_keys=[suggested_team_id])

    def __repr__(self) -> str:
        return f"<AIAnalysis Case {self.case_id}: Priority={self.suggested_priority} (Conf={self.confidence_score:.2f})>"
