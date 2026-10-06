# Profile artwork

Run `python3 scripts/update_profile.py` to regenerate the SVGs and the public activity snapshot. No third-party Python packages are required. `PROFILE_DATE=YYYY-MM-DD` fixes the last day of the 365-day window for reproducible checks. `GH_TOKEN` is optional and is used only for GitHub API rate limits.

The contribution calendar comes from the public, unauthenticated GitHub contribution page. Repository counts include forks; original-repository and star totals exclude forks. Active days and streaks are calculated within the displayed 365-day window. A current streak can end yesterday when today has no contribution yet. Calendar counts can include anonymized private activity only when the account owner already displays it publicly. No private repository names or contents are requested or stored.

The daily workflow runs at 00:45 UTC and can also be dispatched manually from Actions. GitHub can delay scheduled runs and can disable them after prolonged repository inactivity. If fetching or parsing fails, the script stops before replacing the previous artwork and GitHub reports a failed workflow.

The terminal layout was inspired by [AVIVASHISHTA29's profile](https://github.com/AVIVASHISHTA29/AVIVASHISHTA29). This repository uses original artwork and rendering code, with Mohamed Rafiq's own profile information and public projects.

The original README is preserved on branch `backup/profile-before-refresh-2026-10-06`, starting at commit `6db06137165d39f8da19438976cc443117dc22a1`.
