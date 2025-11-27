# CRUD Operation State Flow Diagram

## State Determination Flow

```
┌─────────────────────────────────────────┐
│   User sends a message                  │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│  Check: operation_id exists?            │
└─────────────┬───────────────────────────┘
              │
      ┌───────┴───────┐
      │               │
      ▼               ▼
   YES (not empty)    NO (empty/None)
      │               │
      ▼               ▼
┌──────────────┐  ┌──────────────────────┐
│ CONTINUE     │  │ ANALYZE new intent   │
│ current      │  │ from user message    │
│ operation    │  └──────────┬───────────┘
└──────────────┘             │
      │                      ▼
      │            ┌─────────────────────┐
      │            │ CRUD operation      │
      │            │ detected?           │
      │            └─────────┬───────────┘
      │                  ┌───┴────┐
      │                  │        │
      │                  ▼        ▼
      │                YES       NO
      │                  │        │
      │                  ▼        │
      │         ┌────────────────┐│
      │         │ Generate new   ││
      │         │ operation_id   ││
      │         │ & save any     ││
      │         │ interrupted    ││
      │         │ operations     ││
      │         └────────────────┘│
      │                  │        │
      └──────────────────┼────────┘
                         │
                         ▼
              ┌──────────────────┐
              │ Return response  │
              └──────────────────┘
```

## Interrupted Operations Management

```
STATE: No active operation (operation_id = None)
┌─────────────────────────────────────────────┐
│ interrupted_operations = {}                 │
│ last_create_operation_id = None             │
│ last_update_operation_id = None             │
│ last_delete_operation_id = None             │
└─────────────────────────────────────────────┘
                    │
                    │ User: "Create person"
                    ▼
┌─────────────────────────────────────────────┐
│ operation_id = "create01"                   │
│ last_create_operation_id = "create01"       │
│ last_create_type = "person"                 │
│ interrupted_operations = {}                 │
└─────────────────────────────────────────────┘
                    │
                    │ User: "Update apartment"
                    ▼
┌─────────────────────────────────────────────┐
│ operation_id = "update01"                   │
│ last_update_operation_id = "update01"       │
│ interrupted_operations = {                  │
│   "create": {                               │
│     "operation_id": "create01",             │
│     "type": "person",                       │
│     "envelope": {...}                       │
│   }                                         │
│ }                                           │
└─────────────────────────────────────────────┘
                    │
                    │ User: "Delete contract"
                    ▼
┌─────────────────────────────────────────────┐
│ operation_id = "delete01"                   │
│ last_delete_operation_id = "delete01"       │
│ interrupted_operations = {                  │
│   "create": {...},                          │
│   "update": {                               │
│     "operation_id": "update01",             │
│     "type": "apartment",                    │
│     "envelope": {...}                       │
│   }                                         │
│ }                                           │
└─────────────────────────────────────────────┘
                    │
                    │ User confirms delete
                    │ (cycle_is_ready = True)
                    ▼
┌─────────────────────────────────────────────┐
│ operation_id = None                         │
│ last_delete_operation_id = None             │
│ interrupted_operations = {                  │
│   "create": {...},                          │
│   "update": {...}                           │
│ }                                           │ ← Delete removed, others remain
└─────────────────────────────────────────────┘
```

## Conflict Detection Flow

```
┌─────────────────────────────────────────────┐
│ User wants to start NEW operation           │
└─────────────────┬───────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────┐
│ Check: interrupted_operations empty?        │
└─────────────────┬───────────────────────────┘
                  │
          ┌───────┴────────┐
          │                │
          ▼                ▼
         YES              NO
          │                │
          ▼                ▼
   ┌──────────┐   ┌───────────────────────────┐
   │ Proceed  │   │ Check same operation type?│
   │ normally │   └───────┬───────────────────┘
   └──────────┘           │
                  ┌───────┴───────┐
                  │               │
                  ▼               ▼
          Same type exists    Different types only
                  │               │
                  ▼               ▼
    ┌──────────────────────┐  ┌────────────────────┐
    │ ASK: "Cancel old     │  │ Count total        │
    │ operation?"          │  │ interrupted ops    │
    └──────────────────────┘  └────────┬───────────┘
                                       │
                              ┌────────┴────────┐
                              │                 │
                              ▼                 ▼
                          > 2 total          ≤ 2 total
                              │                 │
                              ▼                 ▼
                  ┌──────────────────────┐  ┌─────────┐
                  │ ASK: "Which to       │  │ Proceed │
                  │ cancel?"             │  │ normally│
                  │ (list all)           │  └─────────┘
                  └──────────────────────┘
```

## Operation Lifecycle

```
NEW OPERATION
    │
    ├─→ Generate operation_id (e.g., "abc12345")
    │
    ├─→ Save to last_{type}_operation_id
    │
    ├─→ Save interrupted operations (if any different type)
    │
    ▼
COLLECT DATA (cycle_is_ready = False)
    │
    ├─→ Keep same operation_id
    │
    ├─→ Update last_{type}_envelope
    │
    │   Loop until all data collected
    │   ◄─────────┘
    │
    ▼
COMPLETE (cycle_is_ready = True)
    │
    ├─→ Clear operation_id (set to None)
    │
    ├─→ Remove from interrupted_operations
    │
    ├─→ Clear last_{type}_operation_id
    │
    └─→ Clear last_{type}_type
```

## Key Decision Points

1. **When to generate operation_id:**
   - Only when `operation_id` is None/empty AND user starts CRUD operation

2. **When to save to interrupted_operations:**
   - Only when starting NEW operation while another is in progress
   - Only save DIFFERENT operation types (not same type)

3. **When to clear operation_id:**
   - Only when `cycle_is_ready = True` (operation complete)

4. **When to ask user for confirmation:**
   - Starting same operation type as an interrupted one
   - More than 2 total interrupted operations exist

5. **What LLM sees:**
   - `feedback.operation_id`: Current active operation ID
   - `feedback.interrupted_operations`: Dictionary of saved operations
   - `feedback.result`: Envelope from last operation step
