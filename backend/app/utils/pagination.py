def normalize_pagination(page: int = 1, page_size: int = 20) -> tuple[int, int]:
    page = max(page, 1)
    page_size = max(1, min(page_size, 200))
    return page, page_size
