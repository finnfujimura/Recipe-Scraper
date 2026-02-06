from recipe_scrapers import scrape_me
from typing import Dict, List, Tuple
import logging
import re
import json
from html import unescape
from collections import OrderedDict
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GENERIC_STEP_TITLE_RE = re.compile(r"^step\s+\d+$", re.IGNORECASE)
HEADING_PREFIX_RE = re.compile(
    r"^([A-Z][A-Za-z&'/-]*(?:\s+[A-Za-z&'/-]+){0,5})\s+([A-Z].+)$"
)
STEP_HEADING_RE = re.compile(r"^Step\s+(\d+)(?::\s*(.*))?$", re.IGNORECASE)
INVALID_SECTION_RE = re.compile(r"^(step\s*\d+|add)$", re.IGNORECASE)

BUN_RIEU_SECTION_ORDER = [
    "Broth",
    "Crab Meatball (Rieu)",
    "Noodles",
    "Toppings",
    "Garnishes",
    "For Serving / Other",
]

INSTAGRAM_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    )
}
INSTAGRAM_HEADERS_MOBILE = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/17.0 Mobile/15E148 Safari/604.1"
    )
}

INSTAGRAM_CONTENT_PATH_RE = re.compile(r"/(p|reel|reels|tv)/([A-Za-z0-9_-]+)", re.IGNORECASE)

INGREDIENT_SECTION_RE = re.compile(r"^(ingredients?|what you need)\s*:?\s*$", re.IGNORECASE)
INSTRUCTION_SECTION_RE = re.compile(
    r"^(instructions?|method|directions?|steps?)\s*:?\s*$",
    re.IGNORECASE,
)
GENERIC_SECTION_RE = re.compile(r"^[A-Za-z][A-Za-z0-9 '&/()-]{1,40}:\s*$")
MEASUREMENT_RE = re.compile(
    r"^(\d+([./]\d+)?|\d+\s+\d/\d|\d/\d)\s*"
    r"(cup|cups|tbsp|tsp|teaspoon|teaspoons|tablespoon|tablespoons|"
    r"oz|ounce|ounces|g|gram|grams|kg|lb|lbs|ml|l)\b",
    re.IGNORECASE,
)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def _split_embedded_heading(text: str) -> Tuple[str | None, str]:
    cleaned = _clean_text(text)
    match = HEADING_PREFIX_RE.match(cleaned)
    if not match:
        return None, cleaned
    heading, remainder = match.groups()
    if len(heading.split()) <= 6 and len(remainder) >= 15:
        return heading.strip(), remainder.strip()
    return None, cleaned


def _looks_like_heading(text: str) -> bool:
    stripped = _clean_text(text)
    if not stripped:
        return False
    if len(stripped) > 65:
        return False
    if any(p in stripped for p in ".!?"):
        return False
    if stripped.lower().startswith("http"):
        return False
    words = stripped.split()
    return 1 <= len(words) <= 8


def _looks_like_body(text: str) -> bool:
    stripped = _clean_text(text)
    if not stripped:
        return False
    return len(stripped) >= 35 or any(p in stripped for p in ".!?")


def _extract_instruction_steps(scraper) -> List[Dict[str, str]]:
    try:
        raw_steps = [_clean_text(str(item)) for item in (scraper.instructions_list() or [])]
    except Exception:
        raw_steps = []

    raw_steps = [item for item in raw_steps if item]
    steps: List[Dict[str, str]] = []
    index = 0
    while index < len(raw_steps):
        current = raw_steps[index]

        # Pattern: "Step 2: Make the sauce"
        explicit_step_match = STEP_HEADING_RE.match(current)
        if explicit_step_match:
            title = (explicit_step_match.group(2) or "").strip()
            body = ""
            if index + 1 < len(raw_steps) and _looks_like_body(raw_steps[index + 1]):
                body = raw_steps[index + 1]
                index += 1
            steps.append({"title": title, "text": body})
            index += 1
            continue

        # Pattern from some sites: heading line followed by body line.
        if (
            _looks_like_heading(current)
            and index + 1 < len(raw_steps)
            and _looks_like_body(raw_steps[index + 1])
        ):
            steps.append({"title": current, "text": raw_steps[index + 1]})
            index += 2
            continue

        heading, body = _split_embedded_heading(current)
        steps.append({"title": heading or "", "text": body})
        index += 1

    return steps


