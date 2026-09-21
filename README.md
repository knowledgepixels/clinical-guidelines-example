# Versioned clinical guidance as nanopublications — prototype

> **Synthetic demonstration only.** Guidance A, Condition A, Criteria B/B1/B2, Intervention C,
> Standard Approach D, Contraindications K/L, the demo-unit, and every trial, pooled analysis and
> safety report cited here are fictional. Nothing in this repository is clinical guidance or
> clinical advice. Every nanopublication is marked `npx:ExampleNanopub` and carries an
> `rdfs:comment` saying so. **Nothing here is signed or published** — the drafts use
> `http://purl.org/nanopub/temp/npNN/` placeholder URIs.

## The three questions

For a given fictional profile the prototype answers:

1. **What is the current applicable recommendation?** — the recommendation version that is not
   superseded and whose population, applicability conditions and contraindications the profile
   satisfies, together with its full regimen.
2. **What changed since the previous version?** — every recorded change between v1.0 and v2.0,
   with the aspect changed, the old and new values, and the evidence that motivated it.
3. **What is the evidence/source trail behind it?** — the evidence record and its sources, plus,
   per component of the recommendation, which nanopublication asserts it, who it is attributed to
   and which guidance document it was derived from.

## Running it

```bash
python3 run_demo.py
```

Requires `rdflib` (tested with 6.0.2). The script loads all 16 draft nanopublications plus the
three fictional profiles into one RDF dataset and runs the queries in `queries/`. No network
access, no registry, no signing.

To validate the drafts:

```bash
java -jar ~/.nanopub/lib/nanopub-1.94.0-jar-with-dependencies.jar check nanopubs/*.trig
```

All 16 report *valid (not trusty)*. The remaining issues are expected for unsigned drafts: no
signature element, no assertion/provenance template links (see *Before publishing* below), and
`Unexpected graph uri` — an artifact of the placeholder URI that disappears once `sign` replaces
it with a trusty URI.

## What is in it

| # | File | Asserts |
|---|------|---------|
| 01 | `np01-guidance-a-v1-version-record.trig` | Guidance A v1.0: version identifier, **version date** (2024) |
| 02 | `np02-recommendation-v1.trig` | The **recommendation assertion** itself: verbatim text, strength, intervention |
| 03 | `np03-population-v1.trig` | **Population**: adults with Condition A |
| 04 | `np04-applicability-conditions-v1.trig` | **Applicability conditions**: Criteria B ∧ no response to Standard Approach D |
| 05 | `np05-regimen-v1.trig` | **Dose, route, frequency, duration** (14 days) and the reassessment requirement |
| 06 | `np06-contraindications-v1.trig` | **Contraindication** K |
| 07 | `np07-evidence-v1.trig` | **Evidence/source record** for v1.0: certainty, DT-101, DPA-03 |
| 08 | `np08-guidance-a-v2-version-record.trig` | Guidance A v2.0: version identifier, **version date** (2026) |
| 09 | `np09-recommendation-v2.trig` | The v2.0 recommendation assertion |
| 10 | `np10-population-v2.trig` | Population for v2.0 (the same population resource, re-linked) |
| 11 | `np11-applicability-conditions-v2.trig` | Applicability conditions: Criteria B1 ∧ B2, each linked to B by `cpg:narrows` |
| 12 | `np12-regimen-v2.trig` | Dose, route, frequency (unchanged) and duration (7 days) |
| 13 | `np13-contraindications-v2.trig` | Contraindications K and L |
| 14 | `np14-evidence-v2.trig` | Evidence/source record for v2.0: DT-101 (carried over), DT-207, DSR-14 |
| 15 | `np15-supersession.trig` | The **supersedes relationship**, as stated by the guidance itself |
| 16 | `np16-change-set-v1-to-v2.trig` | The **change set**: what changed, what stayed, and why |

Each component is its own nanopublication, so it can be cited, annotated, superseded or retracted
on its own, and the query results name the asserting nanopublication for every single fact.

```
                 ex:recommendation-c-for-condition-a          (version-independent identity)
                        ^                    ^
            dct:isVersionOf              dct:isVersionOf
                        |                    |
   np02 ->  ...-v1  <------ dct:replaces ------  ...-v2  <- np09
             |                (np15)              |
   np03 -> appliesToPopulation ............ appliesToPopulation <- np10   (same population IRI)
   np04 -> hasApplicabilityConditions      hasApplicabilityConditions <- np11
   np05 -> hasRegimen                      hasRegimen                 <- np12
   np06 -> contraindicatedInPresenceOf     contraindicatedInPresenceOf <- np13
   np07 -> supportedByEvidence             supportedByEvidence         <- np14
                        \                    /
                         np16: cpg:GuidanceChangeSet
```

## Modelling decisions worth discussing

- **Link and detail travel together.** Each component nanopublication asserts both the link from
  the recommendation version (`ex:...-v1 cpg:hasRegimen ex:regimen-v1`) and the component's own
  description. The core recommendation nanopublication is therefore not a hub that must be
  reissued whenever a component changes.
