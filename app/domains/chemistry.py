"""Deterministic Beginner-Level Chemistry Molecular Structure Engine (Phase 10).

Pure-Python SMILES parser and covalent valence validator for beginner molecules
(no native RDKit C++ binary required). Explicitly rejects aromaticity,
stereochemistry, ionic charges, disconnected mixtures, and invalid valences.
Never infers toxicity, reaction yields, medical properties, or lab safety.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from app.domains import DomainSimulationError
from app.models import DiagramDocument, Edge, MoleculeModel, Node, SourceInfo

ELEMENT_NAMES: dict[str, str] = {
    "H": "Hydrogen",
    "C": "Carbon",
    "N": "Nitrogen",
    "O": "Oxygen",
    "F": "Fluorine",
    "Cl": "Chlorine",
    "Br": "Bromine",
    "S": "Sulfur",
    "P": "Phosphorus",
}

STANDARD_VALENCE: dict[str, int] = {
    "H": 1,
    "C": 4,
    "N": 3,
    "O": 2,
    "F": 1,
    "Cl": 1,
    "Br": 1,
    "S": 2,
    "P": 3,
}

BOND_ORDER: dict[str, int] = {
    "single_bond": 1,
    "double_bond": 2,
    "triple_bond": 3,
}

ORDER_TO_RELATION: dict[int, str] = {
    1: "single_bond",
    2: "double_bond",
    3: "triple_bond",
}

UNSUPPORTED_SMILES_CHARS = frozenset({"@", "/", "\\", "[", "]", ".", "+", ":"})
AROMATIC_CHARS = frozenset({"c", "n", "o", "s", "p", "b"})


@dataclass(frozen=True)
class ChemistryValidationResult:
    valid_semantics: bool
    simulation_ready: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def get_atom_counts(diagram: DiagramDocument) -> dict[str, int]:
    """Count atoms by element symbol in a molecular graph."""
    counts: dict[str, int] = {}
    for node in diagram.nodes:
        if node.kind == "atom":
            el = str((node.attributes or {}).get("element", "")).strip()
            if el:
                counts[el] = counts.get(el, 0) + 1
    return dict(sorted(counts.items()))


def format_hill_formula(counts: dict[str, int]) -> str:
    """Format standard Hill molecular formula (C first, then H, then alphabetical)."""
    if not counts:
        return "Unknown"
    order: list[str] = []
    if "C" in counts:
        order.append("C")
        if "H" in counts:
            order.append("H")
    for el in sorted(counts.keys()):
        if el not in order:
            order.append(el)
    parts = [f"{el}{counts[el] if counts[el] > 1 else ''}" for el in order]
    return "".join(parts)


def get_atom_neighbors(
    diagram: DiagramDocument, atom_id: str
) -> list[tuple[Edge, Node, int]]:
    """Return directly bonded neighbor atoms and bond orders for atom_id."""
    node_by_id = {n.id: n for n in diagram.nodes}
    if atom_id not in node_by_id:
        raise DomainSimulationError(
            code="UNKNOWN_TARGET",
            message=f"Atom '{atom_id}' was not found in this molecule.",
            status_code=400,
        )
    neighbors: list[tuple[Edge, Node, int]] = []
    for edge in diagram.edges:
        order = BOND_ORDER.get(edge.relation, 1)
        if edge.source == atom_id and edge.target in node_by_id:
            neighbors.append((edge, node_by_id[edge.target], order))
        elif edge.target == atom_id and edge.source in node_by_id:
            neighbors.append((edge, node_by_id[edge.source], order))
    return neighbors


def find_shortest_bond_path(
    diagram: DiagramDocument, start_id: str, target_id: str
) -> list[str]:
    """Return shortest bond path (list of atom IDs) between start_id and target_id."""
    node_ids = {n.id for n in diagram.nodes}
    if start_id not in node_ids or target_id not in node_ids:
        return []
    if start_id == target_id:
        return [start_id]

    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}
    for edge in diagram.edges:
        if edge.source in adj and edge.target in adj:
            adj[edge.source].append(edge.target)
            adj[edge.target].append(edge.source)

    queue: deque[list[str]] = deque([[start_id]])
    visited = {start_id}
    while queue:
        path = queue.popleft()
        cur = path[-1]
        for nxt in adj[cur]:
            if nxt == target_id:
                return [*path, nxt]
            if nxt not in visited:
                visited.add(nxt)
                queue.append([*path, nxt])
    return []


def validate_molecule(diagram: DiagramDocument) -> ChemistryValidationResult:
    """Validate elements, bond relations, duplicate edges, and covalent valences."""
    errors: list[str] = []
    warnings: list[str] = []

    if diagram.domain != "chemistry_molecule":
        errors.append("Expected domain 'chemistry_molecule'.")
    if not isinstance(diagram.domain_model, MoleculeModel):
        errors.append("Expected domain_model.kind to be 'molecule'.")
        return ChemistryValidationResult(
            valid_semantics=False,
            simulation_ready=False,
            errors=errors,
            warnings=warnings,
        )

    node_by_id: dict[str, Node] = {}
    bond_sum: dict[str, int] = {}

    for node in diagram.nodes:
        if node.id in node_by_id:
            errors.append(f"Duplicate atom ID '{node.id}'.")
        node_by_id[node.id] = node
        bond_sum[node.id] = 0
        if node.kind != "atom":
            errors.append(
                f"Node '{node.id}' has kind '{node.kind}', expected 'atom' in chemistry_molecule."
            )
            continue
        el = str((node.attributes or {}).get("element", "")).strip()
        if el not in STANDARD_VALENCE:
            errors.append(
                f"Atom '{node.id}' has unsupported element '{el or 'unknown'}'. "
                f"Supported beginner elements: {', '.join(sorted(STANDARD_VALENCE))}."
            )

    seen_pairs: set[frozenset[str]] = set()
    for edge in diagram.edges:
        if edge.relation not in BOND_ORDER:
            errors.append(
                f"Edge '{edge.id}' has relation '{edge.relation}', "
                "expected 'single_bond', 'double_bond', or 'triple_bond'."
            )
            continue
        if edge.source not in node_by_id or edge.target not in node_by_id:
            errors.append(f"Bond '{edge.id}' references an unknown atom ID.")
            continue
        if edge.source == edge.target:
            errors.append(f"Bond '{edge.id}' cannot connect atom '{edge.source}' to itself.")
            continue

        pair = frozenset((edge.source, edge.target))
        if pair in seen_pairs:
            errors.append(
                f"Duplicate bond between '{edge.source}' and '{edge.target}'. "
                "Use double_bond or triple_bond instead of duplicate edges."
            )
        seen_pairs.add(pair)

        order = BOND_ORDER[edge.relation]
        bond_sum[edge.source] += order
        bond_sum[edge.target] += order

    for node in diagram.nodes:
        el = str((node.attributes or {}).get("element", "")).strip()
        max_val = STANDARD_VALENCE.get(el)
        if max_val is not None and bond_sum.get(node.id, 0) > max_val:
            errors.append(
                f"Invalid valence on {node.label} ({el}): total bond order is "
                f"{bond_sum[node.id]}, which exceeds standard valence {max_val}."
            )

    valid = len(errors) == 0
    return ChemistryValidationResult(
        valid_semantics=valid,
        simulation_ready=valid,
        errors=errors,
        warnings=warnings,
    )


def build_molecule_summary(diagram: DiagramDocument) -> str:
    """Generate a deterministic plain-language structural summary of a molecule."""
    if not isinstance(diagram.domain_model, MoleculeModel):
        return diagram.summary
    counts = get_atom_counts(diagram)
    parts = [f"{cnt} {ELEMENT_NAMES.get(el, el)} ({el})" for el, cnt in counts.items()]
    return (
        f"{diagram.title} (formula {diagram.domain_model.formula}, SMILES: "
        f"{diagram.domain_model.smiles}) contains {len(diagram.nodes)} atoms "
        f"({', '.join(parts)}) and {len(diagram.edges)} covalent bond(s). "
        "Structural connectivity only; does not infer toxicity, reaction yields, "
        "medical properties, or lab safety."
    )


def parse_smiles_to_molecule(
    smiles: str, title: str | None = None
) -> DiagramDocument:
    """Parse a beginner-level SMILES string into a validated molecular DiagramDocument.

    Explicitly rejects aromaticity, stereochemistry, charges, and invalid valences.
    Automatically adds explicit hydrogens to satisfy standard covalent valences.
    """
    raw = (smiles or "").strip()
    if not raw or len(raw) > 80:
        raise DomainSimulationError(
            code="INVALID_SMILES",
            message="SMILES must be between 1 and 80 characters.",
            status_code=400,
        )

    for ch in raw:
        if ch in UNSUPPORTED_SMILES_CHARS:
            raise DomainSimulationError(
                code="UNSUPPORTED_CHEMISTRY",
                message=(
                    f"Unsupported SMILES notation '{ch}'. Aromaticity, stereochemistry, "
                    "ionic charges, and disconnected mixtures are outside beginner scope."
                ),
                status_code=422,
            )
        if ch in AROMATIC_CHARS:
            raise DomainSimulationError(
                code="UNSUPPORTED_CHEMISTRY",
                message=(
                    f"Lowercase aromatic atom '{ch}' is outside beginner scope. "
                    "Use explicit Kekule single/double bonds instead."
                ),
                status_code=422,
            )

    atoms: list[tuple[str, str]] = []  # (atom_id, element)
    bonds: list[tuple[str, str, int]] = []  # (src_id, tgt_id, order)
    element_counters: dict[str, int] = {}
    branch_stack: list[str | None] = []
    ring_open: dict[str, tuple[str, int]] = {}
    prev_atom: str | None = None
    pending_order: int = 1

    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "(":
            if prev_atom is None:
                raise DomainSimulationError(
                    code="INVALID_SMILES",
                    message="Branch '(' cannot appear before any atom.",
                    status_code=400,
                )
            branch_stack.append(prev_atom)
            i += 1
        elif ch == ")":
            if not branch_stack:
                raise DomainSimulationError(
                    code="INVALID_SMILES",
                    message="Unmatched closing parenthesis ')' in SMILES.",
                    status_code=400,
                )
            prev_atom = branch_stack.pop()
            pending_order = 1
            i += 1
        elif ch == "-":
            pending_order = 1
            i += 1
        elif ch == "=":
            pending_order = 2
            i += 1
        elif ch == "#":
            pending_order = 3
            i += 1
        elif ch.isdigit():
            if prev_atom is None:
                raise DomainSimulationError(
                    code="INVALID_SMILES",
                    message=f"Ring closure digit '{ch}' cannot appear before an atom.",
                    status_code=400,
                )
            if ch in ring_open:
                partner, open_order = ring_open.pop(ch)
                order = max(open_order, pending_order)
                bonds.append((partner, prev_atom, order))
            else:
                ring_open[ch] = (prev_atom, pending_order)
            pending_order = 1
            i += 1
        elif ch.isupper():
            # Check two-letter elements (Cl, Br) first.
            two = raw[i : i + 2]
            if two in {"Cl", "Br"}:
                el = two
                i += 2
            elif ch in STANDARD_VALENCE:
                el = ch
                i += 1
            else:
                raise DomainSimulationError(
                    code="INVALID_SMILES",
                    message=f"Unsupported or unknown element starting at '{raw[i:i+2]}'.",
                    status_code=400,
                )

            element_counters[el] = element_counters.get(el, 0) + 1
            atom_id = f"{el}_{element_counters[el]}"
            atoms.append((atom_id, el))
            if prev_atom is not None:
                bonds.append((prev_atom, atom_id, pending_order))
            prev_atom = atom_id
            pending_order = 1
        else:
            raise DomainSimulationError(
                code="INVALID_SMILES",
                message=f"Unexpected character '{ch}' in SMILES '{raw}'.",
                status_code=400,
            )

    if branch_stack:
        raise DomainSimulationError(
            code="INVALID_SMILES",
            message="Unclosed branch '(' in SMILES.",
            status_code=400,
        )
    if ring_open:
        raise DomainSimulationError(
            code="INVALID_SMILES",
            message=f"Unclosed ring digit(s) {', '.join(sorted(ring_open))} in SMILES.",
            status_code=400,
        )
    if not atoms:
        raise DomainSimulationError(
            code="INVALID_SMILES",
            message="No valid atoms were parsed from SMILES.",
            status_code=400,
        )

    # Compute heavy-atom bond orders and materialize implicit hydrogens to satisfy valence.
    order_sum: dict[str, int] = {aid: 0 for aid, _ in atoms}
    for src, tgt, order in bonds:
        order_sum[src] += order
        order_sum[tgt] += order

    for aid, el in list(atoms):
        max_v = STANDARD_VALENCE[el]
        used = order_sum[aid]
        if used > max_v:
            raise DomainSimulationError(
                code="INVALID_VALENCE",
                message=(
                    f"Invalid valence on {el} ({aid}): bond order {used} exceeds "
                    f"standard valence {max_v}."
                ),
                status_code=422,
            )
        if el != "H":
            remaining_h = max_v - used
            for _ in range(remaining_h):
                element_counters["H"] = element_counters.get("H", 0) + 1
                h_id = f"H_{element_counters['H']}"
                atoms.append((h_id, "H"))
                bonds.append((aid, h_id, 1))

    nodes: list[Node] = []
    for aid, el in atoms:
        num = aid.split("_", 1)[1]
        nodes.append(
            Node(
                id=aid,
                kind="atom",
                label=f"{ELEMENT_NAMES[el]} {el}{num}",
                description=f"{ELEMENT_NAMES[el]} atom (standard covalent valence {STANDARD_VALENCE[el]}).",
                attributes={"element": el, "max_valence": STANDARD_VALENCE[el]},
            )
        )

    edges: list[Edge] = []
    node_label = {n.id: n.label for n in nodes}
    for idx, (src, tgt, order) in enumerate(bonds, start=1):
        rel = ORDER_TO_RELATION[order]
        bond_word = rel.replace("_", " ")
        edges.append(
            Edge(
                id=f"bond_{idx}",
                source=src,
                target=tgt,
                relation=rel,  # type: ignore[arg-type]
                description=f"{bond_word.capitalize()} between {node_label[src]} and {node_label[tgt]}.",
            )
        )

    counts = {el: cnt for el, cnt in element_counters.items() if cnt > 0}
    formula = format_hill_formula(counts)
    doc_title = (title or f"Molecule {formula} ({raw})").strip()

    doc = DiagramDocument(
        schema_version="1.0",
        id="smiles_molecule",
        title=doc_title,
        domain="chemistry_molecule",
        summary="Validated covalent molecule.",
        source=SourceInfo(mode="fixture", filename="parsed.smiles", provider=None),
        review_status="confirmed",
        nodes=nodes,
        edges=edges,
        domain_model=MoleculeModel(
            kind="molecule",
            smiles=raw,
            formula=formula,
        ),
        warnings=[],
    )

    validation = validate_molecule(doc)
    if not validation.simulation_ready:
        raise DomainSimulationError(
            code="INVALID_MOLECULE",
            message="Parsed molecule failed chemical valence validation.",
            status_code=422,
            details=validation.errors,
        )

    doc.summary = build_molecule_summary(doc)
    return doc
