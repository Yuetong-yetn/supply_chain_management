# demo-flow

Run the complete business flow to verify all system features are working.

## Prerequisites
- Database initialized with example data
- Backend running at `http://127.0.0.1:8000`

## Verification steps

### 1. System health
```
GET /api/health        -> {"success": true, ...}
GET /api/health/db     -> "oceanbase-primary" or "sqlite-fallback"
```

### 2. Frontend login
1. Open `http://127.0.0.1:8000/demo`
2. Login with `demo`
3. Select any role

### 3. System status page
Check API status, database status, and data import status

### 4. Dashboard
Verify summary metrics appear:
- Product count, supplier count, warehouse count, store count
- Total inventory, alert count, recommendation count
- ECharts inventory ranking chart renders

### 5. Purchase -> Inbound flow
1. Create a purchase order
2. View inbound orders list
3. Complete an inbound order -> warehouse inventory increases
4. Check stock transaction log shows the inbound record

### 6. Replenishment -> Outbound flow
1. Create a store replenishment request
2. Approve the request -> auto-generates outbound orders
3. Ship the outbound order -> warehouse stock decreases
4. Confirm receipt at store -> store inventory increases
5. Check stock transaction log for all movements

### 7. AI recommendations
1. Generate recommendations (with LLM enhancement if configured)
2. Verify risk levels, suggested quantities, and reasons display
3. Adopt or reject a recommendation

### 8. Analytics
1. Check inventory ranking chart
2. Check monthly warehouse in/out trend chart
3. View supplier score ranking

### 9. API docs
Open `http://127.0.0.1:8000/docs` and test any endpoint interactively.
