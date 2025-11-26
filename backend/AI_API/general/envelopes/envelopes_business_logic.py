from enum import Enum
from typing import TypeVar, Type
from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)

class DataTypeInDB(str, Enum): # str because of serialization in Pydantic
    APARTMENT = "apartment"
    PERSON = "person"
    CONTRACT = "contract"
    TENANCY = "tenancy"

# ========= CRUD INTENT =========
class CrudOperationData(BaseModel):
    value: bool
    type: DataTypeInDB

class ShowOperationData(CrudOperationData):
    single: bool # True -> get one entity, False -> get all entities

class CrudIntentModel(BaseModel):
    create: CrudOperationData
    show: ShowOperationData
    update: CrudOperationData
    delete: CrudOperationData

# ========= LLM COLLECTS DATA TO WRITE CRUD OPERATIONS =========

class CollectData(BaseModel):
    ready: bool
    data: str
    comment: str


# ========= UNIVERSAL VALIDATION =========

def get_json_schema(model: Type[T]) -> dict:
    return model.model_json_schema()

def validate_model(model: Type[T], data: dict) -> T:
    return model.model_validate(data)