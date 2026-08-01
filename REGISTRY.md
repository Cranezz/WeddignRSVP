# Registry — how it works

Two ways to give: an Amazon Wedding Registry for physical gifts, and
Venmo for cash. Both live on the site's Registry section, one button
each.

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

One button, straight to the profile:

    https://venmo.com/u/Logan-Crane-23?txn=pay&note=Logan%20%26%20Mary%20Lou's%20wedding

No amount is prefilled. There used to be a slider, a set of preset
amounts and a name box, all feeding an `amount=` parameter and a log of
who intended to give what. It came out: Venmo is where you pick the
amount, the page had nothing to add to that, and the prefill parameters
were never reliable anyway — Venmo has changed how it honours them, and
behaviour differs across iOS, Android and desktop.

What is left is the note, which is what shows up in the payment so the
gift is identifiable months later.

### Reconciling

Venmo has **no public API for personal accounts** — the API is
business-only, through PayPal/Braintree. A website cannot ask whether a
payment arrived, and the site no longer tries to guess. Venmo already
shows the sender's name and the note, so the Venmo activity feed is the
record.

The Apps Script still understands a `{kind:"gift"}` POST and will append
to a `Gifts` tab if one ever sends it. Nothing does, today.

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
