# PrintTester

Python desktop application for generating print tickets and sending transactions to a server via an HTTP `POST` request.

## Features

- Add text and line breaks.
- Set alignment to left, center, or right.
- Toggle bold text.
- Add a paper feed of 1 to 255 lines.
- Review, remove, or clear operations before printing.
- Send requests in the background to keep the interface responsive.

## Requirements

- Python 3 with Tkinter available.
- A print server accessible from the machine.

The application uses only Python standard library modules; no additional packages need to be installed.

## Execution

From the project folder, run:

```powershell
python main.py
```

Enter the full print endpoint URL into the application. You can also define it before starting the application:

```powershell
$env:PRINT_SERVER_URL = "http://localhost:5000/print"
python main.py
```

The URL configured in the environment variable appears initially in the application field, where it can also be edited.

## Request Format

PrintTester sends a `POST` request with the `Content-Type: application/json` header. The body contains an ordered list of operations:

```json
{
"operations": [
{ "action": "alignment", "data": "C" },
{ "action": "boldText", "data": "1" },
{ "action": "text", "data": "Hi" },
{ "action": "boldText", "data": "0" },
{ "action": "enter", "data": "" },
{ "action": "feed", "data": "3" }
]
}
```

Supported operations:

| `action` | `data` | Description |
| --- | --- | --- |
| `text` | Text | Prints the specified text. |
| `enter` | Empty string | Inserts a line break. |
| `alignment` | `L`, `C`, or `R` | Aligns left, center, or right. |
| `boldText` | `"0"` or `"1"` | Disables or enables bold text. |
| `feed` | String with a number between `1` and `255` | Advances the paper by that number of lines. |

The server must respond with JSON and confirm success using `{"status":"ok"}`. If printing fails, it can include a message in the `error` field—for example, `{"status":"error","error":"Printer unavailable"}`. The application retains the operations in the preview when it receives an error.

## Connection errors

If printing cannot be completed, verify that the URL includes the correct endpoint path, that the server is accessible, and that it responds with JSON. The application waits up to 15 seconds for the response.