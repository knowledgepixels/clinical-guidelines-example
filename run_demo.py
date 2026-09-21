"""Answers the three demo questions against the draft nanopublications.

Loads every ``.trig`` file under ``nanopubs/`` together with the fictional
patient profiles under ``profiles/`` into a single RDF dataset and runs the
SPARQL queries in ``queries/`` over it, so that the prototype can be inspected
without publishing anything to the nanopublication network.
"""

import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from rdflib import ConjunctiveGraph, URIRef
from rdflib.term import Literal

PROJECT_DIRECTORY = Path(__file__).resolve().parent
NANOPUB_DIRECTORY = PROJECT_DIRECTORY / "nanopubs"
PROFILE_DIRECTORY = PROJECT_DIRECTORY / "profiles"
QUERY_DIRECTORY = PROJECT_DIRECTORY / "queries"

PROFILE_NAMESPACE = "https://example.org/demo/profile/"
DEMO_PROFILES = ["profile-1", "profile-2", "profile-3"]

ABBREVIATIONS = {
    "https://example.org/demo/cpg-vocab/": "cpg:",
    "https://example.org/demo/clinical-guidance/": "ex:",
    "https://example.org/demo/source/": "src:",
    "https://example.org/demo/profile/": "profile:",
    "https://example.org/demo/guidance/": "doc:",
    "http://purl.org/nanopub/temp/": "np:",
    "https://orcid.org/": "orcid:",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs:",
    "http://purl.org/dc/terms/": "dct:",
}


def load_dataset() -> ConjunctiveGraph:
    """Loads all nanopublication and profile files into one dataset.

    :return: the dataset holding every named graph of the demonstration
    """
    dataset = ConjunctiveGraph()
    for trig_file in sorted(NANOPUB_DIRECTORY.glob("*.trig")) + sorted(PROFILE_DIRECTORY.glob("*.trig")):
        dataset.parse(trig_file, format="trig")
    return dataset


def abbreviate(term) -> str:
    """Shortens an IRI to a prefixed name and strips nanopublication graph suffixes.

    :param term: an RDF term from a query result
    :return: a compact human-readable rendering of the term
    """
    if term is None:
        return ""
    if isinstance(term, Literal):
        return str(term)
    text = str(term)
    for namespace, prefix in ABBREVIATIONS.items():
        if text.startswith(namespace):
            return prefix + text[len(namespace):]
    return text


def bind_parameters(query_text: str, parameters: dict) -> str:
    """Substitutes the grlc-style query parameters with concrete IRIs.

    Textual substitution is used rather than SPARQL result bindings because a
    variable bound from the outside is not visible inside a nested
    ``filter not exists`` block, which silently widens the applicability checks.

    :param query_text: the stored query
    :param parameters: parameter name without the leading ``?_`` mapped to its IRI
    :return: the query with every parameter replaced by an IRI
    """
    for name, iri in parameters.items():
        query_text = query_text.replace(f"?_{name}", f"<{iri}>")
    return query_text


def run_query(dataset: ConjunctiveGraph, query_name: str, parameters: dict) -> list:
    """Runs one of the stored SPARQL queries.

    :param dataset: the dataset to query
    :param query_name: file name of the query inside the queries directory
    :param parameters: parameter name without the leading ``?_`` mapped to its IRI
    :return: the result rows, each as a dictionary of variable name to term
    """
    query_text = bind_parameters((QUERY_DIRECTORY / query_name).read_text(), parameters)
    result = dataset.query(query_text)
    variables = [str(variable) for variable in result.vars]
    return [dict(zip(variables, row)) for row in result]


def print_heading(text: str) -> None:
    """Prints a section heading.

    :param text: the heading text
    """
    print()
    print(text)
    print("-" * len(text))


def print_records(rows: list, fields: list) -> None:
    """Prints query result rows as indented records.

    :param rows: the result rows
    :param fields: the variable names to show, in display order
    """
    if not rows:
        print("  (none)")
        return
    width = max(len(field) for field in fields)
    for index, row in enumerate(rows):
        if index:
            print()
        for field in fields:
            value = abbreviate(row.get(field))
            if value:
                print(f"  {field.ljust(width)}  {value}")


