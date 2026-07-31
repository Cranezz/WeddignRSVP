# RSVP — connecting the guest list

The guest list lives in a Google Sheet. The website never receives the
whole list: it asks an Apps Script for names matching what the guest
typed, and only matching households come back.

That matters. The list contains children's names, and this repository is
public. Publishing the sheet as CSV would put every name one URL away.

## The sheet

One spreadsheet, two tabs.

### Tab `Guests` — one row per household

| id | household | adults | children | plus_one |
|----|-----------|--------|----------|----------|
| 1 | The Whitfield Family | Marcus Whitfield, Elena Whitfield | Nora Whitfield, Theo Whitfield | no |
| 2 | Dana Reyes | Dana Reyes | | yes |
| 3 | Samuel Okafor | Samuel Okafor | | no |

- **id** — anything unique. Numbers are fine. Don't reuse one.
- **household** — how the greeting reads. "The Whitfield Family", or just
  a name for a single guest.
- **adults** — comma separated. Everyone who gets their own seat.
- **children** — comma separated, or blank.
- **plus_one** — `yes` or `no`. `yes` adds one more seat and a box for
  the guest's name.

Searching matches on the start of any word in that row, so "reyes",
"dana" and "rey" all find row 2 — and it tolerates typos, so "Rayes"
and "Whitfeild" work too. If two households match, the site asks which
one rather than guessing.

How much misspelling is allowed scales with word length: three letters
or fewer must be exact (at that size one typo turns a real name into a
different real name), four to six letters allow one error, seven or more
allow two. Results come back sorted by how close the match was.

### Tab `Replies` — written by the script

Put these headers in row 1 and leave the rest empty:

    timestamp | party_id | household | name | type | attending | meal | dietary | email

One row per person. When someone changes their answer the old rows for
that household are removed first, so the sheet always shows one current
answer per person — safe to count directly.

## The Apps Script

In the spreadsheet: **Extensions → Apps Script**. Delete what's there and
paste this.

```js
const GUESTS  = 'Guests';
const REPLIES = 'Replies';
const NOTIFY  = 'lcrane644@gmail.com';   // '' to turn emails off

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function norm(s) {
  return String(s || '').toLowerCase().replace(/[^a-z\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

function readGuests() {
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(GUESTS);
  const values = sh.getDataRange().getValues();
  const head = values.shift().map(h => String(h).trim().toLowerCase());
  const col = name => head.indexOf(name);

  return values
    .filter(r => String(r[col('id')]).trim() !== '')
    .map(r => {
      const get  = k => String(r[col(k)] == null ? '' : r[col(k)]).trim();
      const list = k => get(k).split(',').map(s => s.trim()).filter(Boolean);
      return {
        id: get('id'),
        household: get('household'),
        adults: list('adults'),
        children: list('children'),
        plusOne: /^(y|yes|true|1)$/i.test(get('plus_one'))
      };
    });
}

// ---- Name matching (mirrors the same functions in index.html) ----

// Levenshtein distance, abandoned once it exceeds max.
function editDistance(a, b, max) {
  const la = a.length, lb = b.length;
  if (Math.abs(la - lb) > max) return max + 1;

  let prev = [], cur = [];
  for (let j = 0; j <= lb; j++) prev[j] = j;

  for (let i = 1; i <= la; i++) {
    cur[0] = i;
    let best = i;
    for (let j = 1; j <= lb; j++) {
      const cost = a.charAt(i - 1) === b.charAt(j - 1) ? 0 : 1;
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
      if (cur[j] < best) best = cur[j];
    }
    if (best > max) return max + 1;
    prev = cur.slice();
  }
  return prev[lb];
}

// Short words get no latitude: at three letters one typo turns a real
// name into a different real name.
function slack(token) {
  if (token.length <= 3) return 0;
  if (token.length <= 6) return 1;
  return 2;
}

function tokenScore(token, words) {
  const allow = slack(token);
  let best = null;
  for (const w of words) {
    if (w.indexOf(token) === 0) return 0;
    if (allow) {
      const d = editDistance(token, w, allow);
      if (d <= allow && (best === null || d < best)) best = d;
    }
  }
  return best;
}

// Every word typed must land somewhere in the household. The total is
// how far off the query was overall — lower sorts first.
function doGet(e) {
  const tokens = norm((e && e.parameter && e.parameter.q) || '').split(' ').filter(Boolean);
  if (!tokens.length) return json({ parties: [] });

  const scored = [];
  readGuests().forEach(p => {
    const words = norm([p.adults.join(' '), p.children.join(' '), p.household].join(' '))
      .split(' ').filter(Boolean);
    let total = 0;
    for (const t of tokens) {
      const s = tokenScore(t, words);
      if (s === null) return;
      total += s;
    }
    scored.push({ party: p, score: total });
  });

  scored.sort((a, b) => a.score - b.score);
  return json({ parties: scored.map(s => s.party) });
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const data = JSON.parse(e.postData.contents);
    const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(REPLIES);
    const values = sh.getDataRange().getValues();

    // Clear this household's previous answer. Walk backwards — deleting
    // a row shifts everything below it up.
    for (let i = values.length - 1; i >= 1; i--) {
      if (String(values[i][1]) === String(data.partyId)) sh.deleteRow(i + 1);
    }

    (data.people || []).forEach(p => {
      sh.appendRow([
        new Date(), data.partyId, data.household, p.name, p.type,
        p.attending ? 'yes' : 'no', p.meal || '',
        data.dietary || '', data.email || ''
      ]);
    });

    if (NOTIFY) {
      const going = (data.people || []).filter(p => p.attending).length;
      MailApp.sendEmail(NOTIFY, 'RSVP: ' + data.household,
        data.household + ' replied — ' + going + ' attending.\n\n' +
        (data.people || []).map(p => '  ' + p.name + ': ' + (p.attending ? 'yes' : 'no')).join('\n') +
        (data.dietary ? '\n\nDietary: ' + data.dietary : ''));
    }

    return json({ ok: true });
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}
```

`LockService` is not optional. Two households replying in the same second
will otherwise interleave their row deletions and corrupt each other's
answers.

## Deploying

1. **Deploy → New deployment → Web app.**
2. **Execute as: Me.**
3. **Who has access: Anyone.** Not "Anyone with a Google Account" — that
   forces guests to sign in and most will give up.
4. Authorize it. Google shows an "unverified app" warning for your own
   script; **Advanced → Go to project** is the way through.
5. Copy the URL. It ends in `/exec`, not `/dev`.

Paste that URL into `index.html`:

```js
var RSVP_API = "https://script.google.com/macros/s/AKfy.../exec";
```

With it set, the sample-invitation buttons hide themselves and the page
runs entirely off the sheet.

**The gotcha that catches everyone:** editing the script does nothing to
the live URL until you run **Deploy → Manage deployments → ✏️ → Version:
New version → Deploy**. Same URL, new code. If a change seems to have no
effect, this is why.

## Meal choices

Not asked at all right now. In `index.html`:

```js
var MEALS = [];
```

Fill it in once the caterer is booked and a dinner question appears for
every attending guest, and flows through to the `meal` column:

```js
var MEALS = ["Chicken", "Beef", "Vegetarian"];
```

## Known limits

- **No login.** Anyone who can guess a guest's name can see that
  household's invitation and reply for them. Standard for wedding sites,
  worth knowing.
- **Apps Script is slow to wake.** The first search after a quiet spell
  can take a couple of seconds. The button says "Looking…" so it doesn't
  read as broken.
- **Failures are handled, not hidden.** If the script can't be reached
  the guest is told to try again or email, rather than silently losing
  their reply.
