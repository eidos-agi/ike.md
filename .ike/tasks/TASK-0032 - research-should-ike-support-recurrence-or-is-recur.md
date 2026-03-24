---
id: TASK-0032
title: 'Research: Should Ike support recurrence, or is recurrence an anti-pattern?'
status: To Do
created: '2026-03-23'
priority: medium
tags:
  - research
  - architecture
  - recurrence
  - scorecard-pattern
acceptance-criteria:
  - 'Decision: recurrence as a feature vs. anti-pattern, with evidence'
  - 'If anti-pattern: document the scorecard-to-task pattern as the recommended alternative'
  - 'If feature: design the minimal recurrence spec that avoids the busywork trap'
  - Write up as an ADR in ike.md's visionlog
---
Insight from the AIC CISO cockpit (2026-03-23): recurring tasks may be the wrong abstraction for solo operators with AI agents.

**The argument against recurrence in Ike:**

Most productivity systems conflate two things:
1. **The obligation** — a standing commitment (e.g., "run security scans weekly")
2. **The work item** — a specific, contextual action born from a gap

When you fuse them into a recurring task, you get busywork without context. A "run scans" task that auto-creates every Monday doesn't know that *this* Monday is different because CI broke three weeks ago and 9 high findings are aging out.

**The alternative pattern discovered:**

Separate the layers:
- **VisionLog SOPs** define the cadence (the obligation persists)
- **A scorecard/check** runs on schedule and detects when the obligation wasn't met
- **Ike tasks** are created by the scorecard with full context about what broke and why it matters *this specific week*

The recurring thing is the *check*, not the *task*. Tasks are born from failures, not calendars. This mirrors how ops teams work — nobody has a recurring Jira ticket "check if prod is up." They have monitoring. When monitoring fires, an incident ticket gets created with specifics.

**Research questions:**
1. Is this pattern general or specific to solo operators?
2. Would teams benefit from this separation too?
3. If Ike adds recurrence, does it become another nagging todo app?
4. Should Ike explicitly support a "scorecard → task generation" pattern instead?
5. What's the right boundary between Ike (execution) and VisionLog (obligations)?

**Origin:** CISO cockpit session where `/ciso-score` found 31 days of missed scans. The SOP existed. The habit broke. A recurring task wouldn't have helped — it would have been ignored alongside the scans. The scorecard caught it and created a real task with teeth.
