"""Controlled conversational voice command interpreter for SenseGraph (Phase 15).

Design guarantees:
- Pure deterministic intent parser for navigation, subject/lesson selection,
  exploration, and experiment controls. Never executes arbitrary code or
  unrestricted LLM actions.
- Scientific questions are routed strictly to the Evidence-Grounded STEM Tutor
  (`answer_grounded_question`), which validates confirmed diagrams and cites
  exact node/edge IDs.
- Uncertain or unrecognized utterances return `intent='clarify'` with a short,
  accessible clarification prompt rather than guessing.
"""

from __future__ import annotations

import re

from app.domains import DomainSimulationError
from app.models import (
    VoiceInterpretRequest,
    VoiceInterpretResponse,
    VoiceOptionSummary,
)
from app.services.tutor import TutorNarrator, answer_grounded_question

SUBJECT_ALIASES: dict[str, str] = {
    "physics": "physics_circuit",
    "circuit": "physics_circuit",
    "circuits": "physics_circuit",
    "electricity": "physics_circuit",
    "biology": "biology_food_web",
    "food web": "biology_food_web",
    "food chain": "biology_food_web",
    "ecosystem": "biology_food_web",
    "computer science": "cs_flowchart",
    "flowchart": "cs_flowchart",
    "coding": "cs_flowchart",
    "algorithm": "cs_flowchart",
    "cs": "cs_flowchart",
    "math": "math_plot",
    "mathematics": "math_plot",
    "graph": "math_plot",
    "plot": "math_plot",
    "chemistry": "chemistry_molecule",
    "molecule": "chemistry_molecule",
    "molecules": "chemistry_molecule",
    "atoms": "chemistry_molecule",
}

SUBJECT_DISPLAY: dict[str, str] = {
    "physics_circuit": "Physics",
    "biology_food_web": "Biology",
    "cs_flowchart": "Computer Science",
    "math_plot": "Mathematics",
    "chemistry_molecule": "Chemistry",
}

ORDINAL_MAP: dict[str, int] = {
    "one": 0,
    "1": 0,
    "first": 0,
    "a": 0,
    "two": 1,
    "2": 1,
    "second": 1,
    "b": 1,
    "three": 2,
    "3": 2,
    "third": 2,
    "c": 2,
    "four": 3,
    "4": 3,
    "fourth": 3,
    "d": 3,
    "five": 4,
    "5": 4,
    "fifth": 4,
    "e": 4,
}