def _format_instructions(steps: List[Dict[str, str]], fallback: str) -> str:
    if not steps:
        return fallback

    formatted_steps: List[str] = []
    for index, step in enumerate(steps, start=1):
        title = (step.get("title") or "").strip()
        text = _clean_text(step.get("text", ""))

        if title and not GENERIC_STEP_TITLE_RE.match(title):
            header = f"Step {index}: {title}"
        else:
            header = f"Step {index}"

        if text:
            formatted_steps.append(f"{header}\n{text}")
        else:
            formatted_steps.append(header)

    return "\n\n".join(formatted_steps)


def _canonical_section_name(section: str | None) -> str | None:
    if section is None:
        return None

    normalized = _clean_text(section).rstrip(":").strip()
    lowered = normalized.lower()
    if not lowered:
        return None
    if INVALID_SECTION_RE.match(lowered):
        return None

    section_aliases = {
        "broth": "Broth",
        "finish broth": "Broth",
        "rieu/meatballs": "Crab Meatball (Rieu)",
        "rieu / meatballs": "Crab Meatball (Rieu)",
        "rieu": "Crab Meatball (Rieu)",
        "crab meatball": "Crab Meatball (Rieu)",
        "crab meatballs": "Crab Meatball (Rieu)",
        "crab meatball (rieu)": "Crab Meatball (Rieu)",
        "meatball": "Crab Meatball (Rieu)",
        "meatballs": "Crab Meatball (Rieu)",
        "noodle": "Noodles",
        "noodles": "Noodles",
        "topping": "Toppings",
        "toppings": "Toppings",
        "garnish": "Garnishes",
        "garnishes": "Garnishes",
        "ingredients": "Ingredients",
        "for serving": "For Serving / Other",
        "for serving / other": "For Serving / Other",
    }
    return section_aliases.get(lowered, normalized)


def _merge_grouped_sections(grouped: List[Dict[str, List[str]]]) -> List[Dict[str, List[str]]]:
    if not grouped:
        return []

    merged: "OrderedDict[str, List[str]]" = OrderedDict()
    last_valid_section = "Ingredients"

    for group in grouped:
        raw_section = group.get("section") if isinstance(group, dict) else None
        section = _canonical_section_name(raw_section)
        items = []
        raw_items = group.get("items", []) if isinstance(group, dict) else []
        for item in raw_items:
            cleaned = _clean_text(str(item))
            if cleaned:
                items.append(cleaned)

        if not items:
            continue
        if section is None:
            section = last_valid_section
        else:
            last_valid_section = section
        if section not in merged:
            merged[section] = []
        merged[section].extend(items)

    return [{"section": section, "items": items} for section, items in merged.items() if items]


def _looks_like_bun_rieu(grouped: List[Dict[str, List[str]]]) -> bool:
    haystack = " ".join(
        item.lower()
        for group in grouped
        for item in group.get("items", [])
    )
    markers = [
        "bun rieu",
        "bún riêu",
        "mam ruoc",
        "mắm ruốc",
        "crab paste with soya oil",
        "fermented shrimp paste",
    ]
    return any(marker in haystack for marker in markers)


def _contains_any(text: str, phrases: List[str]) -> bool:
    return any(phrase in text for phrase in phrases)


