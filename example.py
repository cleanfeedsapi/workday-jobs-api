import json, urllib.request

def workday_jobs(host, tenant, site):
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    offset, total = 0, None
    while total is None or offset < total:
        body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}).encode()
        req = urllib.request.Request(f"{base}/jobs", data=body, method="POST",
              headers={"Content-Type": "application/json", "Accept": "application/json",
                       "User-Agent": "your-app/1.0 (contact@example.com)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        if total is None:
            total = int(d.get("total") or 0)
        page = d.get("jobPostings") or []
        if not page:
            return
        for j in page:
            yield {"id": (j.get("bulletFields") or [None])[0], "title": j["title"],
                   "location": j.get("locationsText"), "posted": j.get("postedOn"),
                   "url": f"https://{host}/{site}{j['externalPath']}"}
        offset += len(page)

def diff(prev_path, rows):
    """Return (new, closed) ids versus a previous JSON snapshot."""
    try:
        prev = {r["id"] for r in json.load(open(prev_path))}
    except FileNotFoundError:
        prev = set()
    cur = {r["id"] for r in rows}
    return sorted(cur - prev), sorted(prev - cur)

if __name__ == "__main__":
    rows = list(workday_jobs("nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite"))
    print(len(rows), "jobs"); print(rows[0])
