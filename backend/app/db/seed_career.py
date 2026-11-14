"""Curated career role maps, portfolio briefs and mock-interview question bank.

Everything here is platform content, versioned in code. Skill references use the
(slug, subject slug) pairs seeded in `seed.py`; seeding fails loudly if a role
points at a skill that does not exist rather than silently dropping the gap.
"""

from __future__ import annotations

CAREER_ROLES: list[dict] = [
    {
        "slug": "backend_developer",
        "title": "Backend Developer",
        "summary": (
            "Builds APIs, data models and services that other systems depend on. "
            "The role rewards correctness, clear interfaces and operational awareness."
        ),
        "level": "entry",
        "version": 1,
        "skills": [
            ("python", "syntax-and-types", 60, 3),
            ("python", "control-flow", 60, 2),
            ("python", "functions", 65, 3),
            ("python", "data-structures", 70, 3),
            ("python", "error-handling", 65, 2),
            ("python", "testing", 55, 3),
            ("python", "modules-packaging", 50, 2),
            ("sql", "select-queries", 70, 3),
            ("sql", "joins", 70, 3),
            ("sql", "indexing", 55, 2),
            ("sql", "transactions", 55, 2),
            ("system-design", "api-design", 65, 3),
            ("system-design", "reliability", 50, 2),
            ("system-design", "observability", 45, 2),
        ],
        "portfolio_briefs": [
            {
                "title": "Authenticated task API",
                "brief": (
                    "Build a small REST API with user registration, session auth and per-user "
                    "resources. Include request validation, a consistent error envelope and "
                    "integration tests that cover the happy path and one failure per endpoint."
                ),
                "skills": ["api-design", "functions", "testing", "select-queries"],
            },
            {
                "title": "Query review notebook",
                "brief": (
                    "Take five slow queries against a sample schema, explain the plans, add the "
                    "indexes that help, and document before/after timings. The write-up matters "
                    "as much as the speedup."
                ),
                "skills": ["indexing", "joins", "select-queries"],
            },
        ],
    },
    {
        "slug": "frontend_developer",
        "title": "Frontend Developer",
        "summary": (
            "Turns product requirements into accessible, responsive interfaces. Strong "
            "candidates can explain state, async data and component boundaries."
        ),
        "level": "entry",
        "version": 1,
        "skills": [
            ("javascript", "js-fundamentals", 70, 3),
            ("javascript", "dom", 60, 3),
            ("javascript", "async-js", 70, 3),
            ("javascript", "fetch-api", 65, 3),
            ("javascript", "react-components", 75, 3),
            ("javascript", "state-management", 60, 3),
            ("javascript", "typescript", 60, 2),
            ("system-design", "api-design", 45, 1),
        ],
        "portfolio_briefs": [
            {
                "title": "Data-driven dashboard",
                "brief": (
                    "Build a dashboard that fetches paginated data, handles loading, empty and "
                    "error states, and keeps filter state in the URL. Include one optimistic "
                    "update with a rollback on failure."
                ),
                "skills": ["react-components", "state-management", "fetch-api"],
            },
            {
                "title": "Accessible form flow",
                "brief": (
                    "Ship a multi-step form with keyboard navigation, field-level validation and "
                    "clear announcements for screen readers. Document the decisions you made."
                ),
                "skills": ["dom", "js-fundamentals", "typescript"],
            },
        ],
    },
    {
        "slug": "data_scientist",
        "title": "Data Scientist",
        "summary": (
            "Turns data into decisions: framing questions, cleaning data, modelling and "
            "communicating uncertainty. Evidence and evaluation habits matter more than tools."
        ),
        "level": "entry",
        "version": 1,
        "skills": [
            ("python", "data-structures", 65, 3),
            ("python", "modules-packaging", 50, 2),
            ("python", "testing", 40, 1),
            ("sql", "select-queries", 70, 3),
            ("sql", "joins", 65, 3),
            ("sql", "aggregation", 70, 3),
            ("sql", "subqueries", 55, 2),
            ("machine-learning", "statistics", 70, 3),
            ("machine-learning", "regression", 65, 3),
            ("machine-learning", "classification", 60, 3),
            ("machine-learning", "model-evaluation", 65, 3),
            ("machine-learning", "feature-engineering", 55, 2),
        ],
        "portfolio_briefs": [
            {
                "title": "Decision memo from a dataset",
                "brief": (
                    "Pick a public dataset, state a decision it should inform, and write a memo "
                    "with the cleaning steps, baseline, model comparison and the uncertainty in "
                    "your recommendation."
                ),
                "skills": ["statistics", "model-evaluation", "aggregation"],
            },
            {
                "title": "Leakage audit",
                "brief": (
                    "Take a model you built and document every place target leakage could enter, "
                    "then rebuild the evaluation with a clean split and report the score change."
                ),
                "skills": ["model-evaluation", "feature-engineering", "regression"],
            },
        ],
    },
    {
        "slug": "ml_engineer",
        "title": "Machine Learning Engineer",
        "summary": (
            "Ships models as dependable services. The role blends modelling judgement with "
            "software engineering, evaluation and monitoring."
        ),
        "level": "mid",
        "version": 1,
        "skills": [
            ("machine-learning", "python-for-ml", 70, 3),
            ("machine-learning", "regression", 65, 2),
            ("machine-learning", "classification", 65, 3),
            ("machine-learning", "model-evaluation", 70, 3),
            ("machine-learning", "neural-networks", 55, 2),
            ("machine-learning", "feature-engineering", 60, 2),
            ("python", "testing", 55, 3),
            ("python", "modules-packaging", 60, 2),
            ("system-design", "scalability", 45, 2),
            ("system-design", "reliability", 45, 2),
            ("system-design", "observability", 50, 3),
        ],
        "portfolio_briefs": [
            {
                "title": "Model service with monitoring",
                "brief": (
                    "Wrap a trained model in an HTTP service with input validation, a health "
                    "check, latency metrics and a logged prediction sample. Explain how you would "
                    "detect drift."
                ),
                "skills": ["model-evaluation", "observability", "testing"],
            },
            {
                "title": "Reproducible training pipeline",
                "brief": (
                    "Build a pipeline that pins data versions, seeds and artefacts, then rerun it "
                    "from scratch and show identical metrics."
                ),
                "skills": ["modules-packaging", "python-for-ml", "testing"],
            },
        ],
    },
    {
        "slug": "devops_engineer",
        "title": "DevOps / Platform Engineer",
        "summary": (
            "Keeps delivery and running systems healthy: automation, observability, and "
            "reliable change. Breadth across networking, storage and process is expected."
        ),
        "level": "mid",
        "version": 1,
        "skills": [
            ("system-design", "reliability", 65, 3),
            ("system-design", "observability", 65, 3),
            ("system-design", "scalability", 60, 3),
            ("system-design", "caching", 50, 2),
            ("system-design", "databases", 55, 2),
            ("python", "error-handling", 55, 2),
            ("python", "testing", 50, 2),
            ("sql", "indexing", 50, 1),
            ("sql", "transactions", 55, 2),
        ],
        "portfolio_briefs": [
            {
                "title": "Deploy pipeline with rollback",
                "brief": (
                    "Automate build, test and deploy for a small service, including a health "
                    "gate and a one-command rollback. Record a failure and the recovery."
                ),
                "skills": ["reliability", "observability", "testing"],
            },
            {
                "title": "Incident runbook",
                "brief": (
                    "Write a runbook for one realistic failure (database saturation, bad deploy), "
                    "with detection, triage, mitigation and follow-up actions."
                ),
                "skills": ["reliability", "databases", "observability"],
            },
        ],
    },
    {
        "slug": "software_engineer",
        "title": "Software Engineer",
        "summary": (
            "Generalist product engineering: implement features, reason about data structures "
            "and keep code reviewable. Suitable when the student has not chosen a specialism."
        ),
        "level": "entry",
        "version": 1,
        "skills": [
            ("python", "functions", 65, 3),
            ("python", "oop", 60, 2),
            ("python", "testing", 60, 3),
            ("dsa", "complexity", 60, 2),
            ("dsa", "arrays-strings", 65, 3),
            ("dsa", "hashing", 55, 2),
            ("dsa", "trees", 45, 1),
            ("sql", "select-queries", 55, 2),
            ("sql", "joins", 50, 2),
            ("system-design", "api-design", 55, 2),
            ("system-design", "reliability", 45, 1),
            ("system-design", "observability", 40, 1),
        ],
        "portfolio_briefs": [
            {
                "title": "Feature slice with tests",
                "brief": (
                    "Implement one user-facing feature end to end in a small app, with tests for "
                    "the core logic and a short note on the trade-offs you chose."
                ),
                "skills": ["functions", "testing", "arrays-strings"],
            },
            {
                "title": "API client with retries",
                "brief": (
                    "Write a client for an HTTP API with pagination, retry with backoff and clear "
                    "error types. Cover the failure modes with tests."
                ),
                "skills": ["api-design", "testing", "hashing"],
            },
        ],
    },
]

