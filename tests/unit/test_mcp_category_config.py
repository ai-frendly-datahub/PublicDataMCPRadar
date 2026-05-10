from __future__ import annotations

from pathlib import Path

from radar.analyzer import apply_entity_rules
from radar.collector import parse_markdown_section_items
from radar.config_loader import load_category_config
from radar.models import Article


def _category_name() -> str:
    configs = sorted(Path("config/categories").glob("*.yaml"))
    assert len(configs) == 1
    return configs[0].stem


def _seed_source(category):
    seeds = [source for source in category.sources if source.type == "github_readme_section"]
    assert len(seeds) == 1
    return seeds[0]


def _mcp_source(category, repository: str):
    return next(
        source
        for source in category.sources
        if source.type == "mcp_server" and source.config.get("repository") == repository
    )


def _mcp_package_source(category, package_name: str):
    return next(
        source
        for source in category.sources
        if source.type == "mcp_server" and source.config.get("package_name") == package_name
    )


def test_mcp_category_config_uses_readme_section_source() -> None:
    category = load_category_config(_category_name())

    source = _seed_source(category)
    assert source.type == "github_readme_section"
    assert source.url == "https://raw.githubusercontent.com/darjeeling/awesome-mcp-korea/main/README.md"
    assert source.section
    assert {entity.name for entity in category.entities} >= {
        "MCPDomain",
        "Provider",
        "Capability",
        "RiskScope",
        "ProjectHealth",
    }


def test_mcp_category_config_matches_section_entries() -> None:
    category = load_category_config(_category_name())
    seed_source = _seed_source(category)
    section = seed_source.section
    markdown = f"""
### {section}

**[example-mcp](https://github.com/example/example-mcp)** - {section} MCP server with API search tools.

### Other Section

**[other-mcp](https://github.com/example/other-mcp)** - Another MCP server.
"""

    items = parse_markdown_section_items(markdown, section)
    assert len(items) == 1

    article = Article(
        title=items[0]["title"],
        link=items[0]["link"],
        summary=items[0]["summary"],
        source=seed_source.name,
        category=category.category_name,
    )
    analyzed = apply_entity_rules([article], category.entities)

    assert analyzed[0].matched_entities
    assert "MCPDomain" in analyzed[0].matched_entities
    assert "ProjectHealth" in analyzed[0].matched_entities

def test_mcp_server_sources_are_disabled_metadata_candidates() -> None:
    category = load_category_config(_category_name())
    candidates = [source for source in category.sources if source.type == "mcp_server"]
    if category.category_name != "misc_mcp":
        assert candidates

    allowed_statuses = {
        "metadata_only",
        "blocked_command_unresolved",
        "blocked_env_required",
        "blocked_tool_allowlist_unresolved",
        "blocked_runtime_config_unresolved",
        "candidate_ready_for_fake_transport_test",
        "fake_transport_smoke_test_passed",
        "permanently_disabled_redundant",
    }
    for source in candidates:
        assert source.enabled is False
        assert source.collection_tier == "C4_mcp_tool"
        assert source.content_type == "mcp_tool_result"
        assert source.config["activation_status"] in allowed_statuses
        assert source.config["repository"]
        assert isinstance(source.config.get("tools", []), list)
        assert isinstance(source.config.get("resources", []), list)
        assert source.config["docs_advisory_audit_status"] == "passed"
        assert (
            source.config["docs_advisory_audit_artifact"]
            == "_workspace/2026-04-30_cycle69_mcp_docs_advisory_audit.json"
        )
        assert source.config["github_readme_present"] is True
        assert source.config["github_docs_present"] is True
        assert source.config["github_docs_paths"]
        assert source.config["github_security_advisory_access_status"].startswith("checked")
        assert source.config["github_security_advisory_count"] >= 0
        if source.config.get("command_discovery_status"):
            assert source.config["command_discovery_checked_at"]
            assert source.config["command_discovery_artifact"] in {
                "_workspace/2026-04-30_cycle71_mcp_command_discovery_audit.json",
                "_workspace/2026-04-30_cycle72_publicdata_package_split_audit.json",
            }
        if "command_or_endpoint_unresolved" in source.config.get("activation_gates", []):
            assert source.config["command_discovery_status"]
        if source.config["activation_status"] != "metadata_only":
            assert source.config["activation_audited_at"]
            if source.config["activation_status"].startswith("permanently_disabled_"):
                assert source.config["disabled_reason"]
                assert source.config["activation_gates"] == []
            else:
                assert source.config["activation_gates"]


