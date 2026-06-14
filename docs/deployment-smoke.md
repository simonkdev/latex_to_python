# Deployment Smoke Checklist

Run these checks after each Vercel deployment. Replace `$BASE_URL` with the deployed URL.

## Required Environment

- `CORS_ORIGINS` contains the production frontend origin and no wildcard origin.
- `ENABLE_DOCS=false` for public production deployments unless API docs are intentionally exposed.
- Production install uses `requirements.txt`.
- `uvicorn[standard]` is intentionally kept out of production dependencies because Vercel serves the ASGI app through `@vercel/python`; it remains in `requirements-dev.txt` for local development only.

## HTTP Checks

1. Frontend shell:

   ```bash
   curl -fsS "$BASE_URL/" | grep "LaTeX to Python Translator"
   ```

2. Health endpoint:

   ```bash
   curl -fsS "$BASE_URL/health"
   ```

   Expected JSON:

   ```json
   {"status":"healthy"}
   ```

3. Conversion endpoint:

   ```bash
   curl -fsS "$BASE_URL/api/v1/convert" \
     -H "Content-Type: application/json" \
     -d '{"latex":"\\frac{x+1}{x-1}","mode":"function","func_name":"f","backend":"python"}'
   ```

   Expected fields:

   - `error` is `null`
   - `error_code` is `null`
   - `variables` is `["x"]`
   - `symbol_map` is `{"x":"x"}`
   - `support_level` is `computed`
   - `backend` is `python`
   - `python` contains `def f(x):`

4. Static assets:

   ```bash
   curl -fsSI "$BASE_URL/static/style.css"
   ```

   Expected:

   - HTTP 200
   - `cache-control` contains `max-age=31536000`

5. Docs gating:

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" "$BASE_URL/docs"
   curl -s -o /dev/null -w "%{http_code}\n" "$BASE_URL/openapi.json"
   ```

   Expected in production with `ENABLE_DOCS=false`:

   - `/docs` returns 404
   - `/openapi.json` returns 404

