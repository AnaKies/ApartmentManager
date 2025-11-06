from typing import Union, Dict, Optional, Literal
from pydantic import BaseModel, Field, model_validator
from typing import Any
from flask import jsonify
from sqlalchemy import Boolean


class TextResult(BaseModel):
    message: str
    function_call: bool

class DataResult(BaseModel):
    payload: Any
    function_call: bool
    message: str

class ErrorBlock(BaseModel):
    code: int
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class EnvelopeOk(BaseModel):
    type: Literal["text", "data", "error"]
    result: Union[TextResult, DataResult]
    answer_source: Literal["llm", "backend"]
    llm_model: str

class EnvelopeError(BaseModel):
    type: Literal["text", "data", "error"]
    llm_model: str
    error: ErrorBlock = None

def build_text_answer(message: str,
                       model: str,
                       answer_source: Literal["llm", "backend"],
                       function_call: bool = False):
    env = EnvelopeOk(
        type="text",
        result=TextResult(message=message, function_call=function_call),
        llm_model=model,
        answer_source=answer_source
    )
    result = env.model_dump()
    return result

def build_data_answer(payload: Any,
                       model: str,
                       answer_source: Literal["llm", "backend"],
                       payload_comment: str,
                       function_call: bool = False):
    env = EnvelopeOk(
        type="data",
        result=DataResult(payload=payload, function_call=function_call, message=payload_comment),
        llm_model=model,
        answer_source=answer_source
    )
    result = env.model_dump()
    return result

def build_error(code: int,
                message: str,
                llm_model: str):
    error_block = ErrorBlock(code=code, message=message)

    env = EnvelopeError(
        type="error",
        error=error_block,
        llm_model=llm_model
    )
    result = env.model_dump()
    return result