def test_seoul_data_candidate_has_tool_allowlist_but_runtime_config_block() -> None:
    category = load_category_config(_category_name())
    source = _mcp_source(category, "pinnaclesoft-ko/be-node-seoul-data-mcp")

    assert source.enabled is False
    assert source.config["activation_status"] == "permanently_disabled_redundant"
    assert source.config["env"] == []
    assert source.config["event_model"] == "mcp_tool_result"
    assert "upstream_runtime_config_patch_required" not in source.config["activation_gates"]
    assert source.config["activation_gates"] == []
    assert "tool_resource_allowlist_required" not in source.config["activation_gates"]
    assert "tool_allowlist_unresolved" not in source.config["risk_scope"]
    assert source.config["package_registry_crosscheck_status"] == "failed_unpublished_package"
    assert source.config["package_name"] == "KoreaSeoul"
    assert (
        source.config["package_registry_crosscheck_artifact"]
        == "_workspace/2026-05-07_mcp_registry_crosscheck_gate_closure.json"
    )
    assert "registry_crosscheck_required" not in source.config["activation_gates"]
    assert source.config["package_bin"] == {"mcp-server-korea-seoul": "dist/index.js"}
    assert source.config["command_semantics"] == "npm_package_unpublished_git_package_launchable"
    assert source.config["original_command_status"] == "failed_unpublished_npm_package"
    assert source.config["github_package_probe_status"] == "failed_tool_error_payload"
    assert source.config["runtime_config_issue"] == "upstream_hardcoded_blank_api_key"
    assert source.config["runtime_resolution_status"] == "permanently_disabled_redundant"
    assert (
        source.config["runtime_resolution_artifact"]
        == "_workspace/2026-05-07_mcp_runtime_blocker_resolution.json"
    )
    assert (
        source.config["runtime_resolution_replacement_repository"]
        == "Koomook/data-go-mcp-servers"
    )
    assert source.config["disabled_reason"] == "redundant_with_data_go_mcp_package_split"
    assert (
        source.config["real_transport_probe_artifact"]
        == "_workspace/2026-04-29_cycle47_publicdata_github_package_probe.json"
    )
    assert source.config["args"] == [
        "-y",
        "--package",
        "github:pinnaclesoft-ko/be-node-seoul-data-mcp",
        "mcp-server-korea-seoul",
    ]
    assert [tool["name"] for tool in source.config["tools"]] == [
        "KoreaSeoulSubwayStatus",
        "CulturalEventInfo",
    ]


def test_seoul_data_candidate_has_fake_transport_evidence() -> None:
    category = load_category_config(_category_name())
    source = _mcp_source(category, "pinnaclesoft-ko/be-node-seoul-data-mcp")

    assert source.config["activation_status"] == "permanently_disabled_redundant"
    assert source.config["fake_transport_smoke_test_status"] == "passed"
    assert (
        source.config["fake_transport_smoke_test_artifact"]
        == "_workspace/2026-05-07_publicdata_pinnaclesoft_seoul_data_fake_probe.json"
    )
    assert (
        source.config["fake_transport_fixture"]
        == "fixtures/mcp/fake_pinnaclesoft_seoul_data_mcp.py"
    )
    assert "fake_transport_smoke_test_required" not in source.config["activation_gates"]
    assert "upstream_runtime_config_patch_required" not in source.config["activation_gates"]
    assert source.config["activation_gates"] == []


