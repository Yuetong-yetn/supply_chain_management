from typing import Any


def success_response(data: Any = None, message: str = "ok") -> dict[str, Any]:
    return {"success": True, "message": message, "data": data}


def error_response(message: str, data: Any = None) -> dict[str, Any]:
    return {"success": False, "message": message, "data": data}


def page_response(items: list[Any], total: int, page: int, page_size: int, message: str = "ok") -> dict[str, Any]:
    return success_response(
        {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        },
        message=message,
    )
