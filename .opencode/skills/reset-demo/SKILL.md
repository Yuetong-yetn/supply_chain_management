---
name: reset-demo
description: Use when resetting demo data, restoring the initial demo state, or preparing a clean course demonstration.
---

# reset-demo — Reset demo data to initial state

Reset the system to a clean demo state.

## Steps
```bash
cd backend
python scripts/reset_demo_data.py
```
or

```bash
cd backend
python scripts/init_db.py --rebuild
python scripts/generate_example_data.py
python scripts/load_example_data.py
```

## What gets reset
- All tables dropped and recreated
- Fresh example data loaded
- Sample purchase orders, inbound orders, replenishment requests
- Inventory records initialized
- AI recommendations cleared and regenerated

## Demo users after reset
| Username | Password | Role |
|---|---|---|
| `admin` | `admin123` | System admin |
| `buyer` | `buyer123` | Purchasing staff |
| `warehouse` | `warehouse123` | Warehouse staff |
| `store` | `store123` | Store staff |
| `manager` | `manager123` | Business manager |
| `demo` | `demo123` | Demo user |

## Verification
- `http://127.0.0.1:8000/api/health` — should return success
- `http://127.0.0.1:8000/demo` — login with demo/demo123
