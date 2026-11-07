# ✈️ Flight Deal Finder

Your personal flight search. You enter a trip, and it searches Google Flights (through SerpApi) across all airlines. It works out the **real cost** of each option (fare + bag fees, with your free United bag counted) and ranks the options by value, not just by ticket price.

It runs on your own computer as a web page at http://localhost:5055.

---

## Setup (one time, about 10 minutes)

### 1. Install Python (skip if you already have it)
- **Mac or Windows:** download Python from https://www.python.org/downloads/ and run the installer.
  - **Windows:** on the first installer screen, tick **"Add python.exe to PATH"**.
- To check that it worked, open **Terminal** (Mac) or **Command Prompt** (Windows) and type `python3 --version` (Windows: `py --version`). You should see `Python 3.x.x`.

### 2. Get this folder onto your computer
On GitHub, open this repository and choose the `claude/flight-deal-finder-0728g7` branch (or `main` once it's merged). Click the green **Code** button, then **Download ZIP**, and unzip it. The app is in the `flight-deal-finder` folder.

### 3. Get your free SerpApi key
1. Go to https://serpapi.com and click **Register**. The free plan doesn't need a credit card.
2. Verify your email (and phone number, if it asks).
3. Open https://serpapi.com/manage-api-key and copy your **Private API Key**.

### 4. Start the app
- **Mac:** double-click **`start-mac.command`**. If macOS says it's from an unidentified developer, right-click it, choose **Open**, then click **Open** again.
- **Windows:** double-click **`start-windows.bat`**.
- **Or** in Terminal or Command Prompt, go into the folder and run:
  ```
  python3 run.py          (Windows: py run.py)
  ```

The first start takes about a minute while it installs what it needs. After that it starts right away, and your browser opens the page.

### 5. Add your key
The app starts in **DEMO MODE**, which shows fake prices so you can try it out. To switch to real flights, paste your key into the yellow box on the right of the search page and click **Save key**.

The key is saved only in a file called `.env` inside the folder. It never goes into the code and is never uploaded anywhere. (You can also open `.env` in a text editor and fill in `SERPAPI_KEY=`. On a Mac, press Cmd+Shift+. in Finder to show hidden files.)

**To stop the app:** close the Terminal or Command Prompt window, or press Ctrl+C in it.

---

## Using it

**Search form**
- **From:** PHX by default. Tick the box to also include Mesa (AZA) and Tucson (TUS).
- **To:** an airport code (`DEN`), several codes (`LAX,SAN`), a city (`Chicago`, `New York`, `Hawaii`), or `anywhere`. "Anywhere" shows the cheapest destinations; click one to see its full flight list.
- **Dates:** exact dates, flexible ±1 to 3 days, or "any weekend in a month" (Fri→Sun, Thu→Sun, Fri→Mon or Sat→Sun).
- **Filters:** max stops, max total travel time, max/min layover, cabin, preferred / only / excluded airlines, and departure and arrival time windows.
  - Time windows are "soft" by default: flights outside them still show but score lower. Tick "Hide flights outside my windows" to remove them.
- **Bags:** how many carry-ons and checked bags you're bringing (per person, each way).

**Results**
- **🏆 Best value**, **💰 Cheapest overall** and **⚡ Fastest under $X**. X defaults to 25% above the cheapest price, or you can set it yourself.
- **Price calendar** (flexible-date searches): the cheapest all-in price for each departure date. Green is cheap, red is expensive, and the cheapest date is outlined.
- **Table:** the top 10 by score, or click "Show all". Click any column header to sort.
- **All-in price** = fare + estimated bag fees. The flags explain each one:
  - 🔴 **Basic economy** and **No carry-on allowed**: if you're bringing a carry-on, the estimated gate-check cost is included.
  - 🔴 **Carry-on costs extra**: budget airlines like Spirit and Frontier.
  - 🟢 **United card: 1st bag free**: your Chase United Explorer card. Pay with the card and add your MileagePlus number when booking.
- **Score (0–100):** a mix of all-in price, travel time, number of stops and fit with your time windows. Use the **Re-rank** sliders to change what matters. Re-ranking is free and uses no credits.
- **Round trips:** click **Pick return →** on an outbound flight to see the return options, then **Book →**.
- **Book →** lists where you can buy the ticket (airline site, Expedia, etc.) and sends you to that site.

**Past searches** are saved automatically. Open one, or click "Edit & rerun".

---

## About API credits (important on the free plan)

The free SerpApi plan gives **250 searches a month (max 50 per hour)**. The searches-left count is shown at the top right of the page.

| Action | Credits |
|---|---|
| Search with exact dates | 1 |
| Flexible ±3 days | up to 7 (one per date) |
| Weekends in a month | 4–5 |
| "Pick return" on a round trip | 1 |
| "Book" (getting booking links) | 1 |
| Re-ranking, sorting, opening past searches | 0 |
| Repeating a search within 6 hours | 0 (saved results are reused) |

- If a search would use more than 3 credits, the app asks first.
- Searches that need more than 14 credits are blocked.
- When you hit your limit, you'll see a clear red message. Saved results still work.
- You can change these numbers in `.env` (`CACHE_HOURS`, `CONFIRM_ABOVE_CREDITS`, `MAX_CREDITS_PER_SEARCH`).
- If you use it a lot, SerpApi's $25/month plan gives 1,000 searches.

---

## Price alerts 🔔

Under any search's results, set a **target price** and click **Save alert**. The app re-checks the search every 12 hours while it's running and records any price drop on the **Price alerts** page. The menu shows a red badge when there's news.

**Get alerts on your phone (optional, free):**
1. Install the **ntfy** app (iPhone or Android) from https://ntfy.sh.
2. In the app, subscribe to a topic with a long, hard-to-guess name, such as `trevor-flights-8k2m9q`. Anyone who knows the name can read it.
3. In `.env`, set `NTFY_TOPIC=trevor-flights-8k2m9q` and restart the app.

**Check alerts even when the app is closed (optional):** tell your computer to run `python3 run.py --check-alerts` from this folder a couple of times a day.
- **Mac:** in Terminal, run `crontab -e` and add a line like
  `0 8,18 * * * cd /path/to/flight-deal-finder && /usr/bin/env python3 run.py --check-alerts`
- **Windows:** use Task Scheduler. Create a Basic Task with the action "Start a program": `py`, arguments `run.py --check-alerts`, and "Start in" set to this folder.

Each alert check uses the same number of credits as the search itself, so prefer exact-date alerts.

---

## Settings you can change
- **`.env`:** API key, cache time, credit limits, `UNITED_EXPLORER_CARD=yes/no`, alert frequency, ntfy topic and port.
- **`finder/bag_fees.py`:** the bag fee for each airline. These are **estimates** of typical prepaid prices; airlines change them often. Edit a number and restart.
- **`finder/airports.py`:** nearby airports and city names.

## Good to know
- Bag fees are estimates. Always check the final price on the airline's site before you pay.
- For round trips, the first results list assumes the same airline both ways. Once you pick a return flight, each direction uses its own airline's fees.
- Time windows apply to the outbound flight.
- "Anywhere" prices are Google's quick estimates (fare only). Click a destination to see full flight details with bag fees.
- Results come from Google Flights through SerpApi. If an airline doesn't sell through Google Flights, it won't appear.

## Troubleshooting
- **"command not found: python3"** (Mac): install Python from python.org (step 1). On Windows, use `py` instead of `python3`.
- **The page doesn't open:** go to http://localhost:5055 yourself. If another program uses that port, change `PORT=` in `.env`.
- **"API key isn't valid":** paste the key again, or fix `SERPAPI_KEY=` in `.env`, and restart.
- **"You've hit your SerpApi search limit":** wait for the hourly or monthly reset, or upgrade your plan.
- **Start fresh:** delete the `data` folder to erase history, alerts and saved results. Delete `.venv` to reinstall.

## For the curious (tests)
`python3 run.py` sets up `.venv`. Run the automated tests with `.venv/bin/python -m unittest discover` (Windows: `.venv\Scripts\python -m unittest discover`).
