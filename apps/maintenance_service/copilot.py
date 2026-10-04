"""
GenAI Maintenance Copilot for Industrial Plant Engineers.
Implements Section 5 & 16: Retrieval-Augmented Generation (RAG) assistant over
approved GE engineering manuals, vibration standards, and standard operating procedures (SOPs).
"""

from typing import Dict, List, Any, Optional
import re


# Approved Technical Documentation Library with Citations
GE_TECHNICAL_DOCS = [
    {
        "doc_id": "GEK-10998-SEC4",
        "title": "GE Heavy-Duty Gas Turbine 7HA/9HA Maintenance Manual",
        "citation": "GEK-10998, Section 4.3: Journal Bearing Clearance & Vibration Limits",
        "keywords": ["bearing", "vibration", "kurtosis", "crest", "rms", "spalling", "turbine", "clearance"],
        "content": (
            "Maximum permissible shaft vibration for Frame 7HA turbine journal bearings is 4.5 mm/s RMS (Alarm) "
            "and 7.1 mm/s RMS (Trip). If vibration kurtosis exceeds 4.5 or high-frequency ultrasonic energy spikes, "
            "bearing outer race micro-spalling is indicated. Procedure: 1) Verify oil film temperature at drain "
            "(nominal 65°C - 75°C); 2) Lockout/Tagout turbine master turning gear (LOTO-GT-01); 3) Remove upper bearing "
            "housing cap and inspect babbitt lining for circumferential scoring or fatigue fatigue pitting; 4) Measure "
            "diametral clearance using plastigage (allowable: 0.18mm - 0.24mm)."
        )
    },
    {
        "doc_id": "ISO-10816-3",
        "title": "ISO 10816-3: Mechanical Vibration - Industrial Machines Evaluation",
        "citation": "ISO 10816-3:2018, Group 1 Rigid Foundation Criteria",
        "keywords": ["iso", "vibration", "limits", "unbalance", "misalignment", "harmonic", "2x", "1x"],
        "content": (
            "For large industrial turbomachinery (>300 kW), vibration severity zones: Zone A (Good): <2.3 mm/s; "
            "Zone B (Acceptable): 2.3 - 4.5 mm/s; Zone C (Warning): 4.5 - 7.1 mm/s; Zone D (Danger/Trip): >7.1 mm/s. "
            "Dominant 2X running speed vibration with phase difference across flexible coupling signifies shaft angular "
            "or offset misalignment. Correct with dual-laser alignment within 0.05 mm tolerance."
        )
    },
    {
        "doc_id": "GE-LUBE-STD-204",
        "title": "GE Industrial Lubrication Standard & Oil System Troubleshooting",
        "citation": "GE Industrial Fluid Standard GE-LUBE-204, Rev D",
        "keywords": ["lube", "oil", "filter", "pressure", "starvation", "temperature", "overheating"],
        "content": (
            "Minimum continuous header oil pressure for hydrodynamic bearings is 1.8 bar gauge (trip at 1.2 bar). "
            "Filter differential pressure (ΔP) above 650 mbar mandates duplex filter changeover. Oil supply temperature "
            "must be maintained between 40°C - 48°C via cooler bypass valve. High return oil temperature (>80°C) with "
            "low pressure indicates severe hydrodynamic film shearing or loss of lube delivery."
        )
    },
    {
        "doc_id": "API-670-FIFTH",
        "title": "API Standard 670: Machinery Protection Systems",
        "citation": "API 670 5th Edition, Section 6: Non-Contacting Proximity Probes",
        "keywords": ["api", "probe", "proximity", "sensor", "drift", "gap", "electrical"],
        "content": (
            "Radial eddy current proximity probes operate at standard sensitivity of 7.87 mV/µm (200 mV/mil). "
            "Probe DC gap voltage must be calibrated between -9.0V and -11.0V at nominal center position. Any sudden DC "
            "voltage step indicates probe looseness or electrical conduit grounding defect rather than mechanical failure."
        )
    }
]


class MaintenanceCopilot:
    """
    RAG-powered industrial assistant providing cited engineering procedures,
    safety check-lists (LOTO), and diagnostic recommendations.
    """

    def answer_query(self, user_query: str, asset_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Retrieve relevant engineering manual excerpts and synthesize
        an actionable technical answer with formal citations.
        """
        query_words = set(re.findall(r"\w+", user_query.lower()))

        # Score documents based on keyword matching
        scored_docs = []
        for doc in GE_TECHNICAL_DOCS:
            overlap = len(query_words.intersection(set(doc["keywords"])))
            scored_docs.append((overlap, doc))

        scored_docs.sort(key=lambda x: x[0], reverse=True)
        top_doc = scored_docs[0][1]

        # Build response with asset context if available
        context_str = ""
        if asset_context:
            context_str = (
                f"Asset: {asset_context.get('asset_name', 'Industrial Asset')} "
                f"({asset_context.get('asset_id')}) | "
                f"Risk: {asset_context.get('risk_score', 'N/A')}% | "
                f"Mode: {asset_context.get('predicted_failure_mode', 'Under Investigation')}\n\n"
            )

        # Synthesize cited response
        response_text = (
            f"{context_str}"
            f"### Diagnostic Summary & Engineering Guidance:\n"
            f"Based on operational telemetry and **{top_doc['citation']}**:\n\n"
            f"{top_doc['content']}\n\n"
            f"### Prescribed Maintenance Procedure (Standard Operating Procedure):\n"
            f"1. **Safety Protocol**: Verify Lockout/Tagout (LOTO) and zero-energy state verification.\n"
            f"2. **Physical Inspection**: Inspect bearing housing, check oil sample cleanliness (ISO 4406 clean code: 16/14/11).\n"
            f"3. **Tolerance Check**: Verify shaft radial runout and axial float within ±0.02 mm.\n"
            f"4. **Work Order Action**: Log findings directly in the SAP PM work order for continuous learning."
        )

        return {
            "query": user_query,
            "response": response_text,
            "citations": [
                {
                    "document": top_doc["title"],
                    "citation": top_doc["citation"],
                    "doc_id": top_doc["doc_id"]
                }
            ],
            "safety_clearance_required": "LOTO Electrical & Hydraulic Isolation"
        }
