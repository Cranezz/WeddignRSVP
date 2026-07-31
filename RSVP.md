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

One row per person, with that person's own `dietary` note — the kitchen
plates per head, so "no nuts for one of us" is no use without knowing
which one.

When someone changes their answer the old rows for that household are
removed first, so the sheet always shows one current answer per person —
safe to count directly.

A household that has already replied is recognised on their next search:
`doGet` returns their existing answers alongside the invitation, and the
site shows the confirmation screen rather than an empty form. "Change
our reply" opens the form with everything they said already filled in.

### Tab `Gifts` — written by the script

Headers in row 1, nothing else:

    timestamp | name | amount | confirmed

Written when someone taps "Continue to Venmo". It records what they
*said* they were sending — nobody has paid anything at that moment. Check
Venmo, then put a yes in `confirmed`. Treat the rest as a to-do list, not
as money.

## The Apps Script

In the spreadsheet: **Extensions → Apps Script**. Delete what's there and
paste this.

```js
const GUESTS  = 'Guests';
const REPLIES = 'Replies';
const GIFTS   = 'Gifts';
const NOTIFY  = 'lcrane644@gmail.com';   // '' to turn emails off

function json(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}

function tab(name) {
  const sh = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(name);
  if (!sh) throw new Error('No tab named "' + name + '"');
  return sh;
}

function norm(s) {
  return String(s || '').toLowerCase().replace(/[^a-z\s]/g, ' ').replace(/\s+/g, ' ').trim();
}

// Headers, forgiving about capitals, spaces and punctuation, so
// "Plus One", "plus-one" and "plus_one" all find the same column.
// Getting this wrong used to fail silently — a mistyped header just
// made everyone look like they had no plus one and no children.
function headerIndex(row) {
  const map = {};
  row.forEach((h, i) => {
    const key = String(h).toLowerCase().trim()
      .replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
    if (key && map[key] === undefined) map[key] = i;
  });
  return map;
}

function pick(map, names, required) {
  for (const n of names) if (map[n] !== undefined) return map[n];
  if (required) {
    throw new Error('The ' + GUESTS + ' tab has no "' + names[0] +
      '" column. Columns found: ' + Object.keys(map).join(', '));
  }
  return -1;
}

const cell = (r, i) => (i < 0 || r[i] == null) ? '' : String(r[i]).trim();
const list = (r, i) => cell(r, i).split(',').map(s => s.trim()).filter(Boolean);
const yes  = v => /^(y|yes|true|1)$/i.test(String(v).trim());

function readGuests() {
  const values = tab(GUESTS).getDataRange().getValues();
  if (!values.length) return [];
  const map = headerIndex(values.shift());

  const cId    = pick(map, ['id'], true);
  const cHouse = pick(map, ['household', 'family', 'name'], true);
  const cAdult = pick(map, ['adults', 'adult', 'guests'], true);
  const cKids  = pick(map, ['children', 'child', 'kids']);
  const cPlus  = pick(map, ['plus_one', 'plusone', 'plus_1', 'plus']);

  return values
    .filter(r => cell(r, cId) !== '')
    .map(r => ({
      id: cell(r, cId),
      household: cell(r, cHouse),
      adults: list(r, cAdult),
      children: list(r, cKids),
      plusOne: yes(cell(r, cPlus))
    }));
}

// Existing answers grouped by household, so a guest who already
// replied is shown what they said instead of a blank form.
function readReplies() {
  const values = tab(REPLIES).getDataRange().getValues();
  if (values.length < 2) return {};
  const map = headerIndex(values.shift());
  const c = k => (map[k] === undefined ? -1 : map[k]);

  const byParty = {};
  values.forEach(r => {
    const id = cell(r, c('party_id'));
    if (!id) return;
    if (!byParty[id]) byParty[id] = { when: '', email: '', people: [] };

    const raw = c('timestamp') >= 0 ? r[c('timestamp')] : '';
    const when = (raw instanceof Date) ? raw.toISOString() : String(raw || '');
    if (when > byParty[id].when) byParty[id].when = when;

    const em = cell(r, c('email'));
    if (em) byParty[id].email = em;

    byParty[id].people.push({
      name: cell(r, c('name')),
      type: cell(r, c('type')),
      attending: yes(cell(r, c('attending'))),
      meal: cell(r, c('meal')),
      dietary: cell(r, c('dietary'))
    });
  });
  return byParty;
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
  try {
    const tokens = norm((e && e.parameter && e.parameter.q) || '').split(' ').filter(Boolean);
    if (!tokens.length) return json({ parties: [] });

    const replies = readReplies();
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
      p.reply = replies[p.id] || null;
      scored.push({ party: p, score: total });
    });

    scored.sort((a, b) => a.score - b.score);
    return json({ parties: scored.map(s => s.party) });
  } catch (err) {
    // Reported rather than swallowed: a bad header must not look to a
    // guest like "we can't find you".
    return json({ parties: [], error: String(err) });
  }
}

function doPost(e) {
  const lock = LockService.getScriptLock();
  lock.waitLock(20000);
  try {
    const data = JSON.parse(e.postData.contents);
    return data.kind === 'gift' ? saveGift(data) : saveRsvp(data);
  } catch (err) {
    return json({ ok: false, error: String(err) });
  } finally {
    lock.releaseLock();
  }
}

function saveRsvp(data) {
  const sh = tab(REPLIES);
  const values = sh.getDataRange().getValues();
  const map = headerIndex(values[0] || []);
  const cParty = map['party_id'] === undefined ? 1 : map['party_id'];

  // Clear this household's previous answer, remembering whether there
  // was one. Walk backwards — deleting a row shifts the rest up.
  let hadPrior = false;
  for (let i = values.length - 1; i >= 1; i--) {
    if (String(values[i][cParty]).trim() === String(data.partyId)) {
      sh.deleteRow(i + 1);
      hadPrior = true;
    }
  }

  (data.people || []).forEach(p => {
    sh.appendRow([
      new Date(), data.partyId, data.household, p.name, p.type,
      p.attending ? 'yes' : 'no', p.meal || '',
      p.dietary || '', data.email || ''
    ]);
  });

  if (NOTIFY) {
    const going = (data.people || []).filter(p => p.attending).length;
    MailApp.sendEmail(NOTIFY,
      (hadPrior ? 'RSVP changed: ' : 'RSVP: ') + data.household,
      data.household + (hadPrior ? ' changed their answer' : ' replied') +
      ' \u2014 ' + going + ' attending.\n\n' +
      (data.people || []).map(p =>
        '  ' + p.name + ' (' + p.type + '): ' + (p.attending ? 'yes' : 'no') +
        (p.dietary ? '  \u2014 ' + p.dietary : '')).join('\n') +
      (data.email ? '\n\nContact: ' + data.email : ''));
  }

  return json({ ok: true, updated: hadPrior });
}

function saveGift(data) {
  const amount = Number(data.amount) || 0;
  tab(GIFTS).appendRow([new Date(), data.name || '', amount, '']);

  if (NOTIFY) {
    MailApp.sendEmail(NOTIFY, 'Venmo gift: $' + amount,
      (data.name || 'Someone') + ' said they are sending $' + amount + ' by Venmo.\n\n' +
      'This is only what they told the website. Check Venmo, then put a yes in ' +
      'the confirmed column.');
  }

  return json({ ok: true });
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

## Checking it works

Open the `/exec` URL in a browser with a real guest's name on the end:

    ...exec?q=smith

You should see JSON. What's in it tells you exactly what is wrong:

- **`{"parties":[],"error":"..."}`** — the message names the problem,
  usually a missing or misspelled column or tab.
- **A sign-in page instead of JSON** — the deployment is set to "Anyone
  with a Google Account". Change it to "Anyone".
- **`"plusOne":false` for someone who should have one** — the `plus_one`
  cell isn't `yes`, or that column is missing.
- **`"reply":null` for a household that has already replied** — either
  the script hasn't been redeployed, or `party_id` in `Replies` doesn't
  match `id` in `Guests`.
- **No `reply` key at all** — the old script is still live. Redeploy.

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
