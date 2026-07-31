# Registry — how the backend will work

The site is static (GitHub Pages), so it can't hold state or take money by
itself. Everything below runs on a Google Sheet plus one Apps Script.
No server, no hosting bill.

## The sheet

One spreadsheet, three tabs.

**`Items`** — published to the web as CSV (File → Share → Publish to web).
The page fetches this URL directly, so reads are fast and cached by Google
and don't burn Apps Script quota.

| id | name | price | image | url | status |
|----|------|-------|-------|-----|--------|
| mixer | Stand mixer | 449 | img/mixer.jpg | https://… | available |

`status` is one of `available`, `claimed`, `received`. Only you set
`received`, once the thing actually turns up.

**`Claims`** — private, never published.

| timestamp | item id | guest name | email | note |
|-----------|---------|------------|-------|------|

This tab is also the thank-you-note list.

**`Gifts`** — private. Cash pledges, reconciled by hand against Venmo.

| timestamp | fund | amount | guest name | email | confirmed |
|-----------|------|--------|------------|-------|-----------|

Keeping claimer names off the published tab is the point of the split. One
sheet published whole would let anyone read who gave what.

## The Apps Script

A single `doPost` bound to the sheet, deployed as a web app with access set
to "Anyone".

1. Reject the request if the honeypot field is filled.
2. `LockService.getScriptLock()` — two guests can tap the same item at the
   same moment, and without the lock both get told they claimed it.
3. Re-read the item's current status. If it isn't `available` any more,
   return a "someone just took this" response so the page can say so
   rather than silently overwriting.
4. Append to `Claims`, flip `Items.status` to `claimed`.
5. `MailApp.sendEmail` to Logan and Mary Lou, and a confirmation to the guest.

The endpoint URL is public — it has to be. That's fine: the worst case is
junk rows, everything is logged, and anything can be undone by editing the
sheet.

## Cash gifts

Guest picks an amount, taps through to Venmo or PayPal with the amount and
fund name prefilled, then taps "I've sent it" which logs a pledge to
`Gifts`. You reconcile against your actual Venmo history and set
`confirmed`.

This is deliberately manual. Stripe would make the progress bars update on
their own, but it costs about 2.9% + 30¢ per gift — roughly $175 on $5,000
— to save reconciling perhaps thirty transactions.

## Still to decide

- Where physical gifts ship. A homemade registry can't hide your address
  the way Zola or MyRegistry can.
- Real Venmo and PayPal handles (placeholders in `index.html`).
- Whether the funds show a goal and progress bar at all, or just a total.
- Product photos: download and commit them resized. Don't hotlink from
  retailers — the links rot and the images aren't ours to serve.
