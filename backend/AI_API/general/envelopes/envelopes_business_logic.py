from datetime import date
from enum import Enum
from typing import TypeVar, Type, Optional, Generic, Union
from pydantic import BaseModel, EmailStr, NonNegativeFloat
from pydantic_extra_types.phone_numbers import PhoneNumber

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
# Optional means: the value type T or None

# --- PERSON ---

class PersonCreate(BaseModel):
    first_name: str
    last_name: str

    bank_data: Optional[str] = None
    phone_number: Optional[PhoneNumber] = None
    email: Optional[EmailStr] = None
    comment: Optional[str] = None

class PersonDeleteById(BaseModel):
    id_personal_data: int

class PersonDeleteByLastName(BaseModel):
    last_name: str

class PersonDeleteByName(BaseModel):
    first_name: str
    last_name: str

PersonDelete = Union[
        PersonDeleteById,
        PersonDeleteByLastName,
        PersonDeleteByName]

class PersonUpdateFields(BaseModel):
    new_first_name: Optional[str] = None
    new_last_name: Optional[str] = None
    new_bank_data: Optional[str] = None
    new_phone_number: Optional[PhoneNumber] = None
    new_email: Optional[EmailStr] = None
    new_comment: Optional[str] = None

class PersonUpdateById(PersonUpdateFields):
    id_personal_data: int

class PersonUpdateByLastName(PersonUpdateFields):
    last_name: str

class PersonUpdateByName(PersonUpdateFields):
    first_name: str
    last_name: str

PersonUpdate = Union[
    PersonUpdateById,
    PersonUpdateByLastName,
    PersonUpdateByName]


# --- TENANCY ---

class TenancyCreate(BaseModel):
    move_in_date: date
    registered_address: str

    id_apartment: Optional[int] = None
    id_tenant_personal_data: Optional[int] = None
    id_contract: Optional[int] = None
    move_out_date: Optional[date] = None
    deposit: Optional[NonNegativeFloat] = None
    comment: Optional[str] = None

class TenancyDeleteById(BaseModel):
    id_tenancy: int

class TenancyDeleteByApartment(BaseModel):
    id_apartment: int

class TenancyDeleteByPerson(BaseModel):
    id_tenant_personal_data: int

TenancyDelete = Union[
    TenancyDeleteById,
    TenancyDeleteByApartment,
    TenancyDeleteByPerson]


class TenancyUpdateFields(BaseModel):
    new_move_in_date: Optional[date] = None
    new_move_out_date: Optional[date] = None
    new_deposit: Optional[NonNegativeFloat] = None
    new_registered_address: Optional[str] = None
    new_comment: Optional[str] = None

class TenancyUpdateById(TenancyUpdateFields):
    id_tenancy: int

class TenancyUpdateByApartment(TenancyUpdateFields):
    id_apartment: int

class TenancyUpdateByPerson(TenancyUpdateFields):
    id_tenant_personal_data: int

TenancyUpdate = Union[TenancyUpdateById, TenancyUpdateByApartment, TenancyUpdateByPerson]


# --- CONTRACT ---

class ContractCreate(BaseModel):
    net_rent: NonNegativeFloat

    utility_costs: Optional[NonNegativeFloat] = None
    vat: Optional[NonNegativeFloat] = None
    garage: Optional[NonNegativeFloat] = None
    parking_spot: Optional[NonNegativeFloat] = None
    comment: Optional[str] = None

class ContractDeleteById(BaseModel):
    id_contract: int

class ContractDelete(BaseModel):
    identification: ContractDeleteById

class ContractUpdateFields(BaseModel):
    new_net_rent: Optional[NonNegativeFloat] = None
    new_utility_costs: Optional[NonNegativeFloat] = None
    new_vat: Optional[NonNegativeFloat] = None
    new_garage: Optional[NonNegativeFloat] = None
    new_parking_spot: Optional[NonNegativeFloat] = None
    new_comment: Optional[str] = None

class ContractUpdateById(ContractUpdateFields):
    id_contract: int

ContractUpdate = ContractUpdateById


# --- APARTMENT ---

class ApartmentCreate(BaseModel):
    # required
    address: str

    area: Optional[NonNegativeFloat] = None
    price_per_square_meter: Optional[NonNegativeFloat] = None
    utility_billing_provider_id: Optional[int] = None

class ApartmentDeleteById(BaseModel):
    id_apartment: int

class ApartmentDeleteByAddress(BaseModel):
    address: str

ApartmentDelete = Union[
    ApartmentDeleteById,
    ApartmentDeleteByAddress]


class ApartmentUpdateFields(BaseModel):
    new_address: Optional[str] = None
    new_area: Optional[NonNegativeFloat] = None
    new_price_per_square_meter: Optional[NonNegativeFloat] = None
    new_utility_billing_provider_id: Optional[int] = None

class ApartmentUpdateById(ApartmentUpdateFields):
    id_apartment: int

class ApartmentUpdateByAddress(ApartmentUpdateFields):
    address: str

ApartmentUpdate = Union[ApartmentUpdateById, ApartmentUpdateByAddress]


# For generic fill of the field data
CollectedData = TypeVar("CollectedData", bound=BaseModel)

class CollectCreate(BaseModel, Generic[CollectedData]):
    """
    Class fo communication with LLM
    """
    ready: bool
    data: Optional[CollectedData] = None
    comment: str


# ========= UNIVERSAL VALIDATION =========

def get_json_schema(model: Type[T]) -> dict:
    return model.model_json_schema()

def validate_model(model: Type[T], data: dict) -> T:
    return model.model_validate(data)