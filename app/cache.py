query_cache = {}
result_cache = {}


def get_cached_sql(question: str):
    return query_cache.get(question)


def set_cached_sql(question: str, sql: str):
    query_cache[question] = sql


def get_cached_result(sql: str):
    return result_cache.get(sql)


def set_cached_result(sql: str, result):
    result_cache[sql] = result