# L12: Testing & Evaluation I — Figures

## Slide 1 — Title

**Figure:** *AI testing pyramid.* Classic testing pyramid adapted for AI systems. Bottom level (widest): Unit Tests — data functions, feature transformations, prompt templates. Middle level: Integration Tests — pipeline end-to-end, API contracts, component interactions. Top level: System Tests — full AI system behavior against business criteria. Additional AI-specific layers shown as overlays: Evaluation Tests (quality metrics), Behavioral Tests (edge cases and invariants). The pyramid communicates: test at every level, with more tests at lower levels.

---

## Slide 2 — How AI Systems Fail: A Taxonomy

**Figure:** *AI failure taxonomy map.* Four quadrant diagram: x-axis: Static (structural) ↔ Dynamic (distributional), y-axis: Deterministic (same input → same failure) ↔ Probabilistic (failure rate dependent on input distribution). Each failure mode from the list is placed in its quadrant. Data failures: top-left. Model failures: top-right (quality drift) and bottom-right (edge cases). System failures: top-left. LLM failures: bottom-right. The quadrant placement reveals the testing strategy: deterministic failures caught by unit tests; probabilistic failures caught by evaluation.

---

## Slide 3 — The AI Testing Pyramid in Detail

**Figure:** *Detailed AI testing pyramid.* Four layers with: name, test count estimate (many unit, few system), run time, and NorthStar example test for each layer. Pyramid is wide at bottom (hundreds of unit tests) and narrow at top (5-10 system tests). The overall shape communicates the investment distribution: most tests are unit tests.

---

## Slide 4 — Unit Testing for AI Pipelines

**Figure:** *Unit test run output.* Terminal-style mockup showing pytest run: `tests/test_feature_engineering.py::TestRFMFeatures::test_recency_computed_from_last_transaction PASSED`. Four tests shown, all PASSED. `4 passed in 0.23s`. Clean, green output communicates: fast, deterministic, reliable.

---

## Slide 5 — Unit Testing Anti-Patterns for AI

**Figure:** *Five anti-patterns checklist.* Five rows with anti-pattern name, code snippet of the wrong approach (red background), and the fix (green background). "Testing the model" row has a production incident counter: "Responsible for ~20% of 'tests pass but model is wrong' incidents."

---

## Slide 6 — Integration Testing for AI Pipelines

**Figure:** *Integration test scope diagram.* System diagram with NorthStar components (Glue → Feature Store → Training Job → Model Registry → Endpoint). Red boundary boxes drawn around each component interface, labeled "Integration test boundary." Integration tests are the tests that cross these boundaries. Contrasts with unit tests (contained within a single component) and system tests (crossing all boundaries).

---

## Slide 7 — System Testing: End-to-End Behavior Validation

**Figure:** *System test execution flow.* Flowchart showing system test run: Load test fixtures → Invoke full pipeline (not mocked) → Capture results → Assert business behavior. Four test boxes (from code above) connected to their assertion. Color: PASS in green, FAIL in red. Below: system test runtime estimate: "~45 minutes on full NorthStar platform."

---

## Slide 8 — Testing for Data Drift (Distribution Tests)

**Figure:** *Distribution drift visualization.* Three-panel figure. Left: "No drift" — training distribution (blue) and today's distribution (orange) nearly overlapping. Middle: "Moderate drift" — PSI 0.1-0.2, distributions visibly different but same shape. Right: "Significant drift" — PSI > 0.2, distributions clearly different shapes. Caption: "PSI test catches the 'significant drift' case automatically."

---

## Slide 9 — Behavioral Testing for LLM Systems

**Figure:** *Behavioral test taxonomy diagram.* Three columns: Deterministic (format, schema), Factual (grounding, no hallucination), Behavioral (invariants, monotonicity). Each column: 2-3 example tests with PASS/FAIL status. A fourth column: "What breaks these," showing failure modes that each test type catches. Communicates: behavioral tests catch a different class of failure than unit tests.

---

## Slide 10 — Adversarial and Security Testing for AI

**Figure:** *Security test results summary.* Table with three sections (Prompt Injection, Data Extraction, Authority Boundary). Each section includes: the number of test cases, PASS/FAIL results, and one example of a caught violation. Guardrail block rate shown per test category. Overall: "23/23 security tests PASS" in green with confidence statement.

---

## Slide 11 — The NorthStar Test Suite Architecture

**Figure:** *Test execution timeline diagram.* Horizontal timeline with five labeled events (pre-commit, PR, pipeline run, deployment gate, nightly). Each event: which test directories run, estimated duration, and pass/fail consequence (PR blocked, deployment blocked, nightly alert). Color-coded by speed: fast (green), medium (amber), slow (red/nightly).

---

## Slide 12 — Lab 4 Testing Requirements Preview

**Figure:** *Lab 4 test requirements checklist.* Four-row table (one per test category) with checkboxes for: required count, example provided in Lab 4 starter code, common failure mode noted. Lab 4 grade distribution pie chart: 20% testing, 30% SageMaker pipeline, 30% CodePipeline, 20% documentation/ADR.

---

## Slide 13 — Evaluation vs. Testing: The Distinction

**Figure:** *Venn diagram: Testing vs. Evaluation.* Two overlapping circles. Left (Testing only): "Correct behavior on edge cases; follows required format; no prompt injection." Right (Evaluation only): "High average AUC; high RAGAS faithfulness." Overlap (both): "Must pass both to deploy." Small region outside both circles labeled "Must never happen: deploy without testing or evaluation." The diagram makes the distinction and the requirement visually clear.

---

## Slide 14 — Continuous Evaluation in Production

**Figure:** *Continuous evaluation timeline graphic.* Three swimlanes (Churn, RAG, Agent). Each swimlane: horizontal timeline with evaluation events marked at their frequency (daily, weekly, monthly). Each event labeled with evaluation type and alert threshold. Shows that evaluation is an ongoing operational activity, not a one-time pre-deployment check.

---

## Slide 15 — The Testing Debt Problem in AI

**Figure:** *Testing debt cost curve.* Two lines over time: "With tests" (investment spikes at the start, then maintenance costs remain flat) vs. "Without tests" (no upfront cost, but debugging costs accelerate over time, crossing the "with tests" line at month 3-4 and diverging significantly by month 12). Classic technical debt visualization, specific to AI systems.

---

## Slide 16 — Key Takeaways + What's Next

**Figure:** *Five-takeaway summary card.* Lab 4 assigned announcement in teal box. Link to the NorthStar test suite template in the course repo. Testing pyramid thumbnail recap.
