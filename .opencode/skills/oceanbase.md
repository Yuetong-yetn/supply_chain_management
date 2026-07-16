# oceanbase — Manage OceanBase database

Manage the OceanBase Docker container used as the primary database.

## Check container status
```bash
docker ps -a --filter name=oceanbase-ce
```

## Start OceanBase
```bash
docker run -d --name oceanbase-ce --restart unless-stopped \
  -p 2881:2881 \
  -e MODE=mini \
  -e OB_TENANT_PASSWORD=ObDemo2026 \
  -e OB_DATABASE=supply_chain \
  oceanbase/oceanbase-ce
```

## Start existing container
```bash
docker start oceanbase-ce
```

## Stop container
```bash
docker stop oceanbase-ce
```

## Remove container
```bash
docker rm -f oceanbase-ce
```

## Verify connectivity
After starting, check the DB health endpoint:
```
GET http://127.0.0.1:8000/api/health/db
```
- `mode: "oceanbase-primary"` → OceanBase is working
- `mode: "sqlite-fallback"` → OceanBase unreachable

## .env configuration for OceanBase
```env
DATABASE_URL=mysql+pymysql://root%40test:ObDemo2026@127.0.0.1:2881/supply_chain?charset=utf8mb4
SQLITE_FALLBACK_URL=sqlite:///./schema/supply_chain.db
DATABASE_CONNECT_TIMEOUT_SECONDS=10
```

## Troubleshooting
- If backend starts before OceanBase is ready, it will use SQLite fallback
- Restart backend after OceanBase becomes available to switch back
- Check container logs: `docker logs oceanbase-ce`
