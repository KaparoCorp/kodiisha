from django.core.paginator import Paginator


PAGE_SIZE_OPTIONS = (10, 50, 100, 150)


def paginate_queryset(request, queryset, default_per_page=10):
    try:
        per_page = int(request.GET.get('per_page', default_per_page))
    except (TypeError, ValueError):
        per_page = default_per_page

    if per_page not in PAGE_SIZE_OPTIONS:
        per_page = default_per_page

    paginator = Paginator(queryset, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    query_params = request.GET.copy()
    query_params.pop('page', None)
    querystring = query_params.urlencode()

    current = page_obj.number
    page_numbers = [
        page_number
        for page_number in (current - 1, current, current + 1)
        if 1 <= page_number <= paginator.num_pages
    ]

    return {
        'page_obj': page_obj,
        'page_size_options': PAGE_SIZE_OPTIONS,
        'selected_per_page': per_page,
        'pagination_querystring': querystring,
        'page_numbers': page_numbers,
    }
