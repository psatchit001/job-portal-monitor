# How Job Postings Work: From Opening to the Public

## The Flow When a Company Creates a New Opening

```
Hiring Manager approves the role
        ↓
HR/Recruiter creates the job posting inside their ATS
        ↓
ATS automatically publishes it everywhere simultaneously
```

The ATS (Applicant Tracking System) is the **internal software the company uses to manage hiring** — posting jobs, collecting applications, scheduling interviews, tracking candidates. Companies like Texas Instruments, Google, Meta — they don't build their own hiring software. They pay for one of these platforms.

---

## Where Greenhouse, Lever, Workday, iCIMS Fit In

They are the ATS vendors. The company is their *customer*. When a recruiter at EchoStar clicks "Publish" on a new job posting inside iCIMS, iCIMS simultaneously:

1. Posts it on the company's own careers page (e.g. `jobs.echostar.com`) — which is just an iCIMS-hosted page with EchoStar's branding on top
2. Sends it to **Indeed, LinkedIn, Glassdoor, ZipRecruiter** automatically (called "job board syndication")
3. Makes it available via their API

So `jobs.echostar.com` **is** iCIMS — it's just skinned to look like EchoStar's website.

---

## Why This Matters for Career Portal Monitoring

| ATS | Approach for Monitoring |
|---|---|
| **Greenhouse** | Free public API at `boards-api.greenhouse.io/v1/boards/{company}/jobs` — no browser needed, instant, reliable |
| **Lever** | Free public API at `api.lever.co/v0/postings/{company}` — same |
| **Ashby** | Public API available |
| **Workday** | No public API, JS-rendered, requires browser automation |
| **iCIMS** | No public API, JS-rendered, requires browser automation |
| **Taleo** (Oracle) | No public API, JS-rendered, requires browser automation |
| **SmartRecruiters** | Has a public API |

For Greenhouse/Lever companies, a clean JSON API call returns all open roles in milliseconds — no browser automation, no risk of being blocked.

---

## Why Going Direct to ATS Beats LinkedIn/Indeed for Early Applications

LinkedIn alerts are **delayed** — sometimes hours to a day behind the actual ATS posting. Going direct to the ATS means you see the role the moment it's published — before LinkedIn even gets it. That's your early-applicant advantage.

- LinkedIn alerts are coarse — you can't filter by exact criteria per company
- 25-50 separate LinkedIn alerts all land in the same inbox as noise
- Direct ATS monitoring tells you "this role at TI just appeared 10 minutes ago"
