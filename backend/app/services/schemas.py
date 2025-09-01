from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Any, Optional


class ConversationTurn(BaseModel):
    """Represents a single turn in the conversation history."""
    role: Literal["user", "assistant"]
    content: str

class AssessmentQuestion(BaseModel):
    """Represents a single question in a standardized test."""
    id: str
    text: str

class AssessmentData(BaseModel):
    """Holds the state of the final assessment phase."""
    test_name: str
    questions: List[AssessmentQuestion]
    answers: Dict[str, Any] = {} # e.g., {"q1": 3, "q2": 1}
    current_question_index: int = 0
    final_score: Optional[float] = None
    summary: Optional[str] = None

# --- The Main State Object ---

class SessionData(BaseModel):
    """
    The single, evolving state object that holds the entire memory of the conversation.
    This is the "passport" passed between the client and server.
    """
    session_id: str = Field(..., description="Unique identifier for this entire session.")
    
    status: Literal[
        "priming", 
        "refining_broad",  
        "refining_sub", 
        "assessing", 
        "complete"
    ] = Field(..., description="The current stage of the diagnostic funnel.")
    
    # The question the AI has just asked and is waiting for a user response to.
    ai_question_to_ask_user: Optional[str] = None
    
    # The full transcript of the conversation for context.
    conversation_history: List[ConversationTurn] = []
    
    # The current set of hypotheses and their confidence scores.
    belief_state: Optional[Dict[str, float]] = None
    
    # The final, high-confidence category identified by the refinement loop.
    final_category: Optional[str] = None
    
    # The data related to the final standardized test phase.
    assessment_data: Optional[AssessmentData] = None


# --- API Endpoint Request/Response Models ---

# For POST /api/conversation/start
class StartRequest(BaseModel):
    initial_text: str
    consent_given: bool

class StartResponse(BaseModel):
    ai_question: str
    session_data: SessionData

# For POST /api/conversation/respond
class RespondRequest(BaseModel):
    user_answer: str
    session_data: SessionData # The client sends the whole state back

class RespondResponse(BaseModel):
    status: str # e.g., "in_progress", "assessment_ready", "complete"
    ai_question: Optional[str] = None # The next question to ask
    session_data: SessionData # The server returns the updated state


class Verdict(BaseModel):
    """The structured output for an AI Judge's evaluation of a user's answer."""
    supported_category: str = Field(description="The single category that the user's answer most strongly supports from the provided list.")
    reasoning: str = Field(description="A brief, one-sentence justification for why this category was chosen, directly quoting or referencing the user's answer.")
    confidence_score: float = Field(description="A confidence score from 0.0 to 1.0 indicating how certain the AI is about its verdict.", ge=0.0, le=1.0)


class QuestionGenerationPlan(BaseModel):
    reasoning: str = Field(description="A brief, internal thought process. Analyze the user's last statement and the candidate descriptions to identify the key differentiating feature to probe next.")
    next_question: str = Field(description="The final, single, empathetic question to ask the user based on the reasoning.")