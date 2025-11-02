#!/usr/bin/env python3
"""
Enrich SARIF file with assessment results from YAML output.

This script reads a SARIF file and a YAML assessment file, then enriches
the SARIF with all assessment results including adding required physicalLocation
for GitHub Code Scanning compatibility.
"""

import json
import yaml
import sys
import os


def map_result_to_sarif_level(result):
    """Map assessment result to SARIF level"""
    result_lower = result.lower() if result else ""
    if result_lower in ["failed", "error"]:
        return "error"
    elif result_lower in ["warn", "warning", "needs review"]:
        return "warning"
    elif result_lower in ["passed", "pass"]:
        return "note"
    else:
        return "none"


def enrich_sarif(sarif_file, yaml_file):
    # Read SARIF file
    with open(sarif_file, 'r') as f:
        sarif_data = json.load(f)

    # Ensure SARIF structure exists
    if "runs" not in sarif_data:
        sarif_data["runs"] = []

    # Get or create the first run
    if len(sarif_data["runs"]) == 0:
        sarif_data["runs"].append({
            "tool": {
                "driver": {
                    "name": "OSPS Security Assessment",
                    "version": "1.0.0"
                }
            },
            "results": []
        })

    run = sarif_data["runs"][0]

    # Initialize results if missing
    if "results" not in run:
        run["results"] = []

    all_results = run["results"]
    existing_rule_ids = set()

    # Ensure all existing results have physicalLocation (required by GitHub Code Scanning)
    for result in all_results:
        if "ruleId" in result:
            existing_rule_ids.add(result["ruleId"])
        # Add physicalLocation if missing (using README.md as placeholder for repository-level assessments)
        if "locations" not in result or len(result["locations"]) == 0:
            result["locations"] = [{
                "physicalLocation": {
                    "artifactLocation": {
                        "uri": "README.md"
                    }
                }
            }]
        else:
            for location in result["locations"]:
                if "physicalLocation" not in location:
                    location["physicalLocation"] = {
                        "artifactLocation": {
                            "uri": "README.md"
                        }
                    }

    # Read YAML to find all assessment results
    if yaml_file and os.path.exists(yaml_file):
        try:
            with open(yaml_file, 'r') as f:
                yaml_data = yaml.safe_load(f)
        except Exception as e:
            print(f"⚠️  Error reading YAML: {e}", file=sys.stderr)
            yaml_data = None

        if yaml_data and "evaluation_suites" in yaml_data:
            for suite in yaml_data["evaluation_suites"]:
                if "control_evaluations" in suite:
                    for control in suite["control_evaluations"]:
                        control_id = control.get("control_id", "")
                        if "assessments" in control:
                            for assessment in control["assessments"]:
                                req_id = assessment.get("requirement_id", "")
                                result = assessment.get("result", "")
                                message = assessment.get("message", "")

                                if req_id and result and result != "Not Run":
                                    rule_id = f"{control_id}/{req_id}"

                                    # Only add result if not already present
                                    if rule_id not in existing_rule_ids:
                                        level = map_result_to_sarif_level(result)

                                        # Create SARIF result entry with physicalLocation (required by GitHub Code Scanning)
                                        # Include all results (including passed) so GitHub can auto-close previous failures
                                        sarif_result = {
                                            "ruleId": rule_id,
                                            "level": level,
                                            "message": {
                                                "text": message if message else f"{req_id}: {result}"
                                            },
                                            "locations": [{
                                                "physicalLocation": {
                                                    "artifactLocation": {
                                                        "uri": "README.md"
                                                    }
                                                },
                                                "logicalLocations": [{
                                                    "fullyQualifiedName": rule_id
                                                }]
                                            }]
                                        }
                                        all_results.append(sarif_result)
                                        existing_rule_ids.add(rule_id)

    # Ensure tool driver name is set
    if "tool" in run and "driver" in run["tool"]:
        if not run["tool"]["driver"].get("name"):
            run["tool"]["driver"]["name"] = "OSPS Security Assessment"
        # Remove rules array if it exists
        if "rules" in run["tool"]["driver"]:
            del run["tool"]["driver"]["rules"]

    # Update SARIF with all results
    run["results"] = all_results

    # Write updated SARIF
    with open(sarif_file, 'w') as f:
        json.dump(sarif_data, f, indent=2)

    return len(all_results)


if __name__ == "__main__":
    sarif_file = sys.argv[1]
    yaml_file = sys.argv[2] if len(sys.argv) > 2 else None
    result_count = enrich_sarif(sarif_file, yaml_file)
    print(f"✅ Enriched SARIF with {result_count} total result(s)")
