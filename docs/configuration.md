## Configuration

Use a `.env` file (python-dotenv is loaded automatically):

```
# .env
RSPORTAL_BASE_URL=https://localhost:8000
EDITOR=notepad
```

Notes:
- API base is resolved as `BASE_URL/api/v1` where `BASE_URL` comes from `RSPORTAL_BASE_URL` (preferred) or `RSPORTAL_API_BASE` for backward compatibility.
- You can still override via OS environment variables.