def test_data_go_candidates_are_split_to_package_level_sources() -> None:
    category = load_category_config(_category_name())
    packages = {
        "data-go-mcp.nps-business-enrollment": [
            "search_business",
            "get_business_detail",
            "get_period_status",
        ],
        "data-go-mcp.nts-business-verification": [
            "validate_business",
            "check_business_status",
            "batch_validate_businesses",
        ],
        "data-go-mcp.pps-narajangteo": [
            "search_bid_announcements",
            "search_successful_bids",
            "search_contracts",
            "get_bid_detail",
        ],
        "data-go-mcp.fsc-financial-info": [
            "get_summary_financial_statement",
            "get_balance_sheet",
            "get_income_statement",
            "search_company_financial_info",
        ],
        "data-go-mcp.presidential-speeches": [
            "list_speeches",
            "search_speeches",
            "get_recent_speeches",
        ],
        "data-go-mcp.msds-chemical-info": [
            "search_chemicals",
            "get_chemical_safety_summary",
            "get_chemical_handling_info",
            "get_chemical_properties",
            "get_chemical_regulatory_info",
            "get_chemical_section",
            "get_complete_msds",
        ],
    }

    assert {
        source.config.get("package_name")
        for source in category.sources
        if source.type == "mcp_server"
        and source.config.get("repository") == "Koomook/data-go-mcp-servers"
    } == set(packages)

    for package_name, tools in packages.items():
        source = _mcp_package_source(category, package_name)

        assert source.enabled is False
        assert source.config["repository"] == "Koomook/data-go-mcp-servers"
        assert source.config["activation_status"] == "blocked_env_required"
        assert source.config["command_discovery_status"] == "resolved_package_uvx"
        assert source.config["command_discovery_artifact"] == (
            "_workspace/2026-04-30_cycle72_publicdata_package_split_audit.json"
        )
        assert source.config["command"] == "uvx"
        assert source.config["args"] == [f"{package_name}@latest"]
        assert source.config["env"] == ["API_KEY"]
        assert source.config["event_model"] == "mcp_tool_result"
        assert source.config["package_registry"] == "pypi"
        assert source.config["package_registry_crosscheck_status"] == "passed"
        assert (
            source.config["package_registry_crosscheck_artifact"]
            == "_workspace/2026-05-07_mcp_registry_crosscheck_gate_closure.json"
        )
        assert "command_or_endpoint_unresolved" not in source.config["activation_gates"]
        assert "tool_resource_allowlist_required" not in source.config["activation_gates"]
        assert "env_secret_documentation_required" not in source.config["activation_gates"]
        assert source.config["env_documentation_status"] == "documented_no_secret_placeholder"
        assert (
            source.config["env_documentation_artifact"]
            == "_workspace/2026-05-07_mcp_env_documentation_manifest.json"
        )
        assert "registry_crosscheck_required" not in source.config["activation_gates"]
        assert "tool_allowlist_unresolved" not in source.config["risk_scope"]
        assert source.config["real_transport_readiness_status"] == "blocked_missing_api_key"
        assert source.config["real_transport_secret_cluster"] == "data_go_kr_api_key"
        assert (
            source.config["real_transport_secret_handling"]
            == "env_injection_only_no_repository_storage"
        )
        assert (
            source.config["real_transport_readiness_artifact"]
            == "_workspace/2026-05-08_publicdata_api_key_cluster_readiness.json"
        )
        assert (
            source.config["real_transport_smoke_batch"]
            == "P0-publicdata-data-go-api-key"
        )
        assert (
            source.config["real_transport_smoke_policy"]
            == "disabled_until_api_key_supplied_bounded_read_only_allowlist_only"
        )
        assert source.config["tools"] == tools


