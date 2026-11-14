"""Current configured native StockWiki math; never alters sys.path."""
def legacy_freshness_status(meta, now):
    from stockwiki.quick_scan_freshness import freshness_status
    return freshness_status(meta, now)

def legacy_ttl_valid_until(observed_at, ttl_hours):
    from stockwiki.quick_scan_freshness import ttl_valid_until
    return ttl_valid_until(observed_at, ttl_hours)
