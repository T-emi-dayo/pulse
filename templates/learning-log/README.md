# PulseDev learning log

This repository stores each weekly pick and its work. PulseDev bootstraps this structure when the configured repository is empty.

`profile.json` is the current user profile. It stores named sections, stable item IDs, evidence links, and dates resolved by PulseDev code. The weekly model may propose an evidence-backed addition, rename, or merge; code assigns identifiers and dates and preserves merged records.

## Working with a pick

Edit `picks/<pick-id>/pick.md` to set its status to `in_progress`, `done`, or `skipped`. Add `skip_reason` when skipping. On completion, set `rating` from 1 to 5, write a `takeaway`, answer every core-idea question in `notes.md`, and save the work described by the pick's outcome. The push-triggered workflow validates completed picks and rebuilds `index.json`.

The next weekly run resends an unreviewed pick once, then lapses it after the second silent week. An in-progress pick is carried once with its original outcome and core ideas unchanged; code adds a continuity note rather than asking the model to re-plan it. A skipped topic is suppressed for three weeks. Ratings and takeaways inform future picks but are personal reflection, not objective skill scores.

Keep private or client work out of this repository.