def _classify_bun_rieu_item(
    item: str, current_section: str, counts: Dict[str, int]
) -> str:
    text = item.lower()

    topping_terms = [
        "fried vietnamese ham",
        "cha chien",
        "tofu puffs",
        "green leaf lettuce",
        "banana blossom",
        "beansprouts",
    ]
    garnish_terms = [
        "cilantro",
        "green onions",
        "vietnamese perilla",
        "limes",
        "thai chili",
        "fermented shrimp paste",
    ]
    broth_terms = [
        "water",
        "pork ribs",
        "dried shrimp",
        "yellow onion",
        "bun rieu seasoning",
        "bún riêu seasoning",
        "rock sugar",
        "msg",
        "mam ruoc",
        "mắm ruốc",
        "roma tomatoes",
        "tomato",
        "salt to taste",
    ]
    meatball_terms = [
        "ground pork",
        "jumbo lump crab meat",
        "salt and pepper",
    ]

    if _contains_any(text, topping_terms):
        return "Toppings"
    if "vermicelli noodles" in text or "vermicelli noodle" in text:
        return "Noodles"
    if _contains_any(text, meatball_terms) or re.search(r"\beggs?\b", text):
        return "Crab Meatball (Rieu)"
    if re.match(r"^1\s*tbsp\b.*fish sauce", text):
        return "Crab Meatball (Rieu)"
    if "crab paste with soya oil" in text:
        if current_section == "Noodles":
            return "Crab Meatball (Rieu)"
        if current_section in {"Broth", "Crab Meatball (Rieu)"}:
            return current_section
        if counts.get("Crab Meatball (Rieu)", 0) == 0:
            return "Crab Meatball (Rieu)"
        return "Broth"
    if "mam ruoc" in text or "mắm ruốc" in text:
        return "Broth"
    if _contains_any(text, garnish_terms):
        return "Garnishes"
    if _contains_any(text, broth_terms):
        return "Broth"
    if current_section in BUN_RIEU_SECTION_ORDER:
        return current_section
    return "For Serving / Other"


def _rebalance_bun_rieu_groups(grouped: List[Dict[str, List[str]]]) -> List[Dict[str, List[str]]]:
    buckets: "OrderedDict[str, List[str]]" = OrderedDict(
        (section, []) for section in BUN_RIEU_SECTION_ORDER
    )
    counts: Dict[str, int] = {}

    for group in grouped:
        current_section = _canonical_section_name(group.get("section")) or "Ingredients"
        for item in group.get("items", []):
            target = _classify_bun_rieu_item(item, current_section, counts)
            if target not in buckets:
                buckets[target] = []
            buckets[target].append(item)
            counts[target] = counts.get(target, 0) + 1

    return [{"section": section, "items": items} for section, items in buckets.items() if items]


def _post_process_grouped_ingredients(grouped: List[Dict[str, List[str]]]) -> List[Dict[str, List[str]]]:
    merged = _merge_grouped_sections(grouped)
    if not merged:
        return []
    if _looks_like_bun_rieu(merged):
        return _rebalance_bun_rieu_groups(merged)
    return merged


def _extract_grouped_ingredients(scraper, steps: List[Dict[str, str]]) -> List[Dict[str, List[str]]]:
    try:
        raw_groups = scraper.ingredient_groups() or []
    except Exception:
        raw_groups = []

    grouped: List[Dict[str, List[str]]] = []
    for index, group in enumerate(raw_groups):
        items = []
        purpose = None
        if hasattr(group, "ingredients"):
            items = [item for item in (group.ingredients or []) if item]
            purpose = getattr(group, "purpose", None)
        elif isinstance(group, dict):
            items = [item for item in (group.get("ingredients") or []) if item]
            purpose = group.get("purpose")

        if not items:
            continue

        section = (purpose or "").strip() or (
            "Ingredients" if len(raw_groups) == 1 else f"Section {index + 1}"
        )
        grouped.append({"section": section, "items": items})

    candidate_groups = grouped

    # If upstream did not provide meaningful grouping, infer groups from step usage.
    if not grouped or (len(grouped) == 1 and grouped[0]["section"] == "Ingredients"):
        flat_ingredients = scraper.ingredients() or []
        inferred = _infer_groups_from_steps(flat_ingredients, steps)
        if inferred:
            candidate_groups = inferred
        else:
            candidate_groups = [{"section": "Ingredients", "items": flat_ingredients}]

    return _post_process_grouped_ingredients(candidate_groups)


