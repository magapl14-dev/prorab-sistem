import os
import json
from datetime import datetime, timezone


def _get_client():
    try:
        import gspread
        from google.oauth2 import service_account
    except ImportError:
        raise RuntimeError("gspread/google-auth not installed. Run: pip install gspread google-auth")

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]

    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
    else:
        path = os.getenv("GOOGLE_CREDENTIALS_PATH", "/opt/prorab-sistem/google-credentials.json")
        if not os.path.exists(path):
            raise RuntimeError(
                f"Google credentials not found. Upload service-account JSON to {path} "
                "or set GOOGLE_CREDENTIALS_JSON env variable."
            )
        with open(path) as f:
            info = json.load(f)

    creds = service_account.Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds), info.get("client_email", "")


async def sync_project_to_sheet(project, records: list) -> dict:
    import asyncio
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_sync, project, records)


def _sync_sync(project, records: list) -> dict:
    client, svc_email = _get_client()

    spreadsheet = client.open_by_key(project.gsheet_id)

    # Use or create sheet named after project
    sheet_name = "Транзакции"
    try:
        ws = spreadsheet.worksheet(sheet_name)
    except Exception:
        ws = spreadsheet.add_worksheet(title=sheet_name, rows=5000, cols=20)

    kind_map = {
        "expense": "Расход",
        "master_payment": "Выплата мастеру",
        "client_payment": "Платёж клиента",
    }

    headers = [
        "Дата", "Вид", "Наименование", "Тип", "Категория", "Касса",
        "Кол-во", "Цена (₽)", "Сумма закупки (₽)", "Сумма с наценкой (₽)",
        "Комиссия прораба (₽)", "Сумма платежа (₽)", "Аванс?", "Представитель клиента",
        "Автор", "Комментарий",
    ]

    rows = [headers]
    for r in sorted(records, key=lambda x: (x.operation_date, x.created_at)):
        rows.append([
            str(r.operation_date),
            kind_map.get(r.kind, r.kind),
            r.name or "",
            r.type or "",
            r.category or "",
            r.kassa or "",
            float(r.qty or 1),
            float(r.price or 0),
            float(r.sum_buy or 0),
            float(r.sum_sell or 0),
            float(r.commission or 0),
            float(r.payment_amount or 0),
            "Да" if (r.kind == "client_payment" and getattr(r, "is_advance", False)) else "",
            r.client_rep_name or "",
            r.author.name if r.author else "",
            r.comment or "",
        ])

    ws.clear()
    ws.update(rows, value_input_option="USER_ENTERED")

    # Bold header row
    try:
        ws.format("A1:P1", {"textFormat": {"bold": True}, "backgroundColor": {"red": 0.95, "green": 0.88, "blue": 0.76}})
    except Exception:
        pass

    synced_at = datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")

    return {
        "synced": len(rows) - 1,
        "sheet_url": f"https://docs.google.com/spreadsheets/d/{project.gsheet_id}",
        "service_email": svc_email,
        "synced_at": synced_at,
    }