- **Shared IRIs make the diff visible without reading the change set.** The population, dose,
  route and frequency resources are the *same* IRIs in both versions; the applicability condition
  sets and regimens are version-specific. What was reused and what was replaced is readable off
  the graph.
- **Two kinds of "changed".** `cpg:Narrowing` / `cpg:Addition` record changes the guidance states.
  `cpg:NotRestated` records that v1.0 said something v2.0 does not mention — the prior-non-response
  requirement and the 14-day reassessment. These carry a `cpg:hasCurationNote` saying the version
  text does not settle whether the requirement was dropped or merely not repeated. Flagging this
  rather than silently deciding it is the point: a real guideline comparison is full of these.
- **Supersession and change set are separate nanopublications.** np15 is what the guidance itself
  states ("This version explicitly supersedes Version 1.0"), attributed to the guidance document.
  np16 is a curator's comparison of two texts, attributed to the curator and `prov:wasGeneratedBy`
  a comparison activity. Different claims, different trust, different retraction paths.
- **Criteria B1 and B2 declare `cpg:narrows ex:criteria-b`.** A profile meeting B1 therefore also
  meets v1.0's Criteria B requirement, via the `cpg:narrows*` path in the queries. This is what
  lets one profile be evaluated against both versions without restating findings per version.
- **Profiles are not nanopublications.** `profiles/demo-profiles.trig` is plain data in one named
  graph. Patient data does not belong on a public network; the recommendations do.
- **The `cpg:` vocabulary is a placeholder.** `https://example.org/demo/cpg-vocab/` stands in for
  what a real deployment would draw from existing vocabularies — CPG-on-FHIR for recommendation
  structure, SNOMED CT for conditions and routes, ATC/RxNorm for interventions, UCUM for units,
  GRADE for certainty of evidence. The nanopublication decomposition does not depend on that
  choice; only the predicate and class IRIs change.

## What the demo prints

| Profile | Findings | Result |
|---------|----------|--------|
| profile-1 | B1, B2, no response to D | v2.0 applies: 10 demo-units, oral, once daily, **up to 7 days** |
| profile-2 | B1 only, no response to D | No current recommendation — **Criteria B2 not met** (np11). Would have been eligible under the superseded v1.0 |
| profile-3 | B1, B2, Contraindication L | No current recommendation — **Contraindication L present** (np13). Would have been eligible under v1.0 |

Profiles 2 and 3 are the interesting ones: the narrowing and the new contraindication are exactly
what excludes them, and the change set nanopublication names the evidence that motivated each.

## Queries

| File | Answers |
|------|---------|
| `q1-current-applicable-recommendation.rq` | Question 1 |
| `q1b-applicable-superseded-recommendation.rq` | Same, but for superseded versions — "would this have applied before?" |
| `q2-why-a-recommendation-does-not-apply.rq` | Which specific condition or contraindication blocks it, and where that is asserted |
| `q3-what-changed-since-previous-version.rq` | Question 2 |
| `q4-evidence-trail.rq` | Question 3, clinical evidence level |
| `q5-nanopub-provenance-trail.rq` | Question 3, nanopublication level: one row per component |

Parameters follow the grlc convention used by Nanopub Query: `?_profile` and `?_recommendation`
are substituted before execution, so the same files can be turned into grlc query nanopublications
later. `run_demo.py` substitutes them textually rather than passing SPARQL bindings, because a
variable bound from outside is not visible inside a nested `filter not exists` in rdflib 6.0.2 —
which silently widened the applicability check to "some profile meets this criterion".

For the same reason the applicability test in `q1` counts required elements against met elements
in two sub-selects instead of nesting `filter not exists` inside `filter not exists`. It is also
the more portable formulation.

## Before any of this is published

1. **Assertion/provenance/pubinfo templates.** None of these structures has a matching
   nanopublication template yet, so the drafts carry no `nt:wasCreatedFromTemplate` links. Templates
   would have to be designed and published first — one per component shape.
2. **Stable IRIs.** The drafts use `https://example.org/demo/clinical-guidance/...` IRIs so the
   files are self-contained and can be signed in any order. In a published set the version-specific
   resources would be `sub:` IRIs introduced by their own nanopublication, and the component
   nanopublications would reference them by trusty URI — which means publishing the recommendation
   nanopublication first and filling its trusty URI into the rest.
3. **`npx:supersedes` vs `dct:replaces`.** np15 asserts content-level supersession between the two
   guidance versions. Nanopublication-level supersession (`npx:supersedes` in pubinfo) is a
   different statement — "this nanopublication replaces that one" — and is only valid when both are
   signed with the same key. Do not conflate them.
4. **An index** (`mkindex`) grouping the 16 nanopublications, published after signing.
5. **Signing identity.** Decide whether these are published by a person or by a curation agent with
   its own key and introduction nanopublication.
6. Keep the `npx:ExampleNanopub` marking as long as the content is fictional.
