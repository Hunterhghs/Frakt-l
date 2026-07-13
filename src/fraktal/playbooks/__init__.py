"""Domain playbooks — standards and quality gates for common deliverables.

The Orchestrator's PlaybookTool fetches these to guide sub-agents on
specialized outputs: dashboards, reports, websites, datasets, research.
"""

from pathlib import Path

PLAYBOOKS: dict[str, str] = {
    "dashboard": "Playbook: Interactive Dashboard",
    "report": "Playbook: Professional Report",
    "website": "Playbook: Responsive Website",
    "dataset": "Playbook: Data Pipeline & Dataset",
    "research": "Playbook: Research Synthesis",
    "presentation": "Playbook: Slide Deck",
    "infographic": "Playbook: Infographic",
}

# ── Playbook definitions ────────────────────────────────────────────────────

DASHBOARD_PLAYBOOK = """# Dashboard Playbook — Quality Standards

## Structure
- KPI summary cards at top (4-6 key metrics).
- Main visualization area (chart, map, or table).
- Filter panel (date range, category, region).
- Data table with sortable columns.
- Footer with data sources and last-updated timestamp.

## Quality Gates
1. Responsive — works on mobile, tablet, desktop.
2. Dark mode support — respects system preference.
3. Interactive — filters update all charts simultaneously.
4. Accessible — keyboard navigable, screen-reader labels.
5. Fast — initial load under 3 seconds.
6. Data-inked — every pixel serves the data story.

## Tech Preferences
- HTML/CSS/JS single-file or React with Tailwind.
- Chart.js or D3.js for visualizations.
- No heavy frameworks unless justified.
"""

REPORT_PLAYBOOK = """# Report Playbook — Quality Standards

## Structure
1. Executive Summary (1 page — the most important part).
2. Introduction & Context.
3. Methodology.
4. Findings (with data visualizations).
5. Analysis & Interpretation.
6. Recommendations.
7. Appendices (data tables, sources, methodology details).

## Quality Gates
- Executive summary stands alone — decision-maker reads nothing else.
- Every claim backed by data with source citation.
- Visualizations follow data-ink ratio principles.
- Professional typography and consistent styling.
- PDF-ready with proper page breaks and headers.
"""

WEBSITE_PLAYBOOK = """# Website Playbook — Quality Standards

## Structure
- Hero section with clear value proposition.
- Feature/benefit sections.
- Social proof (testimonials, logos, metrics).
- Call-to-action at every scroll depth.
- Footer with links, contact, legal.

## Quality Gates
1. Responsive — mobile-first design.
2. Accessible — WCAG 2.1 AA minimum.
3. Fast — Lighthouse score 90+.
4. SEO — proper meta tags, semantic HTML.
5. Dark mode — respects system preference.
6. No AI aesthetic — avoid generic gradients, use real design.

## Tech Preferences
- React + Tailwind CSS for interactivity.
- Static site generation for performance.
- Minimal JavaScript — prefer CSS for animations.
"""

DATASET_PLAYBOOK = """# Dataset Playbook — Quality Standards

## Structure
- Clean CSV/Parquet with consistent column naming.
- Data dictionary (column name, type, description, source).
- Summary statistics (row count, date range, coverage).
- Known limitations and gaps documented.
- Version history.

## Quality Gates
- No missing values without documentation.
- Consistent date/number formatting.
- UTF-8 encoding.
- Reproducible pipeline from source to output.
"""

RESEARCH_PLAYBOOK = """# Research Playbook — Quality Standards

## Structure
1. Research Question & Scope.
2. Literature Review.
3. Methodology.
4. Findings.
5. Discussion.
6. Conclusions & Recommendations.
7. References.

## Quality Gates
- Research question is specific and answerable.
- Methods are reproducible.
- Limitations are explicitly stated.
- Conclusions are proportional to evidence strength.
- All sources cited with DOIs where available.
"""

PRESENTATION_PLAYBOOK = """# Presentation Playbook — Quality Standards

## Structure
- Title slide.
- Agenda/overview.
- Problem statement.
- Key findings (one per slide).
- Data visualizations.
- Recommendations.
- Next steps / call to action.

## Quality Gates
- One idea per slide.
- Minimal text — speaker carries the narrative.
- Consistent branding (colors, fonts, logo placement).
- Charts are readable from the back of the room.
"""

INFOGRAPHIC_PLAYBOOK = """# Infographic Playbook — Quality Standards

## Structure
- Headline that tells the story.
- Key stat or KPI cards.
- Visual hierarchy — most important information largest.
- Data visualizations appropriate to the data type.
- Source citations.
- Brand logo and URL.

## Quality Gates
- Tells a complete story without supporting text.
- Colorblind-safe palette.
- High resolution (300 DPI for print).
- Proper contrast ratios.
"""


def _playbook_dir() -> Path:
    return Path(__file__).parent


def load_playbook(topic: str) -> str:
    """Load a playbook by topic name."""
    playbooks = {
        "dashboard": DASHBOARD_PLAYBOOK,
        "report": REPORT_PLAYBOOK,
        "website": WEBSITE_PLAYBOOK,
        "dataset": DATASET_PLAYBOOK,
        "research": RESEARCH_PLAYBOOK,
        "presentation": PRESENTATION_PLAYBOOK,
        "infographic": INFOGRAPHIC_PLAYBOOK,
    }
    if topic not in playbooks:
        available = ", ".join(sorted(playbooks))
        return f"Unknown playbook topic: {topic}. Available: {available}"
    return playbooks[topic]


def list_playbooks() -> list[str]:
    return sorted(PLAYBOOKS)
