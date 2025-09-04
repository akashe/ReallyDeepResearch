import os
import json
import asyncio
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import gradio as gr
import pdb

from agents import gen_trace_id
from section_agent import SectionResearchManager 
from summarize_agent import generate_final_report
from frameworks.big_idea_framework import big_idea_sections
from frameworks.specific_idea_framework import specific_idea_sections

load_dotenv(override=True)

# ------------- Framework → Section descriptors (loaded from framework files) -------------

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
    trace_name = f"{framework} {topic}"

    # Use asyncio.Queue to collect progress messages from all sections
    progress_queue = asyncio.Queue()
    
    # Create a progress callback that adds messages to the queue
    async def progress_callback(message: str):
        await progress_queue.put(message)

    # Kick off all sections in parallel
    tasks = []
    mgrs = {}
    for sec_name, desc in section_defs.items():
        details = build_section_details(framework, topic, desc, DEFAULT_RUN_PARAMS)
        mgr = SectionResearchManager(sec_name, enable_critic=False)
        mgrs[sec_name] = mgr
        # emit start message
        yield (f"▶️ Starting section **{sec_name}** …", None)
        tasks.append(asyncio.create_task(mgr.run_section_manager(trace_id, details, trace_name, progress_callback)))

    # Monitor both task completion and progress messages
    active_tasks = set(tasks)
    section_results = {}
    
    while active_tasks or not progress_queue.empty():
        # Check for completed tasks
        done_tasks = {task for task in active_tasks if task.done()}
        for task in done_tasks:
            active_tasks.remove(task)
            try:
                res = await task
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
        
        # Check for progress messages
        try:
            while True:
                message = progress_queue.get_nowait()
                yield (message, None)
        except asyncio.QueueEmpty:
            pass
        
        # Brief sleep to prevent busy waiting
        if active_tasks:
            await asyncio.sleep(0.1)

    # Generate comprehensive final report using summarize_agent
    yield ("🔄 Generating final report with fact verification...", None)
    
    report_data = await generate_final_report(framework, topic, section_results, trace_id, trace_name)
    
    # Format the final output - this will be handled by the improved UI
    yield ("📄 Report Complete", report_data)


# ------------- Gradio UI -------------

CSS = """
#chat {height: 400px}
.json-display {font-family: 'Monaco', 'Consolas', monospace; font-size: 12px;}
.metadata-display {background: #f8f9fa; padding: 10px; border-radius: 5px;}
"""

with gr.Blocks(css=CSS, fill_height=True, theme=gr.themes.Soft()) as demo:
    gr.Markdown("## 🔎 DeepResearch MVP\nEnter a topic and choose a framework.")

    with gr.Row():
        topic_in = gr.Textbox(
            label="Topic / Idea",
            placeholder="e.g., AI music  •  or  •  Agents to clear IT backlog",
            lines=1
        )

    with gr.Row():
        btn_big = gr.Button("🌐 Run Big-Idea Exploration", variant="primary")
        btn_specific = gr.Button("🎯 Run Specific-Idea Exploration")

    # Progress chat at the top
    chat = gr.Chatbot(label="🔄 Research Progress", height=400, elem_id="chat")
    
    # Organized results in tabs
    with gr.Tabs():
        with gr.TabItem("📄 Executive Report"):
            narrative_display = gr.Markdown(
                label="Executive Summary",
                value="Research results will appear here...",
                elem_classes=["narrative-display"]
            )
            metadata_display = gr.Markdown(
                label="Research Statistics", 
                value="",
                elem_classes=["metadata-display"]
            )
            
        with gr.TabItem("📊 Structured Data"):
            json_display = gr.Code(
                label="Section Analysis (JSON)",
                language="json",
                value="{}",
                elem_classes=["json-display"]
            )
            
        with gr.TabItem("💾 Export"):
            download_data = gr.JSON(label="Full Research Data", visible=False)
            gr.Markdown("**Export Options:**")
            with gr.Row():
                export_json_btn = gr.DownloadButton("📥 Download JSON", visible=True)
                export_md_btn = gr.DownloadButton("📝 Download Markdown", visible=True)
            
            # Hidden file outputs for downloads
            json_file = gr.File(visible=False)
            md_file = gr.File(visible=False)

    # Hidden state for messages and data
    state_msgs = gr.State([])  # List[Tuple[str,str]]

    async def _start_run(framework: str, topic: str, msgs: List[Tuple[str, str]]):
        if not topic or not topic.strip():
            msgs = msgs + [("user", f"{framework}"), ("assistant", "❌ Please enter a topic/idea first.")]
            # Clear all outputs and return
            yield msgs, "", "", "", {}, msgs
            return

        # Add user's "start" message
        msgs = msgs + [("user", f"{framework}: {topic}")]
        
        # Clear previous outputs
        current_json = ""
        current_narrative = ""
        current_metadata = ""

        # Stream updates as they arrive
        async for text, report_data in run_framework_parallel_stream(framework, topic.strip()):
            msgs = msgs + [("assistant", text)]
            
            if report_data is not None:
                # Extract different parts of the report
                if isinstance(report_data, dict):
                    # Format structured summary as JSON
                    structured_summary = report_data.get("structured_summary", {})
                    current_json = json.dumps(structured_summary, indent=2, ensure_ascii=False)
                    
                    # Extract narrative report
                    current_narrative = report_data.get("narrative_report", "")
                    
                    # Format metadata
                    metadata = report_data.get("metadata", {})
                    current_metadata = f"""**Research Metadata:**
- Total Facts: {metadata.get('total_facts', 0)}
- Average Confidence: {metadata.get('avg_confidence', 0):.2f}
- Sections Analyzed: {metadata.get('sections_count', 0)}"""
            
            yield msgs, current_json, current_narrative, current_metadata, report_data or {}, msgs

        # Final yield to ensure last state is displayed
        yield msgs, current_json, current_narrative, current_metadata, report_data or {}, msgs

    # Download functions
    def download_json(report_data):
        if not report_data:
            return None
        
        import tempfile
        import os
        
        # Create temporary file for JSON download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
            temp_path = f.name
        
        return temp_path

    def download_markdown(report_data):
        if not report_data:
            return None
            
        import tempfile
        import os
        
        # Get the narrative report
        narrative = report_data.get("narrative_report", "# No report available")
        
        # Create temporary file for Markdown download
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write(narrative)
            temp_path = f.name
        
        return temp_path

    # Button handlers (streaming)
    btn_big.click(
        _start_run,
        inputs=[gr.State("big-idea"), topic_in, state_msgs],
        outputs=[chat, json_display, narrative_display, metadata_display, download_data, state_msgs],
        queue=True
    )

    btn_specific.click(
        _start_run,
        inputs=[gr.State("specific-idea"), topic_in, state_msgs],
        outputs=[chat, json_display, narrative_display, metadata_display, download_data, state_msgs],
        queue=True
    )

    # Download button handlers
    export_json_btn.click(
        fn=download_json,
        inputs=[download_data],
        outputs=[json_file]
    )

    export_md_btn.click(
        fn=download_markdown,
        inputs=[download_data], 
        outputs=[md_file]
    )

if __name__ == "__main__":
    # Launch Gradio
    demo.queue()  # enables concurrency/streaming
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", "7860")))
