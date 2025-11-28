from enum import Enum
from typing import TypeVar, Type, Optional, Union
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
    operation_id: str

class ShowOperationData(CrudOperationData):
    single: bool # True -> get one entity, False -> get all entities

class CrudIntentModel(BaseModel):
    create: CrudOperationData
    show: ShowOperationData
    update: CrudOperationData
    delete: CrudOperationData

# ========= LLM COLLECTS DATA TO WRITE CRUD OPERATIONS =========

class PersonCreate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bank_data: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    comment: Optional[str] = None
    # For update/delete
    id_personal_data: Optional[int] = None
    old_first_name: Optional[str] = None
    old_last_name: Optional[str] = None

class TenancyCreate(BaseModel):
    id_apartment: Optional[int] = None
    id_tenant_personal_data: Optional[int] = None
    id_contract: Optional[int] = None
    move_in_date: Optional[str] = None
    move_out_date: Optional[str] = None
    deposit: Optional[float] = None
    registered_address: Optional[str] = None
    comment: Optional[str] = None
    # For update/delete
    id_tenancy: Optional[int] = None

class ContractCreate(BaseModel):
    net_rent: Optional[float] = None
    utility_costs: Optional[float] = None
    vat: Optional[float] = None
    garage: Optional[float] = None
    parking_spot: Optional[float] = None
    comment: Optional[str] = None
    # For update/delete
    id_contract: Optional[int] = None

class ApartmentCreate(BaseModel):
    area: Optional[float] = None
    address: Optional[str] = None
    price_per_square_meter: Optional[float] = None
    utility_billing_provider_id: Optional[int] = None
    # For update/delete
    id_apartment: Optional[int] = None
    old_address: Optional[str] = None

class CollectData(BaseModel):
    ready: bool
    data: Optional[Union[
        PersonCreate,
        TenancyCreate,
        ContractCreate,
        ApartmentCreate
    ]] = None
    comment: str


# ========= UNIVERSAL VALIDATION =========

def get_json_schema(model: Type[T]) -> dict:
    return model.model_json_schema()

def validate_model(model: Type[T], data: dict) -> T:
    return model.model_validate(data)