# (point, keywords) pairs make up each rubric. A point is awarded when any of its
# keywords appears in the answer; the score is the weighted share of points.
INTERVIEW_QUESTIONS: dict[str, list[dict]] = {
    "backend_developer": [
        {
            "kind": "conceptual",
            "skill": "api-design",
            "prompt": "How would you design pagination for an API endpoint that returns a large, changing collection?",
            "rubric": [
                ("Chooses cursor or keyset pagination for large changing data", ["cursor", "keyset"]),
                ("Explains the offset performance problem", ["offset", "slow", "deep"]),
                ("Defines a stable sort key and returns a next cursor", ["sort", "next", "cursor"]),
            ],
            "answer": (
                "Use cursor (keyset) pagination: order by a stable indexed key, return the last "
                "seen value as the next cursor, and avoid OFFSET because deep offsets scan rows. "
                "Document limits and the sort order."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "indexing",
            "prompt": "A query filtering on user_id and ordering by created_at is slow. What do you check and what would you change?",
            "rubric": [
                ("Reads the query plan before changing anything", ["explain", "plan"]),
                ("Proposes a composite index on user_id and created_at", ["composite", "compound", "user_id"]),
                ("Considers write cost and selectivity", ["write", "selectivity", "cost"]),
            ],
            "answer": (
                "Run EXPLAIN ANALYZE, confirm the filter and sort columns, then add a composite "
                "index on (user_id, created_at) matching the order. Weigh the extra write cost and "
                "check whether the index is actually selective."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "transactions",
            "prompt": "When would you use a database transaction, and what can go wrong if you hold one too long?",
            "rubric": [
                ("Groups related writes that must succeed together", ["atomic", "together", "all or nothing"]),
                ("Mentions isolation and locking effects", ["isolation", "lock"]),
                ("Warns about long transactions blocking or exhausting connections", ["long", "block", "connection", "deadlock"]),
            ],
            "answer": (
                "Use a transaction when several writes form one logical change and must commit or "
                "roll back together. Long transactions hold locks, increase contention, can block "
                "other requests and risk deadlocks or pool exhaustion."
            ),
        },
        {
            "kind": "behavioural",
            "skill": None,
            "prompt": "Describe a bug you caused and how you found it. What changed in how you work afterwards?",
            "rubric": [
                ("Describes a concrete situation and the impact", ["bug", "incident", "broke"]),
                ("Explains the debugging process, not just the fix", ["log", "trace", "reproduce", "debug"]),
                ("Names a durable change to process or tests", ["test", "check", "review", "process"]),
            ],
            "answer": (
                "A specific incident, the symptom, how logs or a reproduction isolated the cause, "
                "the fix, and the regression test or review habit added afterwards."
            ),
        },
    ],
    "frontend_developer": [
        {
            "kind": "conceptual",
            "skill": "state-management",
            "prompt": "How do you decide between local component state, lifted state and a global store?",
            "rubric": [
                ("Keeps state as local as possible", ["local", "closest", "component"]),
                ("Lifts state when siblings must share it", ["share", "sibling", "parent"]),
                ("Reserves global state for cross-cutting concerns", ["global", "server", "cache", "cross"]),
            ],
            "answer": (
                "Start local; lift to the nearest common parent when siblings need it; use a global "
                "store only for genuinely cross-cutting state such as session or a server cache. "
                "Derived values should not be stored twice."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "async-js",
            "prompt": "A page fires three requests on mount and shows stale data after a filter change. How do you fix it?",
            "rubric": [
                ("Cancels or ignores outdated responses", ["abort", "cancel", "ignore", "stale"]),
                ("Ties the request to the current filter or key", ["filter", "key", "dependency"]),
                ("Handles loading and error states explicitly", ["loading", "error"]),
            ],
            "answer": (
                "Abort the previous request with an AbortController (or ignore responses whose "
                "filter no longer matches), key the effect on the filter, and render explicit "
                "loading and error states so an old response cannot overwrite a new one."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "react-components",
            "prompt": "How would you make a large list of items render smoothly?",
            "rubric": [
                ("Virtualises or windows the list", ["virtual", "window", "windowing"]),
                ("Keeps row components cheap and memoised", ["memo", "pure", "cheap"]),
                ("Uses stable keys and avoids unnecessary re-renders", ["key", "re-render", "stable"]),
            ],
            "answer": (
                "Virtualise the list so only visible rows mount, keep rows presentational and "
                "memoised, and use stable keys. Profile before optimising further."
            ),
        },
        {
            "kind": "behavioural",
            "skill": None,
            "prompt": "Tell me about a time you pushed back on a design or requirement. How did it end?",
            "rubric": [
                ("Describes the trade-off concretely", ["trade", "cost", "risk", "accessib"]),
                ("Explains how the concern was raised", ["discuss", "propose", "data", "prototype"]),
                ("States the outcome honestly", ["result", "agree", "change", "decided"]),
            ],
            "answer": (
                "A concrete requirement, the specific user or maintenance cost, how the concern was "
                "raised with evidence, and the decision reached — including when the original "
                "requirement stood."
            ),
        },
    ],
    "data_scientist": [
        {
            "kind": "conceptual",
            "skill": "model-evaluation",
            "prompt": "Your classifier reports 96% accuracy on an imbalanced dataset. Why is that not enough, and what would you report instead?",
            "rubric": [
                ("Names the class imbalance and the majority baseline", ["imbalance", "baseline", "majority"]),
                ("Proposes precision, recall or a confusion matrix", ["precision", "recall", "confusion"]),
                ("Chooses a metric tied to the decision cost", ["cost", "false positive", "false negative", "business"]),
            ],
            "answer": (
                "96% may equal the majority baseline. Report the confusion matrix plus precision, "
                "recall and a threshold-aware metric (F1, PR-AUC) chosen from the cost of each error "
                "type, and compare against a trivial baseline."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "statistics",
            "prompt": "How do you decide whether a measured improvement is real?",
            "rubric": [
                ("Uses a held-out or cross-validated comparison", ["holdout", "cross", "validation", "test set"]),
                ("Quantifies uncertainty with intervals or repeated runs", ["confidence", "interval", "variance", "seed"]),
                ("Separates statistical from practical significance", ["practical", "effect", "meaningful"]),
            ],
            "answer": (
                "Compare on held-out or cross-validated data, repeat runs or bootstrap to get "
                "intervals, and judge whether the effect size matters for the decision — not only "
                "whether p is small."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "aggregation",
            "prompt": "Write the shape of a SQL query that returns monthly revenue per region, including regions with no sales.",
            "rubric": [
                ("Groups by month and region", ["group by", "month", "region"]),
                ("Uses a LEFT JOIN from regions", ["left join", "left"]),
                ("Coalesces missing sums to zero", ["coalesce", "zero", "0"]),
            ],
            "answer": (
                "LEFT JOIN regions to sales, GROUP BY month and region, SUM with COALESCE(...,0). "
                "Generate months with a calendar table or CTE so empty months appear too."
            ),
        },
        {
            "kind": "behavioural",
            "skill": None,
            "prompt": "Describe a time your analysis changed a decision — or failed to. What did you learn?",
            "rubric": [
                ("States the decision and the evidence", ["decision", "stakeholder", "result"]),
                ("Explains how uncertainty was communicated", ["uncertain", "caveat", "assumption"]),
                ("Reflects on what would be done differently", ["next time", "instead", "learn"]),
            ],
            "answer": (
                "The question, the evidence, how uncertainty was framed for the decision-maker, the "
                "outcome, and one concrete change to the next analysis."
            ),
        },
    ],
    "ml_engineer": [
        {
            "kind": "conceptual",
            "skill": "observability",
            "prompt": "What would you monitor after deploying a model to production?",
            "rubric": [
                ("Tracks input and prediction distributions for drift", ["drift", "distribution", "input"]),
                ("Tracks latency, error rate and throughput", ["latency", "error", "throughput"]),
                ("Connects monitoring to a retraining or rollback trigger", ["retrain", "rollback", "alert"]),
            ],
            "answer": (
                "Latency, error rate and throughput for the service; input and prediction "
                "distributions for drift; labelled-sample quality when labels arrive. Each alert "
                "maps to a rollback or retraining decision."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "testing",
            "prompt": "How do you test a machine-learning pipeline?",
            "rubric": [
                ("Unit-tests data transforms deterministically", ["unit", "transform", "deterministic"]),
                ("Tests schema and data-quality expectations", ["schema", "validation", "quality"]),
                ("Uses a small end-to-end fixture with a fixed seed", ["end-to-end", "fixture", "seed"]),
            ],
            "answer": (
                "Unit tests for transforms with fixed inputs, schema and data-quality checks at "
                "pipeline boundaries, and a small end-to-end run with pinned seeds and a metric "
                "threshold to catch regressions."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "feature-engineering",
            "prompt": "What is target leakage and how do you detect it before training?",
            "rubric": [
                ("Defines leakage as information unavailable at prediction time", ["not available", "future", "prediction time"]),
                ("Checks feature timing and collection process", ["timing", "when", "collection"]),
                ("Validates with a time-based split", ["time", "split", "chronological"]),
            ],
            "answer": (
                "Leakage is any feature that encodes the target or future information. Audit when "
                "each field is recorded, drop post-outcome fields, and validate with a "
                "time-ordered split."
            ),
        },
        {
            "kind": "behavioural",
            "skill": None,
            "prompt": "Tell me about a model that looked good offline but failed in production.",
            "rubric": [
                ("Describes the offline/online gap with numbers", ["offline", "online", "gap", "production"]),
                ("Investigates data or distribution differences", ["distribution", "data", "drift"]),
                ("Names the fix and the guard added", ["fix", "monitor", "guard", "test"]),
            ],
            "answer": (
                "The measured offline result, what production showed, the investigation into data "
                "or distribution shift, the fix, and the monitoring or evaluation change that "
                "prevents a repeat."
            ),
        },
    ],
    "devops_engineer": [
        {
            "kind": "conceptual",
            "skill": "reliability",
            "prompt": "How would you make a deploy safe enough to run during business hours?",
            "rubric": [
                ("Uses automated tests and a health gate", ["test", "health", "gate"]),
                ("Rolls out gradually with a rollback path", ["canary", "gradual", "rollback", "blue"]),
                ("Monitors error rate and latency after release", ["monitor", "error", "latency"]),
            ],
            "answer": (
                "Automated tests plus a post-deploy health gate, a gradual rollout (canary or "
                "blue-green) with one-command rollback, and alerting on error rate and latency so a "
                "bad release is caught in minutes."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "observability",
            "prompt": "A service is slow but healthy. What signals do you look at first?",
            "rubric": [
                ("Starts with latency percentiles rather than averages", ["percentile", "p95", "p99"]),
                ("Checks saturation: CPU, memory, connections, queue depth", ["cpu", "memory", "connection", "queue"]),
                ("Traces one slow request end to end", ["trace", "span", "end to end"]),
            ],
            "answer": (
                "p95/p99 latency split by endpoint, saturation metrics (CPU, memory, pool, queue "
                "depth), then a distributed trace of one slow request to locate the bottleneck."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "scalability",
            "prompt": "How do you decide between scaling up and scaling out?",
            "rubric": [
                ("Examines whether the workload is stateless", ["stateless", "state"]),
                ("Considers cost and operational complexity", ["cost", "complex"]),
                ("Identifies the actual bottleneck first", ["bottleneck", "database", "cpu", "memory"]),
            ],
            "answer": (
                "Find the bottleneck first. Scale out stateless tiers horizontally; scale up or "
                "shard stateful stores. Weigh cost and operational burden, and prefer the simplest "
                "change that removes the bottleneck."
            ),
        },
        {
            "kind": "behavioural",
            "skill": None,
            "prompt": "Walk me through an incident you handled. What was the timeline and your role?",
            "rubric": [
                ("Gives a clear timeline of detection and mitigation", ["detect", "alert", "mitigat", "timeline"]),
                ("Separates mitigation from root-cause work", ["root cause", "mitigat", "after"]),
                ("Describes the follow-up that prevented recurrence", ["follow", "prevent", "action"]),
            ],
            "answer": (
                "Detection, triage, mitigation, and only then root cause — with the student's "
                "specific role and the action item that reduced the chance of recurrence."
            ),
        },
    ],
    "software_engineer": [
        {
            "kind": "conceptual",
            "skill": "complexity",
            "prompt": "How would you find the first non-repeating character in a string, and what does it cost?",
            "rubric": [
                ("Uses a hash map of counts", ["hash", "dict", "map", "count"]),
                ("Does a second pass for order", ["second pass", "order", "again"]),
                ("States O(n) time and O(k) space", ["o(n)", "linear", "space"]),
            ],
            "answer": (
                "Count characters in a hash map, then scan again and return the first with count 1. "
                "O(n) time and O(k) space for the alphabet."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "testing",
            "prompt": "What makes a unit test worth keeping?",
            "rubric": [
                ("Tests behaviour, not implementation details", ["behaviour", "behavior", "contract"]),
                ("Covers a meaningful edge or failure case", ["edge", "failure", "boundary"]),
                ("Stays fast and deterministic", ["fast", "deterministic", "stable"]),
            ],
            "answer": (
                "It asserts observable behaviour, covers a real edge or failure mode, runs fast and "
                "deterministically, and fails for one clear reason so the diagnosis is obvious."
            ),
        },
        {
            "kind": "conceptual",
            "skill": "api-design",
            "prompt": "How do you version a public HTTP API without breaking existing clients?",
            "rubric": [
                ("Adds changes compatibly before deprecating", ["additive", "compatible", "optional"]),
                ("Versions explicitly and documents deprecation", ["version", "deprecat", "document"]),
                ("Monitors usage before removing anything", ["usage", "monitor", "metric"]),
            ],
            "answer": (
                "Prefer additive, optional changes; version explicitly for breaking ones; document "
                "and announce deprecation; track client usage and only remove after migration."
            ),
        },
        {
            "kind": "behavioural",
            "skill": None,
            "prompt": "Describe a code review comment that changed your mind. What was the reasoning?",
            "rubric": [
                ("Describes the specific technical point", ["comment", "review", "suggest"]),
                ("Explains why the reviewer was right", ["because", "reason", "trade"]),
                ("Shows the change made", ["changed", "refactor", "simpl"]),
            ],
            "answer": (
                "A concrete review comment, the reasoning that made it correct, and the change "
                "made — evidence of taking feedback on the technical merits."
            ),
        },
    ],
}
