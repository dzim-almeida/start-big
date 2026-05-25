from typing import Tuple

def _set_pagination(
    total_items: int,
    filters:dict,
    page: int,
    limit: int
) ->  Tuple[int, dict]:
    
    if filters:
        next_link = 'ordens-servico/?'
        prev_link = 'ordens-servico/?'
    
        search_query = filters.get('search')
        if search_query:
            next_link = f"{next_link}search={search_query}&"
            prev_link = f"{prev_link}search={search_query}&"

        status_query = filters.get('status')
        if status_query:
            next_link = f"{next_link}status={status_query}&"
            prev_link = f"{prev_link}status={status_query}&"\
            
        priority_sort_query = filters.get('priority_sort')
        if priority_sort_query:
            next_link = f"{next_link}priority_sort={priority_sort_query}&"
            prev_link = f"{prev_link}priority_sort={priority_sort_query}&"

    total_pages = (
        total_items // limit
        if total_items % limit == 0
        else total_items // limit + 1
    )

    links = {
        "next": f"{next_link}page={page + 1}&limit={limit}" if page < total_pages else None,
        "prev": f"{prev_link}page={page - 1}&limit={limit}" if page > 1 else None
    }

    return (total_pages, links)
    
    
    
    
