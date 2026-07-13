"""H Heuristics domain tools — validate_dashboard, fetch_data_source, market_sizing.

These tools provide domain-specific capabilities for H Heuristics business analytics:
dashboards, market research, economic development data.
"""

from fraktal.tools.base import Tool, ToolResult


class ValidateDashboardTool(Tool):
    """10-point quality checklist for dashboard HTML."""

    name = "validate_dashboard"
    description = "Run a 10-point quality checklist on a dashboard HTML file."

    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the dashboard HTML file."},
        },
        "required": ["path"],
    }

    CHECKLIST = [
        ("Responsive viewport meta tag", '<meta name="viewport"'),
        ("Dark mode support", 'prefers-color-scheme'),
        ("Chart library loaded", 'Chart.js|plotly|d3|echarts|highcharts'),
        ("KPI summary cards", 'kpi|metric|stat-card|summary-card'),
        ("Interactive filters", 'filter|dropdown|select|date-range'),
        ("Data table present", '<table|DataTable|ag-grid'),
        ("Accessible color contrast", 'aria-label|role='),
        ("Loading states", 'loading|skeleton|spinner'),
        ("Error handling", 'error|fallback|try.*catch'),
        ("Print stylesheet", 'print|@media print'),
    ]

    def execute(self, path: str) -> ToolResult:
        import re
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            return ToolResult(output=f"File not found: {path}", success=False)

        content = p.read_text()
        results = []
        score = 0

        for label, pattern in self.CHECKLIST:
            found = bool(re.search(pattern, content, re.IGNORECASE))
            status = "✓" if found else "✗"
            if found:
                score += 1
            results.append(f"  {status} {label}")

        results.insert(0, f"Dashboard Quality Score: {score}/10\n")
        return ToolResult(output="\n".join(results))


class FetchDataSourceTool(Tool):
    """Metadata for common H Heuristics data sources."""

    name = "fetch_data_source"
    description = "Get metadata for H Heuristics data sources (WHO, IEA, SEforALL, CCA, World Bank, Lancet)."

    parameters = {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "enum": ["WHO", "IEA", "SEforALL", "CCA", "World Bank", "Lancet"],
                "description": "The data source to fetch metadata for.",
            },
        },
        "required": ["source"],
    }

    SOURCES = {
        "WHO": "World Health Organization — global health statistics, household air pollution, disease burden. https://www.who.int/data/gho",
        "IEA": "International Energy Agency — energy access, clean cooking, renewable energy data. https://www.iea.org/data-and-statistics",
        "SEforALL": "Sustainable Energy for All — energy access tracking, cooling for all, clean cooking. https://www.seforall.org/data",
        "CCA": "Clean Cooking Alliance — clean cooking industry data, market snapshots, consumer preferences. https://cleancooking.org",
        "World Bank": "World Bank Open Data — development indicators, energy access, economic data by country. https://data.worldbank.org",
        "Lancet": "The Lancet Countdown — health and climate change indicators, policy tracking. https://www.lancetcountdown.org",
    }

    def execute(self, source: str) -> ToolResult:
        info = self.SOURCES.get(source, "Unknown source.")
        return ToolResult(output=f"{source}: {info}")


class MarketSizingTool(Tool):
    """TAM estimates for key H Heuristics markets."""

    name = "market_sizing"
    description = "Get TAM estimates for key markets: electric cooking, cooling, carbon finance, PAYG solar."

    parameters = {
        "type": "object",
        "properties": {
            "market": {
                "type": "string",
                "enum": ["electric-cooking", "cooling", "carbon-finance", "payg-solar"],
                "description": "The market to size.",
            },
        },
        "required": ["market"],
    }

    ESTIMATES = {
        "electric-cooking": (
            "Electric Cooking Market (Global)\n"
            "- TAM: ~$50B by 2030 (2.4B people without clean cooking access)\n"
            "- Key regions: Sub-Saharan Africa, South Asia, Southeast Asia\n"
            "- Growth drivers: declining renewable costs, carbon finance, health awareness\n"
            "- Key players: BURN Manufacturing, ATEC, Spark+ Africa Fund"
        ),
        "cooling": (
            "Sustainable Cooling Market (Global)\n"
            "- TAM: ~$180B by 2030 (1.2B people at high risk from extreme heat)\n"
            "- Key regions: South Asia, Sub-Saharan Africa, Middle East\n"
            "- Growth drivers: rising temperatures, urbanization, AC efficiency standards\n"
            "- Key segments: efficient AC, cold chains, passive cooling"
        ),
        "carbon-finance": (
            "Carbon Finance for Clean Cooking\n"
            "- TAM: ~$1.5B annual by 2030\n"
            "- Mechanism: Article 6.4, voluntary carbon markets, compliance markets\n"
            "- Key standards: Gold Standard, Verra VCS, CDM\n"
            "- Price range: $5-25/ton CO2e for cookstove projects"
        ),
        "payg-solar": (
            "PAYG Solar Market\n"
            "- TAM: ~$24B by 2030 (600M+ people without electricity access)\n"
            "- Key regions: Sub-Saharan Africa, South Asia\n"
            "- Growth drivers: mobile money penetration, declining panel costs\n"
            "- Key players: M-KOPA, d.light, Greenlight Planet, Sun King"
        ),
    }

    def execute(self, market: str) -> ToolResult:
        info = self.ESTIMATES.get(market, "Unknown market.")
        return ToolResult(output=info)


def register_hheuristics_tools(registry) -> None:
    """Register all H Heuristics domain tools onto a ToolRegistry."""
    registry.register(ValidateDashboardTool())
    registry.register(FetchDataSourceTool())
    registry.register(MarketSizingTool())
