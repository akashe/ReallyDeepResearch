import os
import json
import asyncio
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import gradio as gr
import pdb

from agents import gen_trace_id
from section_agent import SectionResearchManager  # your class from earlier

load_dotenv(override=True)

# ------------- Framework → Section descriptors (MVP set; extend later) -------------

def big_idea_sections() -> Dict[str, Dict]:
    return {
        "landscape": {
            "section": "landscape",
            "description": "Identify key companies, startups, incumbents, labs, and OSS projects; note product focus and funding stage where public.",
            "facets": ["companies", "founding_dates", "funding", "product_focus", "geographies"],
            "example_queries": [
                "\"<TOPIC>\" companies landscape 2025",
                "\"<TOPIC>\" ecosystem map filetype:ppt",
                "\"<TOPIC>\" startups funding OR acquisitions"
            ],
        },
        "product_categories": {
            "section": "product_categories",
            "description": "Classify product categories and workflows; what problems each category solves and for whom.",
            "facets": ["use_cases", "workflows", "customer_segments", "problem_solved"],
            "example_queries": [
                "\"<TOPIC>\" categories generation editing distribution",
                "\"<TOPIC>\" workflow automation case study"
            ],
        },
        "tech_stack": {
            "section": "tech_stack",
            "description": "Common models, datasets, frameworks, infra; latency, training methods, and benchmarks.",
            "facets": ["model_types", "architectures", "datasets", "benchmarks", "infra", "latency"],
            "example_queries": [
                "\"<TOPIC>\" transformer diffusion benchmark",
                "site:arxiv.org <TOPIC> dataset",
                "\"<TOPIC>\" real-time latency"
            ],
        },
        "market_signals": {
            "section": "market_signals",
            "description": "Funding rounds, partnerships, M&A, pricing models, and active business models.",
            "facets": ["funding", "partnerships", "acquisitions", "pricing", "business_models"],
            "example_queries": [
                "\"<TOPIC>\" Series A OR funding OR raise 2025",
                "\"<TOPIC>\" pricing subscription licensing"
            ],
        },
    }

def specific_idea_sections() -> Dict[str, Dict]:
    return {
        "problem_pain": {
            "section": "problem_pain",
            "description": "Evidence the problem is painful, urgent, repeated; quantify impact where possible.",
            "facets": ["frequency", "severity", "customer_types", "evidence"],
            "example_queries": [
                "\"<TOPIC>\" delays costs enterprise",
                "\"<TOPIC>\" SLA breach case study"
            ],
        },
        "buyer_budget_owner": {
            "section": "buyer_budget_owner",
            "description": "Who buys/approves; budget lines; influencers to the decision.",
            "facets": ["buyers", "budget_lines", "decision_influencers"],
            "example_queries": [
                "\"<TOPIC>\" budget owner CIO",
                "\"<TOPIC>\" procurement process"
            ],
        },
        "defensibility": {
            "section": "defensibility",
            "description": "Moats: data, integrations, workflow lock-in; contrast incumbents.",
            "facets": ["moats", "switching_costs", "integration_barriers", "data_lock_in"],
            "example_queries": [
                "\"<TOPIC>\" competitor analysis",
                "\"<TOPIC>\" defensibility"
            ],
        },
        "gtm_channels": {
            "section": "gtm_channels",
            "description": "Feasible GTM motions: PLG, integrations, partners, direct enterprise sales; rank feasibility.",
            "facets": ["plg", "integrations", "direct_sales", "partners"],
            "example_queries": [
                "\"<TOPIC>\" GTM strategy",
                "\"<TOPIC>\" marketplace integration"
            ],
        },
    }

# ------------- Shared run params -------------

DEFAULT_RUN_PARAMS = {
    "depth": "standard",
    "lookback_days": 540,
    "langs": ["en"],
    "k_per_query": 6,
    "max_queries": 12
}

# ------------- Helper: Make full section_details for SectionResearchManager -------------

def build_section_details(framework: str, topic: str, raw_desc: Dict, run_params: Dict) -> Dict:
    # Replace <TOPIC> placeholders in example queries
    ex_queries = [q.replace("<TOPIC>", topic) for q in raw_desc.get("example_queries", [])]
    section_descriptor = {
        "section": raw_desc["section"],
        "description": raw_desc["description"],
        "facets": raw_desc["facets"],
        "example_queries": ex_queries
    }
    return {
        "framework": framework,
        "topic_or_idea": topic,
        "section_descriptor": section_descriptor,
        "run_params": run_params
    }