def _normalize_ingredient_name(ingredient: str) -> str:
    head = ingredient.split(",", 1)[0].lower().strip()
    head = re.sub(r"[^a-z0-9\s]", " ", head)
    head = re.sub(r"\s+", " ", head).strip()
    return head


def _ingredient_aliases(name: str) -> List[str]:
    aliases = {name}
    substitutions = {
        "mayonnaise": "mayo",
        "greek yogurt": "yogurt",
        "scallions": "green onions",
        "cilantro": "coriander",
    }
    for src, dst in substitutions.items():
        if src in name:
            aliases.add(name.replace(src, dst))
    words = name.split()
    if len(words) > 1:
        aliases.add(" ".join(words[-2:]))
    if words:
        aliases.add(words[-1])
    return [alias for alias in aliases if len(alias) > 2]


def _ingredient_matches_step(ingredient_name: str, step_text: str) -> bool:
    lowered_step = step_text.lower()
    for alias in _ingredient_aliases(ingredient_name):
        pattern = r"\b" + re.escape(alias) + r"\b"
        if re.search(pattern, lowered_step):
            return True
    return False


def _normalize_section_title(title: str) -> str:
    lowered = title.lower()
    if "white sauce" in lowered:
        return "White Sauce"
    if "red sauce" in lowered or "hot sauce" in lowered:
        return "Red Hot Sauce"
    if "rice" in lowered:
        return "Yellow Rice"
    if "chicken" in lowered:
        return "Chicken"
    if "serve" in lowered:
        return "For Serving / Other"
    return title


def _infer_groups_from_steps(
    ingredients: List[str], steps: List[Dict[str, str]]
) -> List[Dict[str, List[str]]]:
    if not ingredients or not steps:
        return []
    if not any((step.get("title") or "").strip() for step in steps):
        return []

    step_groups: "OrderedDict[str, List[str]]" = OrderedDict()
    step_labels: List[str] = []
    for index, step in enumerate(steps, start=1):
        title = (step.get("title") or "").strip()
        label = _normalize_section_title(title if title else f"Step {index}")
        step_labels.append(label)
        if label not in step_groups:
            step_groups[label] = []

    leftovers: List[str] = []
    last_match_by_name: Dict[str, int] = {}
    assigned_labels: List[str | None] = [None] * len(ingredients)

    for ingredient_index, ingredient in enumerate(ingredients):
        normalized_name = _normalize_ingredient_name(str(ingredient))
        matches: List[int] = []
        for idx, step in enumerate(steps):
            step_title = step.get("title", "")
            step_text = f"{step_title} {step.get('text', '')}"
            if _ingredient_matches_step(normalized_name, step_text):
                matches.append(idx)

        if not matches:
            continue

        previous_idx = last_match_by_name.get(normalized_name, -1)
        selected_idx = next((idx for idx in matches if idx > previous_idx), matches[0])
        last_match_by_name[normalized_name] = selected_idx
        assigned_labels[ingredient_index] = step_labels[selected_idx]

    # Fill unmatched ingredients by nearest assigned group in ingredient order.
    for ingredient_index, assigned_label in enumerate(assigned_labels):
        if assigned_label is not None:
            continue

        prev_index = ingredient_index - 1
        while prev_index >= 0 and assigned_labels[prev_index] is None:
            prev_index -= 1
        next_index = ingredient_index + 1
        while next_index < len(assigned_labels) and assigned_labels[next_index] is None:
            next_index += 1

        prev_label = assigned_labels[prev_index] if prev_index >= 0 else None
        next_label = assigned_labels[next_index] if next_index < len(assigned_labels) else None

        chosen_label = None
        if prev_label and next_label:
            if prev_label == next_label:
                chosen_label = prev_label
            else:
                prev_distance = ingredient_index - prev_index
                next_distance = next_index - ingredient_index
                chosen_label = prev_label if prev_distance <= next_distance else next_label
        elif prev_label:
            chosen_label = prev_label
        elif next_label:
            chosen_label = next_label

        assigned_labels[ingredient_index] = chosen_label

    for ingredient, label in zip(ingredients, assigned_labels):
        if label:
            step_groups[label].append(ingredient)
        else:
            leftovers.append(ingredient)

    grouped = [
        {"section": section, "items": items}
        for section, items in step_groups.items()
        if items
    ]

    if leftovers:
        existing_other = next(
            (group for group in grouped if group["section"] == "For Serving / Other"),
            None,
        )
        if existing_other:
            existing_other["items"].extend(leftovers)
        else:
            grouped.append({"section": "For Serving / Other", "items": leftovers})

    # Require at least 2 sections before we consider inference meaningful.
    return grouped if len(grouped) >= 2 else []


