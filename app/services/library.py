"""Scalable STEM Learning Library with 20 distinct, validated lessons (Phase 16).

Every lesson provides a distinct scientific diagram configuration or dataset,
passes deterministic domain validation at startup, and preserves backward
compatibility with the original 5 bundled fixtures.
"""

from __future__ import annotations

from app.domains.chemistry import parse_smiles_to_molecule
from app.models import (
    DiagramDocument,
    Edge,
    FlowchartModel,
    FoodWebModel,
    LessonDetailResponse,
    LessonDifficulty,
    LessonMetadata,
    LessonPackagePayload,
    LessonPackageValidationResponse,
    LessonStepItem,
    MathPlotModel,
    MathPlotPoint,
    Node,
    SeriesCircuitModel,
    SourceInfo,
)
from app.services.description import describe_diagram
from app.services.fixtures import FixtureRepository
from app.services.learning import generate_challenges
from app.services.validators import validate_diagram


def _standard_steps(domain_hint: str) -> list[LessonStepItem]:
    return [
        LessonStepItem(
            step_id="explore",
            title="Explore Components",
            instruction=f"Inspect each {domain_hint} one at a time by keyboard or voice.",
        ),
        LessonStepItem(
            step_id="predict",
            title="Make a Prediction",
            instruction="Predict the scientific outcome before running the verified check.",
        ),
        LessonStepItem(
            step_id="experiment",
            title="Run Verified Experiment",
            instruction="Test your prediction using the deterministic Python engine.",
        ),
        LessonStepItem(
            step_id="understand",
            title="Understand & Review",
            instruction="Review the evidence and choose your next lesson.",
        ),
    ]


def _make_physics_diagram(
    *,
    diagram_id: str,
    title: str,
    switch_state: str,
    two_bulbs: bool,
) -> DiagramDocument:
    nodes = [
        Node(
            id="bat_1",
            kind="battery",
            label="Battery B1",
            description="Power source in the single-loop series circuit.",
        ),
        Node(
            id="sw_1",
            kind="switch",
            label="Switch S1",
            description=f"Series switch currently {switch_state}.",
        ),
        Node(
            id="bulb_1",
            kind="bulb",
            label="Bulb L1",
            description="Primary light bulb in the series loop.",
        ),
    ]
    if two_bulbs:
        nodes.append(
            Node(
                id="bulb_2",
                kind="bulb",
                label="Bulb L2",
                description="Second light bulb connected in series with Bulb L1.",
            )
        )

    seq = [n.id for n in nodes]
    edges: list[Edge] = []
    for i, src in enumerate(seq):
        tgt = seq[(i + 1) % len(seq)]
        edges.append(
            Edge(
                id=f"w_{i + 1}",
                source=src,
                target=tgt,
                relation="wire",
                description=f"Wire connecting {src} and {tgt} in the single series loop.",
            )
        )

    doc = DiagramDocument(
        id=diagram_id,
        title=title,
        domain="physics_circuit",
        summary=title,
        source=SourceInfo(mode="fixture", filename=f"{diagram_id}.json", provider=None),
        review_status="confirmed",
        nodes=nodes,
        edges=edges,
        domain_model=SeriesCircuitModel(
            kind="series_circuit",
            loop_wired=True,
            sequence=seq,
            switch_states={"sw_1": switch_state},
        ),
    )
    doc.summary = describe_diagram(doc)
    return doc


def _make_biology_diagram(
    *,
    diagram_id: str,
    title: str,
    organisms: list[tuple[str, str, str]],
    feeding: list[tuple[str, str, str]],
) -> DiagramDocument:
    nodes = [
        Node(id=oid, kind="organism", label=label, description=desc)
        for oid, label, desc in organisms
    ]
    edges = [
        Edge(
            id=f"feed_{i + 1}",
            source=src,
            target=tgt,
            relation="energy_to",
            description=desc,
        )
        for i, (src, tgt, desc) in enumerate(feeding)
    ]
    doc = DiagramDocument(
        id=diagram_id,
        title=title,
        domain="biology_food_web",
        summary=title,
        source=SourceInfo(mode="fixture", filename=f"{diagram_id}.json", provider=None),
        review_status="confirmed",
        nodes=nodes,
        edges=edges,
        domain_model=FoodWebModel(
            kind="food_web",
            arrow_convention="food_to_consumer",
        ),
    )
    doc.summary = describe_diagram(doc)
    return doc


