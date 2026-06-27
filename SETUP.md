# VectorBlast Auto-Quantify — Setup Guide

This guide lets you run the VectorBlast auto-quantify bot on **your own** GitHub
account, for free, with **no computer required**. Once set up, GitHub's servers
will log into VectorBlast and click the "quantify" button for you automatically,
several times a day.

You do **not** need to know how to code. Just follow each step in order.
The whole thing takes about **10 minutes**.

---

## What you need

- A phone number + password for your **VectorBlast** account (the one you log in with).
- About 10 minutes.

---

## Step 1 — Create a free GitHub account

1. Go to **https://github.com/signup**
2. Enter your email, pick a password, pick a username.
3. Verify your email when GitHub asks.

That's it — a free account is all you need.

---

## Step 2 — Fork (copy) the bot into your account

"Forking" just means making your own personal copy of the project.

1. While logged in, open this link:
   **https://github.com/uh60down/vb-auto**
2. In the top-right corner, click the **Fork** button.
3. On the next screen, leave everything as-is and click **Create fork**.

You now have your own copy at `https://github.com/YOUR-USERNAME/vb-auto`.
Everything from here happens in **your** copy.

---

## Step 3 — Turn on Actions (this is required for forks)

GitHub turns off automation on forks by default, so you must enable it once.

1. In **your** copy of the repo, click the **Actions** tab (top menu).
2. You'll see a message saying workflows are disabled. Click the green button:
   **"I understand my workflows, go ahead and enable them"**.

Done. Automation is now allowed.

---

## Step 4 — Add your VectorBlast login (Secrets)

These are stored **encrypted** and are only used by the bot to log in. Nobody,
including the project owner, can read them.

1. In your repo, click **Settings** (top menu).
2. In the left sidebar, click **Secrets and variables** → **Actions**.
3. Click the green **New repository secret** button and add the **first** secret:

   - **Name:** `VB_ID_CODE`
   - **Secret:** your country code, written **with the plus sign**, e.g. `+82`
   - Click **Add secret**.

4. Click **New repository secret** again and add the **second** secret:

   - **Name:** `VB_ID_PHONENUMBER`
   - **Secret:** your phone number **without** the country code, e.g. `1012345678`
   - Click **Add secret**.

5. Click **New repository secret** one more time and add the **third** secret:

   - **Name:** `VB_PASSWORD`
   - **Secret:** your VectorBlast password
   - Click **Add secret**.

> ⚠️ The three names must be **exactly** as written above (all capital letters,
> with underscores). A typo here is the most common reason the bot fails.

When finished, your Secrets page should list exactly three secrets:
`VB_ID_CODE`, `VB_ID_PHONENUMBER`, `VB_PASSWORD`.

---

## Step 5 — Test it once (manually)

Let's make sure it works before leaving it on autopilot.

1. Click the **Actions** tab.
2. On the left, click the **Auto Quantify** workflow.
3. On the right, click the **Run workflow** button → then the green
   **Run workflow** confirmation button.
4. Wait about 1–2 minutes. Refresh the page.
5. A new run appears. If it has a **green check ✅**, it worked! 🎉
   If it has a **red X ❌**, see Troubleshooting below.

---

## Step 6 — That's it — it now runs automatically

You don't need to do anything else. GitHub will automatically run the bot
**several times every hour** (at :07, :17, :27 and :47) and stop once your daily
quantify limit is used up. Your phone/PC can be off — it all runs on GitHub's servers.

> Note: GitHub sometimes skips a scheduled time when its servers are busy.
> That's normal and harmless — the bot runs again at the next slot, and your
> daily limit still gets used up. You don't need to do anything.

---

## Troubleshooting

**The test run failed (red ❌).**
Click the failed run, then click the **quantify** job to read the log.

- **Most common cause:** a secret name is misspelled or a value is wrong.
  Go back to Step 4 and check that the three names are exactly
  `VB_ID_CODE`, `VB_ID_PHONENUMBER`, `VB_PASSWORD`, and that:
  - `VB_ID_CODE` starts with a `+` (e.g. `+82`)
  - `VB_ID_PHONENUMBER` has **no** country code in it
  - `VB_PASSWORD` is your correct password
- After fixing a secret, just run the test again (Step 5).

**I don't see scheduled runs appearing on their own.**
A brand-new fork can take an hour or two before the automatic schedule starts.
Give it some time. The manual test (Step 5) works immediately regardless.

**I want to stop the bot.**
Go to **Actions** → **Auto Quantify** → the **•••** menu → **Disable workflow**.

---

## Quick reference

| Secret name          | What to put                          | Example       |
|----------------------|--------------------------------------|---------------|
| `VB_ID_CODE`         | Country code **with** `+`            | `+82`         |
| `VB_ID_PHONENUMBER`  | Phone number **without** country code| `1012345678`  |
| `VB_PASSWORD`        | Your VectorBlast password            | `••••••••`    |

Runs automatically at **:07, :17, :27 and :47 every hour**. Nothing else to do. ✅
