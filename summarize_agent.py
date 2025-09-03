import json
from tools.playwright_tool import playwright_web_read 
from prompts.agent_prompts import final_summarizer_prompt
from agents import Agent, Runner, trace
from dotenv import load_dotenv
import os

load_dotenv(override=True)
default_model_name = os.environ.get('DEFAULT_MODEL_NAME')

final_report_agent = Agent(
    name="Final Report Agent",
    instructions=final_summarizer_prompt,
    tools=[playwright_web_read],   # so it can open a few URLs if needed
    model=default_model_name
)

async def generate_final_report(framework: str, topic: str, section_results: dict, trace_id: str, trace_name: str) -> dict:
    """
    Generate comprehensive final report with fact deduplication and framework-specific structure.
    
    Args:
        framework: "big-idea" or "specific-idea" 
        topic: research topic/idea
        section_results: dict of section_name -> {section_brief, artifacts}
    
    Returns:
        dict with structured_summary (JSON) and narrative_report (text)
    """
    
    # Build structured summary for JSON display
    merged_summary = {
        "framework": framework,
        "topic_or_idea": topic,
        "sections": {
            s: {
                "highlights": section_results[s]["section_brief"].get("highlights", []),
                "confidence": section_results[s]["section_brief"].get("confidence", 0.0),
                "facts_ref": section_results[s]["section_brief"].get("facts_ref", []),
                "gaps_next": section_results[s]["section_brief"].get("gaps_next", []),
            }
            for s in section_results
        }
    }
    
    # Collect section analyses
    section_analyses = [
        res["artifacts"]["analysis"] for res in section_results.values()
    ]
    
    # Deduplicate facts across sections (handling fact_id collisions)
    all_facts = []
    seen_claims = set()
    global_facts_to_url_mapping = {}
    fact_id_counter = 1
    
    for section_name, res in section_results.items():
        facts = res["artifacts"]["facts"].get("facts", [])
        section_facts_mapping = res["artifacts"].get("facts_to_url_mapping", {})
        
        for fact in facts:
            # Create unique key for deduplication based on content
            entity = fact.get('entity', '').strip().lower()
            claim = fact.get('claim', '').strip().lower()
            source_url = fact.get('source_url', '')
            fact_key = f"{entity}|{claim}|{source_url}"
            
            if fact_key not in seen_claims:
                # Create new global fact_id to avoid collisions
                new_fact_id = f"global_{fact_id_counter}"
                fact_id_counter += 1
                
                # Update fact with new global ID
                fact_copy = fact.copy()
                old_fact_id = fact.get('fact_id')
                fact_copy['fact_id'] = new_fact_id
                fact_copy['section_source'] = section_name  # Track which section this came from
                
                all_facts.append(fact_copy)
                seen_claims.add(fact_key)
                
                # Map the new global fact_id to URLs, preserving old mapping
                if old_fact_id in section_facts_mapping:
                    global_facts_to_url_mapping[new_fact_id] = section_facts_mapping[old_fact_id]
    
    # Create section-specific facts mapping (keeping original IDs for section references)
    facts_to_url_mapping = {
        s: res["artifacts"].get("facts_to_url_mapping", {})
        for s,res in section_results.items()
    }
    
    # Extract section confidences
    section_confidences = {
        s: res["section_brief"].get("confidence", 0.0)
        for s,res in section_results.items()
    }

    # Set framework-specific reporting structure
    if framework == "big-idea":
        report_structure = "a market landscape analysis"
        narrative_structure = """
**Foundation**: What is this domain and why does it matter? Establish the basic concept, scale, and relevance.

**Current Landscape**: Who are the key players and what's happening now? Introduce major companies, technologies, and current market activity with concrete examples.

**Market Dynamics**: How does this ecosystem work? Explore business models, adoption patterns, competitive dynamics, and value chains.

**Critical Insights**: What are the non-obvious patterns and tensions? Synthesize findings to reveal underlying trends, contradictions, and emerging opportunities.

**Strategic Implications**: What does this mean for stakeholders? Distill insights into actionable understanding and key considerations for decision-makers.
"""
    else:  # specific-idea
        report_structure = "a business viability assessment" 
        narrative_structure = """
**Foundation**: What problem does this solve and for whom? Establish the core pain point, affected stakeholders, and why this matters now.

**Problem-Solution Fit**: How real and urgent is this problem? Present evidence of customer pain, market size, and demand signals with specific examples.

**Competitive Reality**: What's the competitive context? Analyze existing solutions, differentiation opportunities, and defensive positioning.

**Business Viability**: How could this work as a business? Explore revenue models, go-to-market approaches, and buyer dynamics.

**Strategic Assessment**: What are the key risks and next steps? Synthesize insights into execution priorities and critical uncertainties to resolve.
"""

    # Prepare payload for final report agent
    payload = {
        "framework": framework,
        "topic_or_idea": topic,
        "report_structure": report_structure,
        "narrative_structure": narrative_structure,
        "section_analyses": section_analyses,
        "facts_to_url_mapping": facts_to_url_mapping,
        "all_facts": all_facts,
        "section_confidences": section_confidences,
        "global_facts_to_url_mapping": global_facts_to_url_mapping
    }

    with trace(f"{trace_name} trace", trace_id=trace_id):
        # Generate final narrative report
        final_report = await Runner.run(final_report_agent, [
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
        ])

    return {
        "structured_summary": merged_summary,
        "narrative_report": final_report.final_output,
        "metadata": {
            "total_facts": len(all_facts),
            "avg_confidence": sum(section_confidences.values()) / len(section_confidences) if section_confidences else 0,
            "sections_count": len(section_results)
        }
    }