def test_data_go_api_key_cluster_readiness_handoff_is_closed() -> None:
    category = load_category_config(_category_name())
    sources = [
        source
        for source in category.sources
        if source.type == "mcp_server"
        and source.config.get("repository") == "Koomook/data-go-mcp-servers"
    ]

    assert len(sources) == 6
    assert {source.config["real_transport_secret_cluster"] for source in sources} == {
        "data_go_kr_api_key"
    }
    assert {tuple(source.config["env"]) for source in sources} == {("API_KEY",)}
    assert {source.config["activation_status"] for source in sources} == {
        "blocked_env_required"
    }
    assert {source.enabled for source in sources} == {False}
    assert all(
        source.config["activation_gates"] == ["real_transport_smoke_test_required"]
        for source in sources
    )
    assert all(
        source.config["fake_transport_smoke_test_status"] == "passed" for source in sources
    )
    assert all(
        source.config["package_registry_crosscheck_status"] == "passed"
        for source in sources
    )
    assert all(
        source.config["real_transport_readiness_status"] == "blocked_missing_api_key"
        for source in sources
    )
    assert all(
        source.config["real_transport_secret_handling"]
        == "env_injection_only_no_repository_storage"
        for source in sources
    )
    assert sorted(source.config["real_transport_smoke_order"] for source in sources) == [
        10,
        20,
        30,
        40,
        50,
        60,
    ]
    disallowed_risks = {
        "financial_action_possible",
        "local_file_write",
        "user_account_scope",
        "write_or_mutation_possible",
    }
    assert all(not (set(source.config["risk_scope"]) & disallowed_risks) for source in sources)


def test_presidential_speeches_candidate_has_fake_transport_evidence() -> None:
    category = load_category_config(_category_name())
    source = _mcp_package_source(category, "data-go-mcp.presidential-speeches")

    assert source.enabled is False
    assert source.config["activation_status"] == "blocked_env_required"
    assert source.config["fake_transport_smoke_test_status"] == "passed"
    assert (
        source.config["fake_transport_smoke_test_artifact"]
        == "_workspace/2026-05-01_cycle82_publicdata_presidential_speeches_fake_probe.json"
    )
    assert (
        source.config["fake_transport_fixture"]
        == "fixtures/mcp/fake_koomook_presidential_speeches_mcp.py"
    )
    assert source.config["event_model"] == "mcp_tool_result"
    assert source.config["tools"] == [
        "list_speeches",
        "search_speeches",
        "get_recent_speeches",
    ]
    assert source.config["env"] == ["API_KEY"]
    assert "fake_transport_smoke_test_required" not in source.config["activation_gates"]
    assert "real_transport_smoke_test_required" in source.config["activation_gates"]


def test_remaining_data_go_packages_have_fake_transport_evidence() -> None:
    category = load_category_config(_category_name())

    expected = {
        "data-go-mcp.nps-business-enrollment": {
            "artifact": "_workspace/2026-05-01_cycle82_publicdata_nps_business_enrollment_fake_probe.json",
            "fixture": "fixtures/mcp/fake_koomook_nps_business_enrollment_mcp.py",
        },
        "data-go-mcp.nts-business-verification": {
            "artifact": "_workspace/2026-05-01_cycle82_publicdata_nts_business_verification_fake_probe.json",
            "fixture": "fixtures/mcp/fake_koomook_nts_business_verification_mcp.py",
        },
        "data-go-mcp.pps-narajangteo": {
            "artifact": "_workspace/2026-05-01_cycle82_publicdata_pps_narajangteo_fake_probe.json",
            "fixture": "fixtures/mcp/fake_koomook_pps_narajangteo_mcp.py",
        },
        "data-go-mcp.fsc-financial-info": {
            "artifact": "_workspace/2026-05-01_cycle82_publicdata_fsc_financial_info_fake_probe.json",
            "fixture": "fixtures/mcp/fake_koomook_fsc_financial_info_mcp.py",
        },
        "data-go-mcp.msds-chemical-info": {
            "artifact": "_workspace/2026-05-01_cycle82_publicdata_msds_chemical_info_fake_probe.json",
            "fixture": "fixtures/mcp/fake_koomook_msds_chemical_info_mcp.py",
        },
    }

    for package_name, expected_paths in expected.items():
        source = _mcp_package_source(category, package_name)
        assert source.enabled is False
        assert source.config["activation_status"] == "blocked_env_required"
        assert source.config["fake_transport_smoke_test_status"] == "passed"
        assert source.config["fake_transport_smoke_test_artifact"] == expected_paths["artifact"]
        assert source.config["fake_transport_fixture"] == expected_paths["fixture"]
        assert source.config["env"] == ["API_KEY"]
        assert "fake_transport_smoke_test_required" not in source.config["activation_gates"]
        assert "real_transport_smoke_test_required" in source.config["activation_gates"]
