# Job Hunter Bot

A Python bot that reads your LinkedIn profile, scans Allan Gray (and the wider web) for developer roles that match your experience, alerts you when new jobs appear, suggests CV improvements, and includes direct apply links.

## What it does

1. **Profile scan** - Parses your LinkedIn profile from JSON, PDF export, or plain text
2. **Job search** - Scrapes [Allan Gray Careers](https://www.allangray.co.za/careers/) and runs targeted web searches
3. **Matching** - Scores each role against your skills and experience
4. **Alerts** - Console, desktop (`notify-send`), email, or webhook (Slack/Discord)
5. **CV advice** - Rule-based tips plus optional OpenAI-powered suggestions
6. **Apply links** - SuccessFactors application URLs for each vacancy

## Quick start

```bash
cd /agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml
cp profile.example.json profile.json   # edit with your real profile
```

### Option A: JSON profile (recommended)

Edit `profile.json` with your skills, experience, and summary from LinkedIn.

### Option B: LinkedIn PDF export

On LinkedIn: **Me → View profile → More → Save to PDF**

```bash
python run.py profile --pdf ~/Downloads/Profile.pdf --save profile.json
```

### Option C: Copy-paste text

Save your LinkedIn profile text to `linkedin.txt`, then:

```bash
python run.py profile --text linkedin.txt --save profile.json
```

> **Note:** LinkedIn blocks automated scraping of live profile pages. Use PDF export or manual JSON for reliable results.

## Commands

```bash
# One-time scan (alerts only for newly discovered jobs)
python run.py scan

# Scan and show all matches, even previously seen
python run.py scan --all

# Write a JSON report
python run.py scan --report data/latest-matches.json

# Continuous monitoring (default: every 6 hours)
python run.py watch

# View job history
python run.py history
python run.py history --export data/job-history.json
```

## Windows .exe (background + email)

You can package this as a **single `.exe`** that runs silently in the background and emails you when new Allan Gray developer jobs appear.

### Build on your Windows laptop

Requirements: [Python 3.11+](https://www.python.org/downloads/) installed with "Add to PATH" checked.

```bat
cd path\to\job-hunter-bot
build.bat
```

This creates `dist\JobHunterBot.exe` (no console window).

### Configure email alerts

Edit `dist\config.yaml`:

```yaml
alerts:
  console: false         # no terminal when running as .exe
  desktop: true          # optional Windows toast popups
  email:
    enabled: true
    to: your-email@gmail.com
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_user: your-email@gmail.com
    smtp_password: ""    # leave blank and use env var instead (safer)
```

**Gmail users:** create an [App Password](https://myaccount.google.com/apppasswords) (requires 2FA). Set it as a Windows environment variable so it is not stored in plain text:

```bat
setx JOB_HUNTER_SMTP_PASSWORD "your-16-char-app-password"
```

**Outlook/Hotmail:** use `smtp.office365.com` port `587` with your Microsoft account.

Test email delivery:

```bat
dist\JobHunterBot.exe test-email
```

### Run in the background

**Option A - Task Scheduler (recommended):**

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-windows-task.ps1
```

Starts automatically when you log in. Logs go to `dist\data\job-hunter.log`.

**Option B - Double-click:**

Run `scripts\start-background.vbs` after editing `dist\config.yaml` and `dist\profile.json`.

**Option C - Manual:**

```bat
dist\JobHunterBot.exe watch
```

The bot checks every 6 hours (change `search.poll_interval_hours` in config.yaml).

### What you get by email

Each new matching job email includes:

- Job title, company, location, closing date
- Match score and why it fits your profile
- CV improvement suggestions
- Direct **Apply** link (SuccessFactors)

---

## Alerts (all platforms)

Edit `config.yaml`:

| Channel | Config |
|---------|--------|
| Console | `alerts.console: true` (default) |
| Desktop | `alerts.desktop: true` (Linux notify-send) |
| Email | `alerts.email.enabled: true` + SMTP settings |
| Webhook | `alerts.webhook_url: https://hooks.slack.com/...` |

## Smarter CV suggestions (optional)

Set your OpenAI API key in `config.yaml` or as `OPENAI_API_KEY`. Without it, the bot uses built-in rule-based CV tips.

## Scheduling with cron

Run every 6 hours:

```cron
0 */6 * * * cd /agent && .venv/bin/python run.py scan >> data/cron.log 2>&1
```

## Current Allan Gray developer roles

The bot monitors the Allan Gray careers carousel and SuccessFactors listings. As of setup, roles like **Developer II** appear on their careers page with apply links to SuccessFactors.

All vacancies portal: [Allan Gray SuccessFactors](https://career2.successfactors.eu/career?company=allangrayp&career_ns=job_listing_summary&navBarLevel=JOB_SEARCH&rcm_site_locale=en_GB&selected_lang=en_GB)

## Project layout

```
/agent
├── run.py                 # CLI entry point
├── config.example.yaml
├── profile.example.json
├── requirements.txt
└── src/
    ├── bot.py             # Orchestration
    ├── profile/           # LinkedIn parsing
    ├── jobs/              # Allan Gray + web search
    ├── matching/          # Profile-to-job scoring
    ├── cv/                # CV suggestions
    ├── alerts/            # Notifications
    └── storage/           # SQLite job history
```

## License

MIT