def _make_math_diagram(
    *,
    diagram_id: str,
    title: str,
    x_label: str,
    x_unit: str,
    y_label: str,
    y_unit: str,
    function_label: str,
    raw_points: list[tuple[float, float, str]],
) -> DiagramDocument:
    nodes: list[Node] = []
    points: list[MathPlotPoint] = []
    for idx, (xv, yv, desc) in enumerate(raw_points, start=1):
        pid = f"pt_{idx}"
        label = f"Point {idx} ({xv:g} {x_unit}, {yv:g} {y_unit})".replace(" )", ")")
        nodes.append(
            Node(
                id=pid,
                kind="data_point",
                label=label,
                description=desc,
                attributes={"x": xv, "y": yv, "exact": True},
            )
        )
        points.append(MathPlotPoint(id=pid, x=xv, y=yv, label=label, exact=True))

    edges: list[Edge] = []
    for idx in range(len(points) - 1):
        p1, p2 = points[idx], points[idx + 1]
        dy = p2.y - p1.y
        trend = "increasing" if dy > 0 else "decreasing" if dy < 0 else "constant"
        edges.append(
            Edge(
                id=f"seg_{idx + 1}",
                source=p1.id,
                target=p2.id,
                relation="series_next",
                description=f"From ({p1.x:g}, {p1.y:g}) to ({p2.x:g}, {p2.y:g}): {trend}.",
            )
        )

    doc = DiagramDocument(
        id=diagram_id,
        title=title,
        domain="math_plot",
        summary=title,
        source=SourceInfo(mode="fixture", filename=f"{diagram_id}.json", provider=None),
        review_status="confirmed",
        nodes=nodes,
        edges=edges,
        domain_model=MathPlotModel(
            kind="math_plot",
            x_label=x_label,
            x_unit=x_unit,
            y_label=y_label,
            y_unit=y_unit,
            function_label=function_label,
            points=points,
        ),
    )
    doc.summary = describe_diagram(doc)
    return doc


def _make_flowchart_diagram(
    *,
    diagram_id: str,
    title: str,
    nodes: list[Node],
    edges: list[Edge],
    default_inputs: dict[str, int | bool],
    max_steps: int = 50,
) -> DiagramDocument:
    doc = DiagramDocument(
        id=diagram_id,
        title=title,
        domain="cs_flowchart",
        summary=title,
        source=SourceInfo(mode="fixture", filename=f"{diagram_id}.json", provider=None),
        review_status="confirmed",
        nodes=nodes,
        edges=edges,
        domain_model=FlowchartModel(
            kind="flowchart",
            entry_node=nodes[0].id,
            inputs=default_inputs,
            max_steps=max_steps,
        ),
    )
    doc.summary = describe_diagram(doc)
    return doc


def _make_chemistry_diagram(
    *,
    diagram_id: str,
    title: str,
    smiles: str,
) -> DiagramDocument:
    doc = parse_smiles_to_molecule(smiles, title=title)
    doc.id = diagram_id
    doc.source = SourceInfo(mode="fixture", filename=f"{diagram_id}.json", provider=None)
    doc.review_status = "confirmed"
    doc.summary = describe_diagram(doc)
    return doc


