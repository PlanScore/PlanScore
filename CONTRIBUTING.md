# Contributing to PlanScore

Goals
--

PlanScore is a website, not a web app. Publish HTML and CSS, and include Javascript
only in specific interactive contexts such as 50 state navigation or a score page.

Since our intended audience includes legislative staff potentially
using older computers or mobile devices, site performance should
[follow Alex Russell’s guidance](https://infrequently.org/2017/10/can-you-afford-it-real-world-web-performance-budgets/):

> We set a budget in time of <= 5 seconds first-load
> [Time-to-Interactive](https://developers.google.com/web/tools/lighthouse/audits/time-to-interactive)
> and <= 2s for subsequent loads. We constrain ourselves to a real-world
> baseline device + network configuration to measure progress. The default
> global baseline is a ~$200 Android device on a 400Kbps link with a 400ms
> round-trip-time (“RTT”). This translates into a budget of ~130-170KB of
> critical-path resources, depending on composition — the more JS you include,
> the smaller the bundle must be.

Code
--

[Use Projects](https://github.com/PlanScore/PlanScore/projects), if applicable.
Don’t commit directly to `master`, [use a pull request](https://github.com/PlanScore/PlanScore/pulls).
