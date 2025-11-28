# ORM Table Relationships

This document outlines the structure and relationships of the ORM tables in the application.

## Rental Database (`apartment_app.db`)

The rental database manages the core business logic: apartments, tenants, contracts, and their associations.

### Tables

1.  **Apartment**
    *   **Table Name:** `apartment`
    *   **Primary Key:** `id_apartment`
    *   **Description:** Represents a physical apartment unit.

2.  **Tenancy**
    *   **Table Name:** `tenancy`
    *   **Primary Key:** `id_tenancy`
    *   **Foreign Keys:**
        *   `id_apartment` references `Apartment(id_apartment)`
        *   `id_tenant_personal_data` references `PersonalData(id_personal_data)`
        *   `id_rent_data` references `Contract(id_rent_data)`
    *   **Description:** Represents a specific rental period, linking an apartment, a tenant, and a contract.

3.  **PersonalData**
    *   **Table Name:** `personal_data`
    *   **Primary Key:** `id_personal_data`
    *   **Description:** Stores personal information about tenants.

4.  **Contract**
    *   **Table Name:** `rent_data`
    *   **Primary Key:** `id_rent_data`
    *   **Description:** Stores financial details of the rental agreement (rent, utilities, etc.).

### Entity Relationship Diagram

```mermaid
erDiagram
    Apartment ||--o{ Tenancy : "is rented via"
    PersonalData ||--o{ Tenancy : "signs"
    Contract ||--|| Tenancy : "governs"

    Apartment {
        int id_apartment PK
        float area
        string address
        float price_per_square_meter
        int utility_billing_provider_id
    }

    Tenancy {
        int id_tenancy PK
        int id_apartment FK
        int id_tenant_personal_data FK
        int id_rent_data FK
        string move_in_date
        string move_out_date
        float deposit
        string registered_address
        string comment
    }

    PersonalData {
        int id_personal_data PK
        string first_name
        string last_name
        string bank_data
        string phone_number
        string email
        string comment
    }

    Contract {
        int id_rent_data PK
        float net_rent
        float utility_costs
        float vat
        float garage
        float parking_spot
        string comment
    }
```

## Logs Database (`log_conversation.db`)

The logs database is separate and stores conversation history and system logs.

### Tables

1.  **Log**
    *   **Table Name:** `log_conversation`
    *   **Primary Key:** `id_log`
    *   **Description:** Stores individual log entries for AI interactions.

```mermaid
erDiagram
    Log {
        int id_log PK
        string ai_model
        string user_question
        string back_end_response
        string ai_answer
        string system_prompt_name
        datetime timestamp
    }
```
