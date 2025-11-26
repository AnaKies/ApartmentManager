from enum import Enum
from typing import Union, Dict
from pydantic import BaseModel, Field
from typing import Any


# ========= ENUMS =========

class AnswerSource(str, Enum):
    LLM = "llm"
    BACKEND = "backend"

class AnswerType(str, Enum):
    TEXT = "text"
    DATA = "data"
    ERROR = "error"

# ========= ENVELOPE OK =========

class TextResult(BaseModel):
    message: str

class DataResult(BaseModel):
    payload: Any
    function_call: bool
    message: str

class EnvelopeApi(BaseModel):
    type: AnswerType
    result: Union[TextResult, DataResult]
    answer_source: AnswerSource
    llm_model: str

# ========= ENVELOPE ERROR =========

class ErrorBlock(BaseModel):
    code: int
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class EnvelopeError(BaseModel):
    type: AnswerType
    llm_model: str
    answer_source: AnswerSource
    error: ErrorBlock = None
    trace_id: str

# ========= FUNCTIONS TO BUILD ENVELOPES ==========

def build_text_answer(message: str,
                       model: str,
                       answer_source: AnswerSource) -> EnvelopeApi:
    result = EnvelopeApi(
        type=AnswerType.TEXT,
        result=TextResult(message=message),
        llm_model=model,
        answer_source=answer_source
    )
    return result

def build_data_answer(payload: Any,
                       model: str,
                       answer_source: AnswerSource,
                       payload_comment: str,
                       function_call: bool = False):
    result = EnvelopeApi(
        type=AnswerType.DATA,
        result=DataResult(payload=payload, function_call=function_call, message=payload_comment),
        llm_model=model,
        answer_source=answer_source
    )

    return result

def build_error(code: int,
                message: str,
                llm_model: str,
                answer_source: AnswerSource,
                trace_id: str):
    error_block = ErrorBlock(code=code, message=message)

    result = EnvelopeError(
        type=AnswerType.ERROR,
        error=error_block,
        llm_model=llm_model,
        answer_source=answer_source,
        trace_id=trace_id
    )
    return result