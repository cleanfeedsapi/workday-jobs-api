# Workday Jobs API: how to list every posting from any Workday career site (myworkdayjobs.com) as JSON

Every Workday career site (`https://{tenant}.{wd1..wd5}.myworkdayjobs.com/{site}`) is driven by a **public JSON endpoint** that the page itself calls. No key, no login. This repository documents that endpoint, its POST body, the `offset` pagination quirk, the detail endpoint, and ships a dependency-free Python example.

## The endpoints

```
POST https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
     Content-Type: application/json
     {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}

GET  https://{tenant}.{wdN}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{externalPath}
```

Example: `https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite` → tenant `nvidia`, host `nvidia.wd5.myworkdayjobs.com`, site `NVIDIAExternalCareerSite`. Localized sites add a language segment (`/en-US/External`); the `cxs` path uses the site name without it.

## What you get back

List endpoint: `{"total": 1234, "jobPostings": [...], "facets": [...]}`. Each posting:

| Field | Example | Notes |
|---|---|---|
| `title` | `Senior Software Engineer, CUDA` | |
| `externalPath` | `/job/US-CA-Santa-Clara/Senior-Software-Engineer_JR1985000` | append to `https://{host}/{site}` for the page, or to the `cxs` base for JSON detail |
| `locationsText` | `US, CA, Santa Clara` | |
| `postedOn` | `Posted 3 Days Ago` | relative text only on the list; absolute date is in the detail |
| `bulletFields[]` | `["JR1985000"]` | usually the requisition id, use it as the stable id |

Detail endpoint (`GET .../wday/cxs/{tenant}/{site}{externalPath}`): `jobPostingInfo` with `jobDescription` (HTML), `location`, `additionalLocations`, `startDate` (ISO date), `timeType`, `jobReqId`, `externalUrl`, `country`.

## Pagination quirks

* `limit` is capped at **20** per request.
* `total` is reliable on the first page only; later pages often return `total: 0`, so remember the first value.
* Walk `offset` in steps of 20 until `jobPostings` is empty or you reach the remembered total.
* `searchText` and `appliedFacets` (e.g. `{"locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"]}`) filter server-side; facet ids come from the `facets` array of the first response.

## Python example (stdlib only)

```python
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

if __name__ == "__main__":
    rows = list(workday_jobs("nvidia.wd5.myworkdayjobs.com", "nvidia", "NVIDIAExternalCareerSite"))
    print(len(rows), "jobs"); print(rows[0])
```

## Finding Workday career sites

Search `site:myworkdayjobs.com`. Large employers on Workday include NVIDIA, Adobe, Salesforce, Dell, Nike, Comcast, Humana and most Fortune 500 HR departments.

## Common questions

**Is this an official API?** It is the JSON backend of the public career site (the `cxs` "candidate experience service"); Workday does not publish it for third parties, but it is unauthenticated and stable since 2019. Treat it respectfully and cache.

**Why does the first request sometimes 404?** The site name is case-sensitive and must not include the language segment.


## Hosted version, pay per result

If you would rather not run and maintain this yourself, the same logic runs as a pay-per-result Apify Actor by CleanFeeds: https://apify.com/cleanfeedsapi/workday-jobs-api ($1.50 per 1,000 rows, no subscription, JSON/CSV/Excel export, API, scheduling, n8n/Make/Zapier and MCP integrations). A multi-ATS variant that mixes Greenhouse, Lever, Ashby, Workday, SmartRecruiters and Recruitee boards in one run: https://apify.com/cleanfeedsapi/ats-jobs-feed

Free sample data: a daily snapshot of about 10,000 open roles at 26 tech companies from these endpoints, CC BY 4.0: https://huggingface.co/datasets/cleanfeeds/tech-jobs-daily

More feeds: https://cleanfeeds.dev

## Legal note

These are public, unauthenticated endpoints that the career pages themselves load. Job postings are employer announcements and belong to the employers. Be polite: identify your client with a User-Agent, cache results, and do not hammer the endpoints. Nothing here is affiliated with or endorsed by Workday.