class LessonLibrary:
    """Validated registry of 20 distinct STEM lessons across all 5 supported domains."""

    def __init__(self, fixture_repo: FixtureRepository) -> None:
        self._fixture_repo = fixture_repo
        self._lessons: dict[str, tuple[LessonMetadata, DiagramDocument]] = {}
        self._build_starter_library()

    def _register(
        self,
        *,
        lesson_id: str,
        title: str,
        difficulty: LessonDifficulty,
        description: str,
        learning_objectives: list[str],
        prerequisites: list[str],
        estimated_duration: str,
        supported_actions: list[str],
        explanations: list[str],
        diagram: DiagramDocument,
        step_hint: str,
    ) -> None:
        validation = validate_diagram(diagram)
        if not validation.valid or not validation.simulation_ready:
            raise ValueError(
                f"Library lesson '{lesson_id}' failed validation: {validation.errors}"
            )
        challenge_set = generate_challenges(diagram)
        meta = LessonMetadata(
            lesson_id=lesson_id,
            title=title,
            domain=diagram.domain,
            difficulty=difficulty,
            description=description,
            learning_objectives=learning_objectives,
            prerequisites=prerequisites,
            diagram_id=diagram.id,
            estimated_duration=estimated_duration,
            lesson_steps=_standard_steps(step_hint),
            supported_actions=supported_actions,
            challenges=[c.id for c in challenge_set.challenges],
            explanations=explanations,
            review_status=diagram.review_status,
            provenance="Pre-annotated curriculum lesson — no AI used",
        )
        self._lessons[lesson_id] = (meta, diagram)

    def _build_starter_library(self) -> None:
        # =========================
        # PHYSICS (4 lessons)
        # =========================
        phy_base = self._fixture_repo.get_example("physics_series")
        assert phy_base is not None
        self._register(
            lesson_id="phy_01_simple_series",
            title="Simple Series Circuit (Open Switch)",
            difficulty="beginner",
            description="Explore a single-loop circuit with a battery, open switch, and one bulb.",
            learning_objectives=[
                "Identify battery, switch, and bulb roles in a series loop.",
                "Predict what happens when an open switch closes.",
            ],
            prerequisites=[],
            estimated_duration="4 min",
            supported_actions=["toggle_switch", "reset_experiment"],
            explanations=[
                "An open switch breaks the single loop so the bulb stays OFF.",
                "Closing the switch completes the path so the bulb turns ON.",
            ],
            diagram=phy_base,
            step_hint="circuit component",
        )

        self._register(
            lesson_id="phy_02_closed_switch",
            title="Opening a Closed Series Circuit",
            difficulty="beginner",
            description="Start with a lit bulb in a closed loop and observe what happens when the switch opens.",
            learning_objectives=[
                "Verify why a closed series loop lights the bulb.",
                "Predict the effect of opening a closed switch.",
            ],
            prerequisites=["phy_01_simple_series"],
            estimated_duration="4 min",
            supported_actions=["toggle_switch", "reset_experiment"],
            explanations=[
                "With the switch closed, the single loop is complete and Bulb L1 is ON.",
                "Opening the switch breaks the path and turns Bulb L1 OFF.",
            ],
            diagram=_make_physics_diagram(
                diagram_id="phy_closed_switch",
                title="Closed Switch Series Circuit",
                switch_state="closed",
                two_bulbs=False,
            ),
            step_hint="circuit component",
        )

        self._register(
            lesson_id="phy_03_two_bulb_open",
            title="Two-Bulb Series Circuit (Open Switch)",
            difficulty="intermediate",
            description="Explore two bulbs wired in a single series loop with an open switch.",
            learning_objectives=[
                "Trace a 4-component single-loop series circuit.",
                "Predict whether one or both bulbs turn ON when the switch closes.",
            ],
            prerequisites=["phy_02_closed_switch"],
            estimated_duration="5 min",
            supported_actions=["toggle_switch", "reset_experiment"],
            explanations=[
                "In a single series loop, both bulbs share the same switch-controlled path.",
                "Closing Switch S1 turns both Bulb L1 and Bulb L2 ON together.",
            ],
            diagram=_make_physics_diagram(
                diagram_id="phy_two_bulb_open",
                title="Two-Bulb Series Circuit (Open)",
                switch_state="open",
                two_bulbs=True,
            ),
            step_hint="circuit component",
        )

        self._register(
            lesson_id="phy_04_two_bulb_closed",
            title="Comparing Series States: Two Lit Bulbs",
            difficulty="advanced",
            description="Inspect two lit bulbs in series and verify qualitative state changes when the switch opens.",
            learning_objectives=[
                "Compare closed vs open states in a two-bulb series loop.",
                "Recognize qualitative scope limits (no voltage/current inference).",
            ],
            prerequisites=["phy_03_two_bulb_open"],
            estimated_duration="6 min",
            supported_actions=["toggle_switch", "reset_experiment"],
            explanations=[
                "Both bulbs are ON while Switch S1 is closed.",
                "Opening Switch S1 turns both Bulb L1 and Bulb L2 OFF simultaneously.",
            ],
            diagram=_make_physics_diagram(
                diagram_id="phy_two_bulb_closed",
                title="Two-Bulb Series Circuit (Closed)",
                switch_state="closed",
                two_bulbs=True,
            ),
            step_hint="circuit component",
        )

        # =========================
        # BIOLOGY (4 lessons)
        # =========================
        self._register(
            lesson_id="bio_01_simple_chain",
            title="Simple Three-Step Food Chain",
            difficulty="beginner",
            description="Follow energy arrows from Grass to Deer to Wolf in a linear food chain.",
            learning_objectives=[
                "Read directed feeding arrows from food/prey to consumer/predator.",
                "Identify which direct links disappear when a middle organism is removed.",
            ],
            prerequisites=[],
            estimated_duration="4 min",
            supported_actions=["remove_organism", "reset_experiment"],
            explanations=[
                "Arrows point from food to consumer: Grass -> Deer -> Wolf.",
                "Removing Deer removes only its incident feeding edges in the diagram.",
            ],
            diagram=_make_biology_diagram(
                diagram_id="bio_simple_chain",
                title="Simple Woodland Food Chain",
                organisms=[
                    ("grass", "Grass", "Primary producer capturing sunlight."),
                    ("deer", "Deer", "Herbivore that eats grass."),
                    ("wolf", "Wolf", "Predator that feeds on deer."),
                ],
                feeding=[
                    ("grass", "deer", "Grass is eaten by Deer."),
                    ("deer", "wolf", "Deer is eaten by Wolf."),
                ],
            ),
            step_hint="organism",
        )

        bio_base = self._fixture_repo.get_example("biology_food_web")
        assert bio_base is not None
        self._register(
            lesson_id="bio_02_grassland_web",
            title="Grassland Food Web",
            difficulty="beginner",
            description="Navigate branching feeding paths in a grassland ecosystem with multiple consumers.",
            learning_objectives=[
                "Compare direct predators and prey of the Rabbit.",
                "Test removing an organism and inspect exact affected relationships.",
            ],
            prerequisites=["bio_01_simple_chain"],
            estimated_duration="5 min",
            supported_actions=["remove_organism", "reset_experiment"],
            explanations=[
                "Grass feeds both Rabbit and Mouse in this grassland web.",
                "Removing an organism removes only that node and its directly connected edges.",
            ],
            diagram=bio_base,
            step_hint="organism",
        )

        self._register(
            lesson_id="bio_03_forest_web",
            title="Temperate Forest Food Web",
            difficulty="intermediate",
            description="Trace multi-step energy paths from Oak Acorns through squirrels, beetles, robins, foxes, and owls.",
            learning_objectives=[
                "Identify multiple consumers sharing a single producer.",
                "Distinguish direct feeding links from indirect downstream consumers.",
            ],
            prerequisites=["bio_02_grassland_web"],
            estimated_duration="6 min",
            supported_actions=["remove_organism", "reset_experiment"],
            explanations=[
                "Oak Acorn supplies energy to both Squirrel and Beetle.",
                "Owl receives energy from both Squirrel and Robin.",
            ],
            diagram=_make_biology_diagram(
                diagram_id="bio_forest_web",
                title="Temperate Forest Food Web",
                organisms=[
                    ("acorn", "Oak Acorn", "Tree seed serving as a primary food source."),
                    ("squirrel", "Squirrel", "Small mammal feeding on oak acorns."),
                    ("beetle", "Beetle", "Insect feeding on oak acorns."),
                    ("robin", "Robin", "Songbird that eats beetles."),
                    ("fox", "Red Fox", "Predator that hunts squirrels."),
                    ("owl", "Barn Owl", "Nocturnal predator hunting squirrels and robins."),
                ],
                feeding=[
                    ("acorn", "squirrel", "Oak Acorn is eaten by Squirrel."),
                    ("acorn", "beetle", "Oak Acorn is eaten by Beetle."),
                    ("beetle", "robin", "Beetle is eaten by Robin."),
                    ("squirrel", "fox", "Squirrel is eaten by Red Fox."),
                    ("squirrel", "owl", "Squirrel is eaten by Barn Owl."),
                    ("robin", "owl", "Robin is eaten by Barn Owl."),
                ],
            ),
            step_hint="organism",
        )

        self._register(
            lesson_id="bio_04_pond_web",
            title="Freshwater Pond Ecosystem Food Web",
            difficulty="advanced",
            description="Inspect a freshwater pond web with Algae, Tadpoles, Minnows, Frogs, Bass, and Herons.",
            learning_objectives=[
                "Trace converging food web paths reaching an apex predator (Heron).",
                "Avoid over-claiming extinction or population changes from structural removal.",
            ],
            prerequisites=["bio_03_forest_web"],
            estimated_duration="6 min",
            supported_actions=["remove_organism", "reset_experiment"],
            explanations=[
                "Algae feeds both Tadpole and Minnow.",
                "Heron has three direct prey sources: Frog, Minnow, and Bass.",
            ],
            diagram=_make_biology_diagram(
                diagram_id="bio_pond_web",
                title="Freshwater Pond Food Web",
                organisms=[
                    ("algae", "Algae", "Aquatic producer in sunlit pond water."),
                    ("tadpole", "Tadpole", "Herbivorous amphibian larva eating algae."),
                    ("minnow", "Minnow", "Small fish that feeds on algae."),
                    ("frog", "Frog", "Adult amphibian eating tadpoles."),
                    ("bass", "Largemouth Bass", "Predatory fish that eats minnows."),
                    ("heron", "Great Blue Heron", "Wading bird that eats frogs, minnows, and bass."),
                ],
                feeding=[
                    ("algae", "tadpole", "Algae is eaten by Tadpole."),
                    ("algae", "minnow", "Algae is eaten by Minnow."),
                    ("tadpole", "frog", "Tadpole is eaten by Frog."),
                    ("minnow", "bass", "Minnow is eaten by Largemouth Bass."),
                    ("frog", "heron", "Frog is eaten by Great Blue Heron."),
                    ("minnow", "heron", "Minnow is eaten by Great Blue Heron."),
                    ("bass", "heron", "Largemouth Bass is eaten by Great Blue Heron."),
                ],
            ),
            step_hint="organism",
        )

        # =========================
        # COMPUTER SCIENCE (4 lessons)
        # =========================
        self._register(
            lesson_id="cs_01_sequential",
            title="Sequential Variable Assignment",
            difficulty="beginner",
            description="Step through a straight-line algorithm that reads x, computes y = x + 5, and computes z = y * 2.",
            learning_objectives=[
                "Follow sequential execution from Start to End.",
                "Track how each assignment updates the variable environment.",
            ],
            prerequisites=[],
            estimated_duration="4 min",
            supported_actions=["run_flowchart_trace"],
            explanations=[
                "Sequential blocks execute one after another without branching.",
                "With x = 3, y becomes 8 and z becomes 16.",
            ],
            diagram=_make_flowchart_diagram(
                diagram_id="cs_sequential",
                title="Sequential Assignment Flowchart",
                nodes=[
                    Node(id="start_1", kind="start", label="Start", description="Algorithm entry point."),
                    Node(
                        id="in_x",
                        kind="input",
                        label="Input x",
                        description="Reads integer input x.",
                        attributes={"variable": "x"},
                    ),
                    Node(
                        id="set_y",
                        kind="assignment",
                        label="y = x + 5",
                        description="Adds 5 to x and stores in y.",
                        attributes={"variable": "y", "expression": "x + 5"},
                    ),
                    Node(
                        id="set_z",
                        kind="assignment",
                        label="z = y * 2",
                        description="Doubles y and stores in z.",
                        attributes={"variable": "z", "expression": "y * 2"},
                    ),
                    Node(id="end_1", kind="end", label="End", description="Terminates algorithm."),
                ],
                edges=[
                    Edge(id="f1", source="start_1", target="in_x", relation="flow", description="Start to Input x."),
                    Edge(id="f2", source="in_x", target="set_y", relation="flow", description="Input x to y = x + 5."),
                    Edge(id="f3", source="set_y", target="set_z", relation="flow", description="y = x + 5 to z = y * 2."),
                    Edge(id="f4", source="set_z", target="end_1", relation="flow", description="z = y * 2 to End."),
                ],
                default_inputs={"x": 3},
            ),
            step_hint="flowchart block",
        )

        self._register(
            lesson_id="cs_02_conditional_branch",
            title="Conditional Branching (Pass / Retry)",
            difficulty="beginner",
            description="Inspect a True/False decision block that compares score >= 60.",
            learning_objectives=[
                "Evaluate a boolean comparison in a decision block.",
                "Follow the True or False branch to the resulting assignment.",
            ],
            prerequisites=["cs_01_sequential"],
            estimated_duration="5 min",
            supported_actions=["run_flowchart_trace"],
            explanations=[
                "When score >= 60 is True, passed becomes True; otherwise passed becomes False.",
            ],
            diagram=_make_flowchart_diagram(
                diagram_id="cs_conditional",
                title="Score Threshold Decision Flowchart",
                nodes=[
                    Node(id="start_1", kind="start", label="Start", description="Entry point."),
                    Node(
                        id="in_score",
                        kind="input",
                        label="Input score",
                        description="Reads integer test score.",
                        attributes={"variable": "score"},
                    ),
                    Node(
                        id="dec_pass",
                        kind="decision",
                        label="Is score >= 60?",
                        description="Checks whether score meets passing threshold.",
                        attributes={"condition": "score >= 60"},
                    ),
                    Node(
                        id="set_pass",
                        kind="assignment",
                        label="passed = True",
                        description="Marks score as passing.",
                        attributes={"variable": "passed", "expression": "True"},
                    ),
                    Node(
                        id="set_retry",
                        kind="assignment",
                        label="passed = False",
                        description="Marks score as needing retry.",
                        attributes={"variable": "passed", "expression": "False"},
                    ),
                    Node(id="end_1", kind="end", label="End", description="Terminates algorithm."),
                ],
                edges=[
                    Edge(id="f1", source="start_1", target="in_score", relation="flow", description="Start to Input score."),
                    Edge(id="f2", source="in_score", target="dec_pass", relation="flow", description="Input score to decision."),
                    Edge(id="f3", source="dec_pass", target="set_pass", relation="branch_true", description="True branch sets passed = True."),
                    Edge(id="f4", source="dec_pass", target="set_retry", relation="branch_false", description="False branch sets passed = False."),
                    Edge(id="f5", source="set_pass", target="end_1", relation="flow", description="Passed to End."),
                    Edge(id="f6", source="set_retry", target="end_1", relation="flow", description="Retry to End."),
                ],
                default_inputs={"score": 75},
            ),
            step_hint="flowchart block",
        )

        self._register(
            lesson_id="cs_03_even_odd",
            title="Even or Odd Modulo Check",
            difficulty="intermediate",
            description="Use the remainder operator (n % 2 == 0) to classify an integer as even or odd.",
            learning_objectives=[
                "Trace a modulo expression (n % 2 == 0) safely.",
                "Predict which branch executes for an odd vs even input.",
            ],
            prerequisites=["cs_02_conditional_branch"],
            estimated_duration="5 min",
            supported_actions=["run_flowchart_trace"],
            explanations=[
                "For n = 7, 7 % 2 equals 1 (not 0), so the False branch sets is_even = False.",
            ],
            diagram=_make_flowchart_diagram(
                diagram_id="cs_even_odd",
                title="Even or Odd Check Flowchart",
                nodes=[
                    Node(id="start_1", kind="start", label="Start", description="Entry point."),
                    Node(
                        id="in_n",
                        kind="input",
                        label="Input n",
                        description="Reads integer n.",
                        attributes={"variable": "n"},
                    ),
                    Node(
                        id="dec_even",
                        kind="decision",
                        label="Is n % 2 == 0?",
                        description="Checks whether n leaves remainder 0 when divided by 2.",
                        attributes={"condition": "n % 2 == 0"},
                    ),
                    Node(
                        id="set_even",
                        kind="assignment",
                        label="is_even = True",
                        description="Records that n is even.",
                        attributes={"variable": "is_even", "expression": "True"},
                    ),
                    Node(
                        id="set_odd",
                        kind="assignment",
                        label="is_even = False",
                        description="Records that n is odd.",
                        attributes={"variable": "is_even", "expression": "False"},
                    ),
                    Node(id="end_1", kind="end", label="End", description="Terminates algorithm."),
                ],
                edges=[
                    Edge(id="f1", source="start_1", target="in_n", relation="flow", description="Start to Input n."),
                    Edge(id="f2", source="in_n", target="dec_even", relation="flow", description="Input n to modulo check."),
                    Edge(id="f3", source="dec_even", target="set_even", relation="branch_true", description="True branch sets is_even = True."),
                    Edge(id="f4", source="dec_even", target="set_odd", relation="branch_false", description="False branch sets is_even = False."),
                    Edge(id="f5", source="set_even", target="end_1", relation="flow", description="Even to End."),
                    Edge(id="f6", source="set_odd", target="end_1", relation="flow", description="Odd to End."),
                ],
                default_inputs={"n": 7},
            ),
            step_hint="flowchart block",
        )

        cs_base = self._fixture_repo.get_example("cs_flowchart")
        assert cs_base is not None
        self._register(
            lesson_id="cs_04_bounded_loop",
            title="Bounded Loop & Running Sum Trace",
            difficulty="advanced",
            description="Trace a finite loop that accumulates total = total + n while n > 0.",
            learning_objectives=[
                "Follow repeated loop iterations safely with a bounded step guard.",
                "Predict the final accumulated total after the loop terminates.",
            ],
            prerequisites=["cs_03_even_odd"],
            estimated_duration="6 min",
            supported_actions=["run_flowchart_trace"],
            explanations=[
                "Each iteration adds n to total and decrements n until n > 0 becomes False.",
            ],
            diagram=cs_base,
            step_hint="flowchart block",
        )

        # =========================
        # MATHEMATICS (4 lessons)
        # =========================
        self._register(
            lesson_id="math_01_linear_increase",
            title="Monotonic Increasing Linear Function",
            difficulty="beginner",
            description="Explore a strictly increasing linear plot y = 2x from x = 0 to x = 4.",
            learning_objectives=[
                "Read ordered (x, y) coordinates and axis units.",
                "Recognize a strictly increasing trend across all intervals.",
            ],
            prerequisites=[],
            estimated_duration="4 min",
            supported_actions=["analyze_math_plot", "sonify_plot"],
            explanations=[
                "Every step increases y by +2 m as x increases by +1 s.",
                "The exact y-intercept and x-intercept both occur at (0, 0).",
            ],
            diagram=_make_math_diagram(
                diagram_id="math_linear_inc",
                title="Distance vs. Time (Constant Speed)",
                x_label="Time",
                x_unit="s",
                y_label="Distance",
                y_unit="m",
                function_label="y = 2x",
                raw_points=[
                    (0, 0, "Start at Time = 0 s, Distance = 0 m."),
                    (1, 2, "At Time = 1 s, Distance = 2 m."),
                    (2, 4, "At Time = 2 s, Distance = 4 m."),
                    (3, 6, "At Time = 3 s, Distance = 6 m."),
                    (4, 8, "End at Time = 4 s, Distance = 8 m."),
                ],
            ),
            step_hint="data point",
        )

        math_base = self._fixture_repo.get_example("math_plot")
        assert math_base is not None
        self._register(
            lesson_id="math_02_peak_extrema",
            title="Finding a Local Maximum (Projectile Height)",
            difficulty="beginner",
            description="Inspect a parabolic height curve y = -x^2 + 4x that rises to a peak and falls back to zero.",
            learning_objectives=[
                "Locate the exact maximum data point on a plot.",
                "Identify where the trend switches from increasing to decreasing.",
            ],
            prerequisites=["math_01_linear_increase"],
            estimated_duration="5 min",
            supported_actions=["analyze_math_plot", "sonify_plot"],
            explanations=[
                "Height rises from 0 m to a peak of 4 m at Time = 2 s, then decreases to 0 m at 4 s.",
            ],
            diagram=math_base,
            step_hint="data point",
        )

        self._register(
            lesson_id="math_03_valley_minimum",
            title="Local Minimum & Sign-Change Intercepts",
            difficulty="intermediate",
            description="Explore a valley curve that drops below zero to a minimum at (2, -4) and rises back above zero.",
            learning_objectives=[
                "Identify an exact local minimum from finite data points.",
                "Distinguish exact intercepts from interpolated crossings.",
            ],
            prerequisites=["math_02_peak_extrema"],
            estimated_duration="5 min",
            supported_actions=["analyze_math_plot", "sonify_plot"],
            explanations=[
                "The curve decreases to its minimum of -4 m at x = 2 m, then increases.",
            ],
            diagram=_make_math_diagram(
                diagram_id="math_valley_min",
                title="Valley Elevation Profile",
                x_label="Horizontal Distance",
                x_unit="m",
                y_label="Elevation",
                y_unit="m",
                function_label="y = (x - 2)^2 - 4",
                raw_points=[
                    (0, 0, "Left rim at x = 0 m, Elevation = 0 m."),
                    (1, -3, "Descending slope at x = 1 m, Elevation = -3 m."),
                    (2, -4, "Valley floor minimum at x = 2 m, Elevation = -4 m."),
                    (3, -3, "Ascending slope at x = 3 m, Elevation = -3 m."),
                    (4, 0, "Right rim at x = 4 m, Elevation = 0 m."),
                ],
            ),
            step_hint="data point",
        )

        self._register(
            lesson_id="math_04_cooling_comparison",
            title="Decreasing Trend & Flat Plateau",
            difficulty="advanced",
            description="Compare rapid temperature decrease followed by a constant room-temperature plateau.",
            learning_objectives=[
                "Compare rates of change across adjacent intervals.",
                "Recognize a constant (zero-change) plateau interval.",
            ],
            prerequisites=["math_03_valley_minimum"],
            estimated_duration="6 min",
            supported_actions=["analyze_math_plot", "sonify_plot"],
            explanations=[
                "Temperature falls from 80 C to 25 C between 0 and 3 min, then stays constant at 25 C.",
            ],
            diagram=_make_math_diagram(
                diagram_id="math_cooling_curve",
                title="Water Cooling Curve",
                x_label="Time",
                x_unit="min",
                y_label="Temperature",
                y_unit="C",
                function_label="Measured cooling dataset",
                raw_points=[
                    (0, 80, "Initial hot water at 0 min, 80 C."),
                    (1, 55, "Rapid cooling at 1 min, 55 C."),
                    (2, 35, "Slower cooling at 2 min, 35 C."),
                    (3, 25, "Reached room temperature at 3 min, 25 C."),
                    (4, 25, "Constant plateau at 4 min, 25 C."),
                ],
            ),
            step_hint="data point",
        )

        # =========================
        # CHEMISTRY (4 lessons — all validated by safe SMILES parser)
        # =========================
        self._register(
            lesson_id="chem_01_water",
            title="Water Molecule (H2O)",
            difficulty="beginner",
            description="Inspect a water molecule built from validated SMILES 'O' with 1 Oxygen and 2 Hydrogen atoms.",
            learning_objectives=[
                "Count atoms by element in H2O.",
                "Verify Oxygen forms two single covalent bonds to Hydrogen.",
            ],
            prerequisites=[],
            estimated_duration="4 min",
            supported_actions=["inspect_molecule"],
            explanations=[
                "Water (H2O) has 1 Oxygen atom bonded to 2 Hydrogen atoms via single bonds.",
            ],
            diagram=_make_chemistry_diagram(
                diagram_id="chem_water",
                title="Water (H2O)",
                smiles="O",
            ),
            step_hint="atom",
        )

        self._register(
            lesson_id="chem_02_methane",
            title="Methane Molecule (CH4)",
            difficulty="beginner",
            description="Explore Methane (SMILES 'C') where one central Carbon forms four single bonds to Hydrogen.",
            learning_objectives=[
                "Verify Carbon's standard valence of 4 using single bonds.",
                "Identify all direct neighbors of the central Carbon atom.",
            ],
            prerequisites=["chem_01_water"],
            estimated_duration="4 min",
            supported_actions=["inspect_molecule"],
            explanations=[
                "Methane (CH4) has 1 Carbon atom forming 4 single bonds to 4 Hydrogen atoms.",
            ],
            diagram=_make_chemistry_diagram(
                diagram_id="chem_methane",
                title="Methane (CH4)",
                smiles="C",
            ),
            step_hint="atom",
        )

        self._register(
            lesson_id="chem_03_co2",
            title="Carbon Dioxide (CO2 — Double Bonds)",
            difficulty="intermediate",
            description="Inspect Carbon Dioxide (SMILES 'O=C=O') to explore double covalent bonds.",
            learning_objectives=[
                "Distinguish double bonds (order 2) from single bonds (order 1).",
                "Verify Carbon achieves valence 4 via two double bonds.",
            ],
            prerequisites=["chem_02_methane"],
            estimated_duration="5 min",
            supported_actions=["inspect_molecule"],
            explanations=[
                "Carbon Dioxide (CO2) has 1 Carbon atom connected to 2 Oxygen atoms by double bonds.",
            ],
            diagram=_make_chemistry_diagram(
                diagram_id="chem_co2",
                title="Carbon Dioxide (CO2)",
                smiles="O=C=O",
            ),
            step_hint="atom",
        )

        chem_base = self._fixture_repo.get_example("chemistry_molecule")
        assert chem_base is not None
        self._register(
            lesson_id="chem_04_ethanol",
            title="Ethanol Molecule (C2H6O)",
            difficulty="advanced",
            description="Trace a multi-atom covalent chain (C-C-O) with bonded Hydrogen atoms in Ethanol.",
            learning_objectives=[
                "Follow a covalent bond path across Carbon and Oxygen atoms.",
                "Count atoms and bond orders without inferring toxicity or lab safety.",
            ],
            prerequisites=["chem_03_co2"],
            estimated_duration="6 min",
            supported_actions=["inspect_molecule"],
            explanations=[
                "Ethanol (C2H6O) contains 2 Carbon, 6 Hydrogen, and 1 Oxygen atom joined by single covalent bonds.",
            ],
            diagram=chem_base,
            step_hint="atom",
        )

    def list_lessons(
        self,
        *,
        domain: str | None = None,
        difficulty: str | None = None,
        query: str | None = None,
        enabled_domains: set[str] | None = None,
    ) -> list[LessonMetadata]:
        results: list[LessonMetadata] = []
        q = (query or "").strip().lower()
        for meta, _ in self._lessons.values():
            if enabled_domains is not None and meta.domain not in enabled_domains:
                continue
            if domain and meta.domain != domain:
                continue
            if difficulty and meta.difficulty != difficulty:
                continue
            if q:
                haystack = " ".join(
                    [meta.title, meta.description, meta.domain, *meta.learning_objectives]
                ).lower()
                if q not in haystack:
                    continue
            results.append(meta.model_copy(deep=True))
        return results

    def get_lesson(self, lesson_id: str) -> LessonDetailResponse | None:
        item = self._lessons.get(lesson_id)
        if item is None:
            return None
        meta, diagram = item
        return LessonDetailResponse(
            lesson=meta.model_copy(deep=True),
            diagram=diagram.model_copy(deep=True),
        )

    @staticmethod
    def validate_lesson_package(
        payload: LessonPackagePayload,
    ) -> LessonPackageValidationResponse:
        errors: list[str] = []
        warnings: list[str] = []

        if payload.diagram.review_status != "confirmed":
            errors.append(
                "Unreviewed AI diagrams cannot be published or imported as verified lessons. "
                "Confirm the diagram in Educator Review first."
            )
        if payload.lesson.review_status != "confirmed":
            errors.append("Lesson package review_status must be 'confirmed'.")
        if payload.lesson.domain != payload.diagram.domain:
            errors.append(
                f"Lesson domain '{payload.lesson.domain}' does not match diagram domain '{payload.diagram.domain}'."
            )
        if payload.lesson.diagram_id != payload.diagram.id:
            warnings.append(
                "Lesson diagram_id was synchronized with diagram.id during package validation."
            )

        diag_validation = validate_diagram(payload.diagram)
        errors.extend(diag_validation.errors)
        warnings.extend(diag_validation.warnings)
        if not diag_validation.simulation_ready:
            errors.append("Diagram must be simulation_ready before packaging as a lesson.")

        if errors:
            return LessonPackageValidationResponse(
                valid=False,
                errors=errors,
                warnings=warnings,
            )

        clean_lesson = payload.lesson.model_copy(deep=True)
        clean_lesson.diagram_id = payload.diagram.id
        clean_diagram = payload.diagram.model_copy(deep=True)
        return LessonPackageValidationResponse(
            valid=True,
            errors=[],
            warnings=warnings,
            lesson=clean_lesson,
            diagram=clean_diagram,
        )
