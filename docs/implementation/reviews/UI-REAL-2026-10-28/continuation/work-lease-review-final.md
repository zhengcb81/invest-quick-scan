# Future work-lease interface independent review

**Passed; no open findings.** Exact final hashes for eight IQS files and three StockQA files are in `work-lease-review-final.json`.

The reviewer did not author these changes. Source review confirms that explicit duration is validated before preparation/launch, is included in the original preparation and execution fingerprints, and reaches the original CLI and lifecycle for future claims. Missing configuration keeps the old argv and 600-second default. Changing the future duration does not renew an active original lease, extend owner authorization, change the budget or loosen checkpoint acceptance.

Eleven focused tests passed in 6.49 seconds: five private interface/SQLite checks and six independently rerun existing CLI/SDK cases. They cover exact legacy argv, frozen fingerprints, a live original600 lease remaining unchanged while a new claim receives3600, non-finite rejection, CLI forwarding, and original delayed-response boundaries. Replies beyond their lease remain uncertain with settled fees and no checkpoint; running again causes no additional HTTP. Temporary workspaces were removed.

The SDK intentionally retains positive finite fractional seconds up to86400; the UI accepts only1–86400 integer seconds. The documentation distinguishes new claim duration, new owner grant lifetime, preparation subprocess timeouts and HTTP read timeout.

This is engineering interface acceptance. The reviewer did not rerun the separately failing full36 native owner-preview experiment, deploy new configuration, reload services, touch active company workers, call live APIs or access real databases. Real UI acceptance of new3600 claims and the separate late-reply recovery capability remain mainline work; this report does not close those gates.