# ------------- Orchestrator (parallel) with streaming logs -------------

async def run_framework_parallel_stream(framework: str, topic: str):
    """
    Async generator that yields (chat_text, partial_results_json) tuples as the run progresses.
    """
    if framework not in ("big-idea", "specific-idea"):
        yield (f"❌ Unknown framework: {framework}", None)
        return

    section_defs = big_idea_sections() if framework == "big-idea" else specific_idea_sections()
    trace_id = gen_trace_id()

    # Kick off all sections in parallel
    tasks = []
    mgrs = {}
    for sec_name, desc in section_defs.items():
        details = build_section_details(framework, topic, desc, DEFAULT_RUN_PARAMS)
        mgr = SectionResearchManager(sec_name, enable_critic=False)
        mgrs[sec_name] = mgr
        # emit start message
        yield (f"▶️ Starting section **{sec_name}** …", None)
        tasks.append(asyncio.create_task(mgr.run_section_manager(trace_id, details)))


    # Collect as tasks finish
    section_results = {}
    for coro in asyncio.as_completed(tasks):
        try:
            res = await coro
            sec = res["section"]
            brief = res["section_brief"]
            section_results[sec] = res
            # stream per-section done
            conf = brief.get("confidence", 0.0)
            hl_count = len(brief.get("highlights", []))
            yield (f"✅ Finished **{sec}** — highlights: {hl_count}, confidence: {conf:.2f}", None)
        except Exception as e:
            print("Something went wrong")
            yield (f"⚠️ A section failed: {e}", None)

    # Build a compact merged summary for display (you can also pass to a FinalMerge editor later)
    merged = {
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

    pretty = json.dumps(merged, indent=2, ensure_ascii=False)
    yield ("🧩 All sections complete. Merged summary JSON is ready (below).", pretty)

# ------------- Gradio UI -------------

CSS = """
#chat {height: 520px}
"""

with gr.Blocks(css=CSS, fill_height=True, theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🔎 DeepResearch MVP\nEnter a topic and choose a framework. Sections run **in parallel**; progress appears below.")

    with gr.Row():
        topic_in = gr.Textbox(
            label="Topic / Idea",
            placeholder="e.g., AI music  •  or  •  Agents to clear IT backlog",
            lines=1
        )

    with gr.Row():
        btn_big = gr.Button("Run Big-Idea Exploration", variant="primary")
        btn_specific = gr.Button("Run Specific-Idea Exploration")

    chat = gr.Chatbot(label="Run Log", height=520, elem_id="chat")
    out_json = gr.Code(label="Merged Summary (JSON)", language="json")

    # state keeps the conversation messages
    state_msgs = gr.State([])  # List[Tuple[str,str]]

    async def _start_run(framework: str, topic: str, msgs: List[Tuple[str, str]]):
        if not topic or not topic.strip():
            msgs = msgs + [("user", f"{framework}"), ("assistant", "❌ Please enter a topic/idea first.")]
            # one yield and then exit
            yield msgs, gr.update(value=""), msgs
            return

        # Add user's “start” message
        msgs = msgs + [("user", f"{framework}: {topic}")]
        collected_json = None

        # Stream updates as they arrive
        async for text, maybe_json in run_framework_parallel_stream(framework, topic.strip()):
            msgs = msgs + [("assistant", text)]
            if maybe_json is not None:
                collected_json = maybe_json
            yield msgs, gr.update(value=collected_json or ""), msgs

        # Final yield to flush last state (no return-with-value!)
        yield msgs, gr.update(value=collected_json or ""), msgs


    # Button handlers (streaming)
    btn_big.click(
        _start_run,
        inputs=[gr.State("big-idea"), topic_in, state_msgs],
        outputs=[chat, out_json, state_msgs],
        queue=True
    )

    btn_specific.click(
        _start_run,
        inputs=[gr.State("specific-idea"), topic_in, state_msgs],
        outputs=[chat, out_json, state_msgs],
        queue=True
    )

if __name__ == "__main__":
    # Launch Gradio
    demo.queue()  # enables concurrency/streaming
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