def _normalize(text: str) -> str:
    cleaned = re.sub(r"[^\w\s?'-]", " ", text.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def _match_subject(norm: str) -> str | None:
    # Check multi-word aliases before single-word aliases.
    for alias in sorted(SUBJECT_ALIASES.keys(), key=len, reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", norm):
            return SUBJECT_ALIASES[alias]
    return None


def _match_option(
    norm: str, options: list[VoiceOptionSummary]
) -> VoiceOptionSummary | None:
    if not options:
        return None

    # 1. Explicit "option one" / "choice 2" / "first option"
    m = re.search(
        r"\b(?:option|choice|number|answer)\s+(one|two|three|four|five|1|2|3|4|5|first|second|third|fourth|fifth|a|b|c|d|e)\b",
        norm,
    )
    if m:
        idx = ORDINAL_MAP.get(m.group(1))
        if idx is not None and 0 <= idx < len(options):
            return options[idx]

    m_ord = re.search(r"\b(first|second|third|fourth|fifth)\s+(?:option|choice|one|answer)\b", norm)
    if m_ord:
        idx = ORDINAL_MAP.get(m_ord.group(1))
        if idx is not None and 0 <= idx < len(options):
            return options[idx]

    # 2. Exact or strong substring/token match against option labels
    best: VoiceOptionSummary | None = None
    best_score = 0
    norm_tokens = set(re.findall(r"[a-z0-9]+", norm))
    stop = {"the", "a", "an", "is", "are", "will", "be", "to", "it", "my", "answer", "i", "think"}
    meaningful_user = norm_tokens - stop

    for opt in options:
        opt_norm = _normalize(opt.label)
        if norm == opt_norm or (len(norm) >= 2 and norm in opt_norm) or opt_norm in norm:
            score = 100 + len(opt_norm)
            if score > best_score:
                best_score = score
                best = opt
            continue

        opt_tokens = set(re.findall(r"[a-z0-9]+", opt_norm)) - stop
        overlap = meaningful_user & opt_tokens
        if overlap:
            score = len(overlap) * 10
            if score > best_score:
                best_score = score
                best = opt

    if best is not None and best_score >= 10:
        return best
    return None


def _looks_like_scientific_question(norm: str) -> bool:
    question_prefixes = (
        "why ",
        "how ",
        "where ",
        "what happens if",
        "what happens when",
        "what is connected",
        "what connects",
        "which ",
        "is the ",
        "are the ",
        "does the ",
        "do the ",
        "can the ",
        "tell me about ",
    )
    if norm.startswith(question_prefixes) or norm.endswith("?"):
        # Exclude pure UI navigation phrases like "what is this?"
        return norm not in {"what is this", "what is this?", "where am i", "where am i?"}
    return False


def interpret_voice_command(
    request: VoiceInterpretRequest,
    narrator: TutorNarrator | None = None,
) -> VoiceInterpretResponse:
    """Interpret a spoken transcript into a verified SenseGraph action or grounded tutor reply."""
    raw = request.transcript.strip()
    norm = _normalize(raw)
    step = (request.step or "welcome").lower()

    if not norm:
        return VoiceInterpretResponse(
            transcript=raw,
            intent="clarify",
            action="clarify",
            spoken_response="I did not catch that. You can say Next, Repeat, Help, or ask a question about the diagram.",
            needs_clarification=True,
            confidence="low",
        )

    # 1. Universal navigation & safety commands
    if re.search(r"\b(stop listening|pause conversation|stop conversation|end conversation|mute)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="stop_guided_voice",
            spoken_response="Guided voice conversation paused. You can continue using the keyboard or press Speak Now anytime.",
        )

    if norm in {"where am i", "where am i?", "what can i do", "what can i do?"}:
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="where_am_i",
            spoken_response="Reading your current location and available choices.",
        )

    if re.search(r"\b(help|what can i say|commands|instructions)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="help",
            spoken_response=(
                "You can say Next, Previous, Repeat, Go back, Start experiment, "
                "or ask a question about the diagram."
            ),
        )

    if re.search(r"\b(repeat|say that again|again please|read again)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="repeat",
            spoken_response="Repeating the current guidance.",
        )

    if re.search(r"\b(go back|back|return)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="go_back",
            spoken_response="Going back to the previous step.",
        )

    if re.search(r"\b(continue learning|resume lesson|continue my lesson|continue)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="continue_learning",
            spoken_response="Continuing your learning session.",
        )

    if re.search(r"\b(start learning|begin learning|start lesson|let us start|lets start)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="start_learning",
            spoken_response=(
                "Welcome! Would you like to explore Physics, Biology, Computer Science, "
                "Mathematics, or Chemistry?"
            ),
        )

    # 2. Difficulty selection (especially on subjects/lessons step)
    for diff in ("beginner", "intermediate", "advanced"):
        if re.search(rf"\b{diff}\b", norm):
            return VoiceInterpretResponse(
                transcript=raw,
                intent="select_difficulty",
                action="select_difficulty",
                parameters={"difficulty": diff},
                spoken_response=f"Filtering for {diff} lessons.",
            )

    # 3. Experiment-specific actions
    if re.search(r"\b(start experiment|do experiment|run experiment|predict|prediction|quiz|test me)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="experiment_action",
            action="start_experiment",
            spoken_response="Opening the prediction and verified experiment step.",
        )

    if re.search(r"\b(submit|submit my answer|check answer|check my answer|run it)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="submit_answer",
            action="submit_answer",
            spoken_response="Submitting your prediction to the verified simulation engine.",
        )

    if re.search(r"\b(try again|retry|reset experiment)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="experiment_action",
            action="try_again",
            spoken_response="Resetting the experiment so you can try again.",
        )

    if re.search(r"\b(next lesson|another lesson)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="next_lesson",
            spoken_response="Moving to the next verified lesson.",
        )

    if re.search(r"\b(close the switch|open the switch|toggle the switch|flip the switch)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="experiment_action",
            action="toggle_switch",
            spoken_response="Toggling the switch using the verified Physics engine.",
        )

    # 4. Option selection during experiment / prediction step
    if step == "experiment" and request.available_options:
        matched_opt = _match_option(norm, request.available_options)
        if matched_opt is not None:
            return VoiceInterpretResponse(
                transcript=raw,
                intent="select_option",
                action="select_option",
                parameters={"option_id": matched_opt.id, "option_label": matched_opt.label},
                spoken_response=(
                    f"Selected: {matched_opt.label}. Say Submit my answer to run the verified experiment."
                ),
            )

    # 5. Exploration commands (before generic scientific questions)
    if norm in {"what is this", "what is this?", "explain this", "explain this component", "describe this"}:
        return VoiceInterpretResponse(
            transcript=raw,
            intent="explore_action",
            action="explain_component",
            spoken_response="Describing the current component.",
        )

    if re.search(r"\b(explain the diagram|overview|describe the diagram|summarize)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="explore_action",
            action="explain_diagram",
            spoken_response="Reading the diagram overview.",
        )

    if re.search(r"\b(tell me more|explain more|more details|details)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="explore_action",
            action="tell_me_more",
            spoken_response="Sharing additional verified details.",
        )

    # 6. Scientific questions routed to Evidence-Grounded Tutor
    if _looks_like_scientific_question(norm) and request.diagram is not None:
        try:
            tutor_reply = answer_grounded_question(
                diagram=request.diagram,
                question=raw,
                response_mode="direct",
                learn_mode=False,
                narrator=narrator,
            )
            return VoiceInterpretResponse(
                transcript=raw,
                intent="tutor_question",
                action="answer_tutor",
                parameters={"abstained": tutor_reply.abstained},
                spoken_response=tutor_reply.answer,
                tutor_response=tutor_reply,
                confidence="high" if not tutor_reply.abstained else "medium",
            )
        except DomainSimulationError as exc:
            return VoiceInterpretResponse(
                transcript=raw,
                intent="clarify",
                action="clarify",
                spoken_response=exc.message,
                needs_clarification=True,
                confidence="low",
            )

    # 7. Subject selection (e.g., "Show Physics lessons", "Open Biology", "Physics")
    subject = _match_subject(norm)
    if subject is not None:
        label = SUBJECT_DISPLAY.get(subject, subject)
        return VoiceInterpretResponse(
            transcript=raw,
            intent="select_subject",
            action="select_subject",
            parameters={"domain": subject, "subject_label": label},
            spoken_response=(
                f"Opening {label} lessons. Would you like a beginner lesson or a specific topic?"
            ),
        )

    # 8. Simple step navigation: Next / Previous / Yes / No
    if re.search(r"\b(next|forward|move on|skip)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="next",
            spoken_response="Moving to the next item.",
        )

    if re.search(r"\b(previous|prev|last one)\b", norm):
        return VoiceInterpretResponse(
            transcript=raw,
            intent="navigate",
            action="previous",
            spoken_response="Moving to the previous item.",
        )

    if norm in {"yes", "yeah", "yep", "sure", "ok", "okay", "please do"}:
        return VoiceInterpretResponse(
            transcript=raw,
            intent="confirm_yes",
            action="confirm_yes",
            spoken_response="Proceeding.",
        )

    if norm in {"no", "nope", "not now", "cancel", "stop"}:
        return VoiceInterpretResponse(
            transcript=raw,
            intent="confirm_no",
            action="confirm_no",
            spoken_response="Okay, staying on the current step.",
        )

    # 9. Fallback: if a confirmed diagram is loaded and user asked an implicit question
    if request.diagram is not None and len(norm.split()) >= 3:
        try:
            tutor_reply = answer_grounded_question(
                diagram=request.diagram,
                question=raw,
                response_mode="direct",
                learn_mode=False,
                narrator=narrator,
            )
            if not tutor_reply.abstained:
                return VoiceInterpretResponse(
                    transcript=raw,
                    intent="tutor_question",
                    action="answer_tutor",
                    parameters={"abstained": False},
                    spoken_response=tutor_reply.answer,
                    tutor_response=tutor_reply,
                    confidence="medium",
                )
        except DomainSimulationError:
            pass

    # 10. Uncertain command -> short clarification
    return VoiceInterpretResponse(
        transcript=raw,
        intent="clarify",
        action="clarify",
        spoken_response=(
            f"I heard '{raw}', but I am not sure what action you want. "
            "You can say Next, Previous, Repeat, Help, a subject name, or ask a question about this diagram."
        ),
        needs_clarification=True,
        confidence="low",
    )