def _is_instagram_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
        path = parsed.path or ""
    except Exception:
        return False
    if "instagram.com" not in host and "instagr.am" not in host:
        return False
    return bool(INSTAGRAM_CONTENT_PATH_RE.search(path))


def _is_instagram_host(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = (parsed.netloc or "").lower()
    except Exception:
        return False
    return "instagram.com" in host or "instagr.am" in host


def _normalize_instagram_url(url: str) -> str:
    parsed = urlparse(url)
    raw_path = re.sub(r"/+", "/", parsed.path or "/")
    match = INSTAGRAM_CONTENT_PATH_RE.search(raw_path)
    if match:
        content_type = match.group(1).lower()
        shortcode = match.group(2)
        normalized_path = f"/{content_type}/{shortcode}/"
    else:
        normalized_path = raw_path.rstrip("/") + "/"
    return urlunparse((parsed.scheme or "https", parsed.netloc, normalized_path, "", "", ""))


def _instagram_embed_url(url: str) -> str:
    parsed = urlparse(url)
    base_path = (parsed.path or "/").rstrip("/")
    return urlunparse((parsed.scheme or "https", parsed.netloc, f"{base_path}/embed/captioned/", "", "", ""))


def _instagram_candidate_urls(url: str) -> List[str]:
    normalized = _normalize_instagram_url(url)
    embed_url = _instagram_embed_url(normalized)
    url_with_lang = normalized + "?hl=en"
    embed_with_lang = embed_url + "?hl=en"
    return [normalized, url_with_lang, embed_url, embed_with_lang]


def _extract_meta_content(soup: BeautifulSoup, attr: str, value: str) -> str:
    tag = soup.find("meta", attrs={attr: value})
    if not tag:
        return ""
    return str(tag.get("content", "")).strip()


def _extract_instagram_caption_from_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    og_description = _extract_meta_content(soup, "property", "og:description")
    if og_description:
        match = re.search(r'on Instagram:\s*"(.+?)"', og_description, re.IGNORECASE | re.DOTALL)
        if match:
            return unescape(match.group(1)).strip()
        quoted_match = re.search(r':\s*"(.+?)"\s*$', og_description, re.DOTALL)
        if quoted_match:
            return unescape(quoted_match.group(1)).strip()
        quoted_start_match = re.search(r':\s*"(.+)$', og_description, re.DOTALL)
        if quoted_start_match:
            return unescape(quoted_start_match.group(1)).strip().rstrip('"')
        return unescape(og_description).strip()

    name_description = _extract_meta_content(soup, "name", "description")
    if name_description:
        return unescape(name_description).strip()

    for script_tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script_tag.string or script_tag.text or ""
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        candidates = payload if isinstance(payload, list) else [payload]
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            for field in ("caption", "description", "articleBody"):
                value = candidate.get(field)
                if isinstance(value, str) and value.strip():
                    return unescape(value).strip()

    return ""


def _extract_instagram_image_from_html(html: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    image_url = _extract_meta_content(soup, "property", "og:image")
    return image_url or None


def _normalize_caption_text(caption: str) -> str:
    text = unescape(caption or "")
    text = text.replace("\\n", "\n")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\u200b", "", text)
    return text.strip()


def _clean_caption_line(line: str) -> str:
    cleaned = line.strip()
    cleaned = re.sub(r"^[\-\*\u2022]+\s*", "", cleaned)
    cleaned = re.sub(r"^\d+[\.)]\s*", "", cleaned)
    cleaned = cleaned.strip()
    return cleaned


def _looks_like_ingredient_line(line: str) -> bool:
    if not line:
        return False
    lowered = line.lower()
    if MEASUREMENT_RE.search(line):
        return True
    ingredient_words = [
        "salt",
        "pepper",
        "garlic",
        "onion",
        "oil",
        "sugar",
        "flour",
        "butter",
        "chicken",
        "beef",
        "pork",
        "egg",
        "milk",
        "cream",
        "water",
    ]
    return any(word in lowered for word in ingredient_words) and "," in line


def _parse_ingredient_groups_from_lines(lines: List[str]) -> List[Dict[str, List[str]]]:
    groups: List[Dict[str, List[str]]] = []
    current = {"section": "Ingredients", "items": []}

    for line in lines:
        if not line:
            continue
        if INSTRUCTION_SECTION_RE.match(line):
            break
        if INGREDIENT_SECTION_RE.match(line):
            continue
        if GENERIC_SECTION_RE.match(line) and not _looks_like_ingredient_line(line):
            if current["items"]:
                groups.append(current)
            current = {"section": line.rstrip(":").strip(), "items": []}
            continue
        current["items"].append(line)

    if current["items"]:
        groups.append(current)

    return _post_process_grouped_ingredients(groups)


def _extract_title_from_caption(lines: List[str]) -> str:
    for line in lines:
        lowered = line.lower()
        if INGREDIENT_SECTION_RE.match(line) or INSTRUCTION_SECTION_RE.match(line):
            continue
        if lowered.startswith("#"):
            continue
        title = re.sub(r"\s*#\w+", "", line).strip()
        if title:
            return title[:120]
    return "Instagram Recipe"


def _format_instructions_from_lines(lines: List[str]) -> str:
    if not lines:
        return "No instructions available."

    cleaned_steps = []
    for raw in lines:
        if not raw:
            continue
        if INSTRUCTION_SECTION_RE.match(raw):
            continue
        if INGREDIENT_SECTION_RE.match(raw):
            continue
        cleaned_steps.append(raw)

    if len(cleaned_steps) == 1:
        sentence_steps = [
            item.strip()
            for item in re.split(r"(?<=[.!?])\s+", cleaned_steps[0])
            if item.strip()
        ]
        if len(sentence_steps) > 1:
            cleaned_steps = sentence_steps

    if not cleaned_steps:
        return "No instructions available."

    formatted = []
    for index, step in enumerate(cleaned_steps, start=1):
        formatted.append(f"Step {index}\n{step}")
    return "\n\n".join(formatted)


def _split_caption_into_lines(caption: str) -> List[str]:
    normalized = _normalize_caption_text(caption)
    if not normalized:
        return []

    raw_lines = [_clean_caption_line(line) for line in normalized.split("\n")]
    lines = [line for line in raw_lines if line]

    # If caption is a single long line, split on sentence boundaries as fallback.
    if len(lines) == 1 and len(lines[0]) > 180:
        sentence_lines = [
            _clean_caption_line(part)
            for part in re.split(r"(?<=[.!?])\s+", lines[0])
        ]
        lines = [line for line in sentence_lines if line]

    return lines


def _parse_instagram_caption(caption: str) -> Dict:
    lines = _split_caption_into_lines(caption)
    title = _extract_title_from_caption(lines)

    ingredient_start = next((i for i, line in enumerate(lines) if INGREDIENT_SECTION_RE.match(line)), None)
    instruction_start = next((i for i, line in enumerate(lines) if INSTRUCTION_SECTION_RE.match(line)), None)

    ingredient_lines: List[str] = []
    instruction_lines: List[str] = []

    if ingredient_start is not None:
        end_index = instruction_start if instruction_start is not None and instruction_start > ingredient_start else len(lines)
        ingredient_lines = lines[ingredient_start + 1:end_index]
    else:
        ingredient_lines = [line for line in lines if _looks_like_ingredient_line(line)]

    if instruction_start is not None:
        instruction_lines = lines[instruction_start + 1:]
    else:
        instruction_lines = [
            line for line in lines
            if line not in ingredient_lines and not INGREDIENT_SECTION_RE.match(line)
        ]

    grouped_ingredients = _parse_ingredient_groups_from_lines(ingredient_lines)
    if not grouped_ingredients and ingredient_lines:
        grouped_ingredients = [{"section": "Ingredients", "items": ingredient_lines}]

    instructions = _format_instructions_from_lines(instruction_lines)

    return {
        "title": title,
        "ingredients": grouped_ingredients,
        "instructions": instructions,
    }


def _scrape_instagram_recipe(url: str) -> Dict:
    last_error: Exception | None = None
    caption = ""
    image_url = None

    header_sets = [INSTAGRAM_HEADERS, INSTAGRAM_HEADERS_MOBILE]
    for candidate_url in _instagram_candidate_urls(url):
        for headers in header_sets:
            try:
                response = requests.get(candidate_url, headers=headers, timeout=20)
                response.raise_for_status()
                html = response.text
                found_caption = _extract_instagram_caption_from_html(html)
                if found_caption:
                    caption = found_caption
                    image_url = _extract_instagram_image_from_html(html)
                    break
            except Exception as e:
                last_error = e
                continue
        if caption:
            break

    if not caption:
        if last_error:
            logger.warning(f"Instagram fetch warning for {url}: {last_error}")
        raise Exception("Could not extract caption from Instagram post/reel. Try manual entry.")

    parsed = _parse_instagram_caption(caption)
    recipe_title = parsed.get("title") or "Instagram Recipe"
    return {
        "url": url,
        "title": recipe_title,
        "image_url": image_url,
        "ingredients": parsed.get("ingredients") or [{"section": "Ingredients", "items": []}],
        "instructions": parsed.get("instructions") or "No instructions available.",
        "total_time": None,
        "yields": None,
    }


def scrape_recipe(url: str) -> Dict:
    """
    Scrape recipe data from a URL using recipe-scrapers library

    Args:
        url: The recipe URL to scrape

    Returns:
        Dictionary containing recipe data or an error message

    Raises:
        ValueError: If URL is invalid
    """
    if not url or not url.startswith('http'):
        raise ValueError("Invalid URL provided")

    try:
        is_instagram = _is_instagram_host(url)
        if is_instagram:
            # Try Instagram caption parsing first for post/reel/tv URLs.
            # Some shared URLs can vary, so we also keep a fallback in the
            # exception handler below.
            if _is_instagram_url(url):
                recipe_data = _scrape_instagram_recipe(url)
                logger.info(f"Successfully scraped Instagram recipe: {recipe_data['title']}")
                return recipe_data

        # Use wild_mode to support sites following common patterns
        scraper = scrape_me(url, wild_mode=True)
        instruction_steps = _extract_instruction_steps(scraper)
        grouped_ingredients = _extract_grouped_ingredients(scraper, instruction_steps)
        formatted_instructions = _format_instructions(
            instruction_steps,
            scraper.instructions(),
        )

        # Extract recipe data
        recipe_data = {
            'url': url,
            'title': scraper.title(),
            'image_url': scraper.image() if scraper.image() else None,
            'ingredients': grouped_ingredients,
            'instructions': formatted_instructions,
            'total_time': scraper.total_time() if scraper.total_time() else None,
            'yields': scraper.yields() if scraper.yields() else None,
        }

        logger.info(f"Successfully scraped recipe: {recipe_data['title']}")
        return recipe_data

    except Exception as e:
        if _is_instagram_host(url):
            try:
                recipe_data = _scrape_instagram_recipe(url)
                logger.info(
                    "Successfully scraped Instagram recipe after fallback: "
                    f"{recipe_data['title']}"
                )
                return recipe_data
            except Exception as instagram_error:
                logger.error(
                    "Failed Instagram fallback scrape from %s: %s",
                    url,
                    str(instagram_error),
                )
                return {'url': url, 'error': f"Failed to scrape recipe: {str(instagram_error)}"}

        logger.error(f"Failed to scrape recipe from {url}: {str(e)}")
        return {'url': url, 'error': f"Failed to scrape recipe: {str(e)}"}
