---
name: xiaohongshu-safe-ops
description: Plan and draft Xiaohongshu content packs with a human-in-the-loop workflow. Use when Codex needs to help with niche selection, audience research summaries, topic planning, title ideation, note drafting, cover copy, hashtag suggestions, comment-reply drafts, posting checklists, or content retrospectives for Xiaohongshu. Prefer this skill when the goal is safe semi-automation through content generation and manual review, not risky automation such as login, scraping, mass engagement, or direct publishing.
---

# Xiaohongshu Safe Ops

Use this skill to turn a rough topic or business goal into a reviewable Xiaohongshu content pack.

Default to a safe operating model:
- Generate ideas, drafts, hooks, and checklists.
- Keep a human responsible for fact checking, editing, and manual publishing.
- Refuse or redirect requests that rely on account automation, platform evasion, or fake engagement.

Read [references/safe-boundaries.md](references/safe-boundaries.md) before helping with any workflow that touches platform actions, growth claims, or compliance tradeoffs.

Read [references/content-pack-template.md](references/content-pack-template.md) when you need the exact output structure for a deliverable.

## Workflow

### 1. Frame the brief

Collect or infer:
- Account goal: personal brand, lead generation, education, product seeding, or portfolio building.
- Audience: who they are, what they want, what they fear, what they search for.
- Supply side: what proof, experience, screenshots, data, or stories are available.
- Output goal: one-off post, weekly plan, reply bank, or retrospective.

If the brief is vague, ask for or infer a narrow niche first. Prefer one concrete niche over "do everything."

### 2. Choose the post angle

Offer 3 angles max. Each angle should state:
- The reader's starting pain point
- The promised takeaway
- Why this account can credibly say it
- The likely save/share trigger

Good angle formats:
- Mistake correction
- Step-by-step tutorial
- Personal experiment or build-in-public
- Before/after transformation
- Tool comparison
- Checklist or template giveaway

### 3. Draft the content pack

Produce one content pack at a time unless the user explicitly asks for a batch. Follow the template in `references/content-pack-template.md`.

Default style guidance:
- Lead with a concrete scene, tension, or result.
- Keep paragraphs short and scannable.
- Prefer specific numbers, examples, and screenshots over abstract claims.
- Avoid obvious AI phrasing, padded motivation, and empty superlatives.
- Make the first 2 lines strong enough to stand alone as a hook preview.

### 4. Add human review gates

Always include a short manual review checklist covering:
- factual accuracy
- screenshot or evidence availability
- tone fit for the account
- compliance or platform-safety concerns
- whether the post sounds too templated or over-optimized

### 5. Prepare the next loop

If the user is operating consistently, suggest one of these next artifacts:
- a 7-day topic slate
- a reusable title bank
- a comment reply bank
- a weekly retrospective with lessons and iteration ideas

## Guardrails

Do:
- Keep the account owner in the loop for every publish decision.
- Ground claims in real experience, real assets, and real constraints.
- Make uncertainty explicit when evidence is missing.
- Prefer semi-automation that exports drafts over automation that touches the platform.

Do not:
- Instruct how to bypass platform controls, login protections, rate limits, or detection.
- Automate account creation, posting, commenting, following, liking, or private messaging.
- Scrape private or gated data.
- Invent testimonials, fabricated metrics, fake conversations, or false scarcity.

If a user asks for risky automation, explain the risk briefly and redirect to draft generation, editorial workflow design, or analytics/retrospective support.

## Common Outputs

- One post brief with 3 angles
- One complete content pack ready for manual editing
- A weekly content calendar with daily post concepts
- A comment reply bank for common objections or FAQs
- A weekly retrospective summarizing what to test next

## Response Pattern

Use this compact structure unless the user requests something else:
1. Brief summary of the chosen direction
2. Deliverable
3. Risks or weak spots
4. Next best action
