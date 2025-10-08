## Quickstart

- Install dependencies (optional): `pip install -r requirements.txt`
- Run: `python main.py -h`

Windows PowerShell:

```
$env:EDITOR = "notepad"   # or code/vim
$env:RSPORTAL_API_BASE = "https://your.api"
```

- Authenticate:
```
python main.py auth login
```
- Pull tasks:
```
python main.py pull tasks
```
- Track time:
```
python main.py time start -t TASK-123
python main.py time stop -t TASK-123
```
- View logs:
```
python main.py log summary
```