def current_applicable_recommendations(dataset: ConjunctiveGraph, profile: URIRef) -> list:
    """Finds the recommendation versions that are current and applicable to a profile.

    :param dataset: the dataset to query
    :param profile: the patient profile to evaluate
    :return: the matching result rows
    """
    return run_query(dataset, "q1-current-applicable-recommendation.rq", {"profile": profile})


def applicable_superseded_recommendations(dataset: ConjunctiveGraph, profile: URIRef) -> list:
    """Finds superseded recommendation versions that would have applied to a profile.

    :param dataset: the dataset to query
    :param profile: the patient profile to evaluate
    :return: the matching result rows
    """
    return run_query(dataset, "q1b-applicable-superseded-recommendation.rq", {"profile": profile})


def unique_terms(rows: list, field: str) -> list:
    """Collects the distinct values of one result field, preserving order.

    :param rows: the result rows
    :param field: the variable name to collect
    :return: the distinct terms
    """
    collected = []
    for row in rows:
        term = row.get(field)
        if term is not None and term not in collected:
            collected.append(term)
    return collected


def report_profile(dataset: ConjunctiveGraph, profile_name: str) -> None:
    """Reports the full answer for one fictional profile.

    :param dataset: the dataset to query
    :param profile_name: local name of the profile within the profile namespace
    """
    profile = URIRef(PROFILE_NAMESPACE + profile_name)
    label = dataset.value(profile, URIRef("http://www.w3.org/2000/01/rdf-schema#label"))
    print()
    print("=" * 100)
    print(f"{profile_name}: {label}")
    print("=" * 100)

    applicable = current_applicable_recommendations(dataset, profile)

    print_heading("1. Current applicable recommendation")
    print_records(applicable, [
        "recommendation", "guidance_version", "version_identifier", "issued", "strength",
        "dose", "route", "frequency", "maximum_duration", "recommendation_text", "asserted_in",
    ])

    if applicable:
        traced_recommendations = unique_terms(applicable, "recommendation")
    else:
        print_heading("1b. Why the current recommendation does not apply")
        print_records(
            run_query(dataset, "q2-why-a-recommendation-does-not-apply.rq", {"profile": profile}),
            ["recommendation", "reason", "blocking_element_label", "asserted_in"],
        )
        superseded = applicable_superseded_recommendations(dataset, profile)
        print_heading("1c. Superseded versions that would have applied")
        print_records(superseded, [
            "recommendation", "superseding_recommendation", "version_identifier", "issued",
            "maximum_duration", "recommendation_text", "asserted_in",
        ])
        traced_recommendations = unique_terms(superseded, "superseding_recommendation")

    for recommendation in traced_recommendations:
        print_heading(f"2. What changed since the previous version of {abbreviate(recommendation)}")
        print_records(
            run_query(dataset, "q3-what-changed-since-previous-version.rq", {"recommendation": recommendation}),
            ["change_type", "change_label", "changed_aspect", "previous_value", "new_value",
             "motivating_source", "curation_note", "asserted_in"],
        )

        print_heading("3a. Evidence and sources behind it")
        print_records(
            run_query(dataset, "q4-evidence-trail.rq", {"recommendation": recommendation}),
            ["evidence_record", "certainty", "source_label", "source_year", "citation",
             "asserted_in", "source_described_in"],
        )

        print_heading("3b. Nanopublication trail per component")
        print_records(
            run_query(dataset, "q5-nanopub-provenance-trail.rq", {"recommendation": recommendation}),
            ["component_aspect", "component", "nanopub_label", "attributed_to", "derived_from", "created"],
        )


def main() -> None:
    """Loads the dataset and reports on every demonstration profile."""
    dataset = load_dataset()
    graph_count = len(list(dataset.contexts()))
    print(f"Loaded {len(dataset)} triples in {graph_count} named graphs "
          f"from {len(list(NANOPUB_DIRECTORY.glob('*.trig')))} nanopublication drafts.")
    for profile_name in DEMO_PROFILES:
        report_profile(dataset, profile_name)


if __name__ == "__main__":
    main()
