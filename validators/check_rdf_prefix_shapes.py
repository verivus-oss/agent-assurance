#!/usr/bin/env python3
"""Exercise the three RDF identifier prefix shapes with accepted and rejected graphs."""

from pathlib import Path

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import SH


ROOT = Path(__file__).resolve().parents[1]
DAG = Namespace("https://verivus-oss.org/dagtoml/v1#")
CASES = (
    (DAG.Requirement, DAG.RequirementIdPrefixShape, "REQ:"),
    (DAG.Implementation, DAG.ImplementationIdPrefixShape, "IMP:"),
    (DAG.Test, DAG.TestIdPrefixShape, "TEST:"),
)


def verdict(shapes: Graph, entity_class: URIRef, label: str) -> tuple[bool, Graph]:
    subject = DAG.control
    data = Graph()
    data.add((subject, RDF.type, entity_class))
    data.add((subject, RDFS.label, Literal(label)))
    conforms, results, _ = validate(
        data_graph=data, shacl_graph=shapes, inference="none", advanced=False,
    )
    if not isinstance(results, Graph):
        raise AssertionError("SHACL engine did not return a result graph")
    return conforms, results


def main() -> None:
    shapes = Graph()
    shapes.parse(ROOT / "reference/database/rdf/shapes.ttl", format="turtle")
    if not shapes:
        raise AssertionError("RDF shapes graph is empty")
    declared = {subject for subject in shapes.subjects(RDF.type, SH.NodeShape)
                if str(subject).endswith("IdPrefixShape")}
    expected = {shape for _, shape, _ in CASES}
    if declared != expected:
        raise AssertionError("identifier prefix shape population changed")
    for entity_class, shape, prefix in CASES:
        if (shape, SH.targetClass, entity_class) not in shapes:
            raise AssertionError("identifier shape target changed")
        good, good_results = verdict(shapes, entity_class, prefix + "7")
        bad, bad_results = verdict(shapes, entity_class, "WRONG:7")
        if not good or list(good_results.subjects(RDF.type, SH.ValidationResult)):
            raise AssertionError("SHACL rejected an accepted prefix")
        if bad or shape not in set(bad_results.objects(None, SH.sourceShape)):
            raise AssertionError("SHACL did not reject the wrong prefix with the expected shape")
    print("RDF prefix shapes: 3 accepted and 3 rejected graphs executed")


if __name__ == "__main__":
    main()
