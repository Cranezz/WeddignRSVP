# Registry — how it works

Two ways to give: an Amazon Wedding Registry for physical gifts, and
Venmo for cash. Both live on the site's Registry section.

## Amazon

Amazon owns the checkout, so it marks items purchased by itself, hides
the shipping address from guests, and offers group gifting on expensive
items. Nothing to build — the site links out.

Live at:

    https://www.amazon.com/wedding/guest-view/2C62WFP0WYN3U

That is the *guest view* — the logged-out page guests see. Worth opening
it in a private window occasionally to check it still resolves without a
sign-in prompt, since that is the state every guest will be in.

## Venmo

Venmo has **no public API for personal accounts** — the API is
business-only, through PayPal/Braintree. A website cannot ask whether a
payment arrived. So the flow is:

1. Guest picks an amount (slider, chips, or typed).
2. The page builds a deep link with the amount and a note prefilled.
3. Guest sends the money in the Venmo app.
4. Logan checks Venmo and matches it against the log.

Venmo already shows the sender's name, so the name field on the page is
a convenience for matching, not the only signal.

### The link format

```
https://venmo.com/u/Logan-Crane-23?txn=pay&amount=100&note=...
```

Prefill parameters are **best-effort**. Venmo has changed how it honours
them and behaviour differs across iOS, Android and desktop web. If they
are dropped the guest still lands on the right profile having just seen
the amount, so the worst case is typing it again. Worth testing on a real
phone and adjusting if needed.

### Logging (not built yet)

`giftGo`'s click handler in `index.html` is where a pledge gets recorded.
It currently only updates the thank-you line. To wire it up, POST to an
Apps Script `doPost` that appends to a private `Gifts` tab:

| timestamp | amount | guest name | confirmed |
|-----------|--------|------------|-----------|

`confirmed` is set by hand after checking Venmo. Treat the log as
*intent*: a guest can tap Continue and never send anything, so the log
alone is not money.

Note the request has to be sent in a way that survives the page
navigating away to Venmo — `navigator.sendBeacon` rather than a plain
`fetch`, or fire it slightly before the hand-off.

### Fees

Venmo takes nothing on personal payments between friends. It does take a
cut if a sender marks the payment as goods and services, which also
raises 1099-K paperwork. Guests won't do that by default. Not worth
mentioning on the site unless it comes up.

## Deliberately not built

- **A running total or progress bar.** The numbers would be unverified
  pledges rather than money received, and a public tally reads more like
  a fundraiser than a wedding.
- **Stripe.** It would make totals update automatically, but at roughly
  2.9% + 30¢ per gift — about $175 on $5,000 — to save reconciling maybe
  thirty transactions by hand.
