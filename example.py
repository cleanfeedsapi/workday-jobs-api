import json, sys, urllib.request

def workday_jobs(host, tenant, site):
    base = f"https://{host}/wday/cxs/{tenant}/{site}"
    offset, seen = 0, set()
    while True:  # "total" is unreliable on Workday; stop when a page repeats
        body = json.dumps({"appliedFacets": {}, "limit": 20, "offset": offset, "searchText": ""}).encode()
        req = urllib.request.Request(f"{base}/jobs", data=body, method="POST",
              headers={"Content-Type": "application/json", "Accept": "application/json",
                       "User-Agent": "your-app/1.0 (contact@example.com)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        page = [j for j in d.get("jobPostings") or [] if j.get("externalPath") not in seen]
        if not page:  # empty, or the last page served again: Workday caps a query at 2,000 postings
            return
        seen.update(j.get("externalPath") for j in page)
        if offset % 500 == 0:
            print(f"{offset} postings so far...", file=sys.stderr)
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
