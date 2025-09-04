from copy import deepcopy
from agents import Runner, Agent, trace, gen_trace_id
from dotenv import load_dotenv
from prompts.agent_prompts import *
from utils import *
from tools.serper_tool import serper_search
from tools.playwright_tool import playwright_web_read
import os
import pdb
import json

load_dotenv(override=True)
default_model_name = os.environ.get('DEFAULT_MODEL_NAME')

class SectionResearchManager:
    def __init__(self, section_name: str, enable_critic: bool = True) -> None:
        self.section_name = section_name
        self.enable_critic = enable_critic

        self.complexity_agent = Agent(
            name=f"Complexity Agent: {section_name}",
            instructions=complexity_agent_system_prompt,
            model=default_model_name
        )
        self.query_gen_agent = Agent(
            name=f"Query Gen Agent: {section_name}",
            instructions=query_gen_agent_system_prompt,
            model=default_model_name
        )
        self.researcher_agent = Agent(
            name=f"Researcher agent: {section_name}",
            instructions=researcher_agent_system_prompt,
            tools=[serper_search],
            model=default_model_name
        )
        self.analyst_agent = Agent(
            name=f"Analyst agent: {section_name}",
            instructions=analyst_agent_system_prompt,
            tools=[playwright_web_read],
            model=default_model_name
        )
        self.critic_agent = Agent(
            name=f"Critic agent: {section_name}",
            instructions=critic_agent_system_prompt,
            model=default_model_name
        )
        self.editor_agent = Agent(
            name=f"Editor agent: {section_name}",
            instructions=editor_agent_system_prompt,
            model=default_model_name
        )

    async def run_section_manager(self, trace_id: str, section_details: Dict, trace_name: str, progress_callback=None) -> Dict:
        section = section_details["section_descriptor"]["section"]

        with trace(f"{trace_name} trace", trace_id=trace_id):
            base_payload = {
                "framework": section_details["framework"],
                "topic_or_idea": section_details["topic_or_idea"],
                "section_descriptor": section_details["section_descriptor"],
                "run_params": section_details.get("run_params", {})
            }
            
            # ---------- Step 1: Complexity Assessment ----------
            if progress_callback:
                await progress_callback(f"🧠 Analyzing complexity for **{section}**...")
            print(f"[{section}] Running Complexity Assessment")
            complexity_raw = await Runner.run(self.complexity_agent, as_messages(base_payload))
            
            try:
                complexity_result = json.loads(complexity_raw.final_output)
            except json.JSONDecodeError as e:
                print(f"Error parsing complexity JSON for {section}: {e}")
                complexity_result = {
                    "complexity": "moderate", 
                    "reasoning": "fallback due to parsing error",
                    "recommended_query_count": 12,
                    "search_strategy_notes": "standard approach"
                }
            
            complexity_level = complexity_result.get("complexity", "moderate")
            recommended_count = complexity_result.get("recommended_query_count", 12)
            strategy_notes = complexity_result.get("search_strategy_notes", "")
            
            print(f"[{section}] Complexity: {complexity_level}, Recommended queries: {recommended_count}")
            if progress_callback:
                await progress_callback(f"📊 **{section}** complexity: {complexity_level} → generating {recommended_count} queries")

            # ---------- Step 2: Query Generation ----------
            query_payload = {
                **base_payload,
                "complexity_level": complexity_level,
                "recommended_query_count": recommended_count,
                "search_strategy_notes": strategy_notes
            }
            
            if progress_callback:
                await progress_callback(f"🔍 Generating search queries for **{section}**...")
            print(f"[{section}] Running Query Generation")
            query_gen_raw = await Runner.run(self.query_gen_agent, as_messages(query_payload))
            
            try:
                query_gen_result = json.loads(query_gen_raw.final_output)
            except json.JSONDecodeError as e:
                print(f"Error parsing query_gen JSON for {section}: {e}")
                query_gen_result = {"queries": []}

            actual_queries = len(query_gen_result.get("queries", []))
            print(f"[{section}] Generated {actual_queries} queries (target: {recommended_count})")
            if progress_callback:
                await progress_callback(f"🌐 Researching **{section}** with {actual_queries} search queries...")

            # Update run_params with dynamic query count for researcher
            dynamic_run_params = base_payload["run_params"].copy()
            dynamic_run_params["max_queries"] = recommended_count

            # ---------- Step 3: Research ----------
            researcher_payload = {
                **base_payload, 
                "queries": query_gen_result.get("queries", []),
                "run_params": dynamic_run_params
            }
            print(f"[{section}] Running Researcher")
            researcher_raw = await Runner.run(self.researcher_agent, as_messages(researcher_payload))
            # pdb.set_trace()
            # researcher_result = parse_json(researcher_raw)
            # researcher_result = ensure_keys(researcher_result, {"facts": [], "domains_seen": [], "gap_flags": []})

            try:
                researcher_result = json.loads(researcher_raw.final_output)
            except json.JSONDecodeError as e:
                print(f"Error parsing researcher JSON for {section}: {e}")
                researcher_result = {"facts": [], "domains_seen": [], "gap_flags": []}
            facts_to_url_mapping = {}
            if 'facts' in researcher_result and len(researcher_result['facts'])>0:
                for fact in researcher_result['facts']:
                    fact_id = fact["fact_id"]
                    source_url = fact["source_url"]

                    if fact_id not in facts_to_url_mapping:
                        facts_to_url_mapping[fact_id] = []
                    facts_to_url_mapping[fact_id].append(source_url)


            # ---------- Step 4: Analysis ----------
            facts_count = len(researcher_result.get("facts", []))
            if progress_callback:
                await progress_callback(f"🧪 Analyzing {facts_count} facts for **{section}**...")
                
            analyst_payload = {
                **base_payload,
                "facts": researcher_result.get("facts", []),
                "domains_seen": researcher_result.get("domains_seen", []),
                "gap_flags": researcher_result.get("gap_flags", [])
            }
            print(f"[{section}] Running Analyst")
            analyst_raw = await Runner.run(self.analyst_agent, as_messages(analyst_payload))
            
            try:
                analyst_result = json.loads(analyst_raw.final_output)
            except json.JSONDecodeError as e:
                print(f"Error parsing analyst JSON for {section}: {e}")
                analyst_result = {"section": section, "bullets": [], "mini_takeaways": [], "conflicts": [], "gaps_next": []}

            # ---------- Step 5: Quality Assessment (Critic) ----------
            critic_result = {}
            if self.enable_critic:
                if progress_callback:
                    await progress_callback(f"🔬 Assessing research quality for **{section}**...")
                    
                critic_payload = {
                    **base_payload,
                    "facts": researcher_result.get("facts", []),
                    "analyst_json": analyst_result
                }
                print(f"[{section}] Running Quality Assessment (Critic)")
                critic_raw = await Runner.run(self.critic_agent, as_messages(critic_payload))

                try:
                    critic_result = json.loads(critic_raw.final_output)
                except json.JSONDecodeError as e:
                    print(f"Error parsing critic JSON for {section}: {e}")
                    critic_result = {
                        "needs_iteration": False,
                        "iteration_reason": "JSON parse error",
                        "quality_issues": [],
                        "gap_queries": [],
                        "confidence_assessment": 0.5
                    }

            # Extract iteration decision from Critic
            needs_iteration = critic_result.get("needs_iteration", False)
            iteration_reason = critic_result.get("iteration_reason", "")
            critic_confidence = critic_result.get("confidence_assessment", 0.5)
            gap_queries_raw = critic_result.get("gap_queries", [])
            
            print(f"[{section}] Critic assessment - Needs iteration: {needs_iteration}, Confidence: {critic_confidence:.2f}")

            # ---------- Step 6: Self-Healing Research Loop (if needed) ----------
            if self.enable_critic and needs_iteration and len(gap_queries_raw) > 0:
                if progress_callback:
                    await progress_callback(f"🔄 **{section}** needs iteration → running {len(gap_queries_raw[:5])} gap queries...")
                print(f"[{section}] Triggering self-healing loop: {iteration_reason}")
                
                # Use Critic's gap queries (already formatted)
                iteration_queries = gap_queries_raw[:5]  # Max 5 gap queries
                
                # Second research round
                iteration_payload = {
                    **base_payload,
                    "queries": iteration_queries,
                    "run_params": {**dynamic_run_params, "max_queries": len(iteration_queries)}
                }
                
                print(f"[{section}] Running iteration research with {len(iteration_queries)} gap queries")
                iteration_researcher_raw = await Runner.run(self.researcher_agent, as_messages(iteration_payload))
                
                try:
                    iteration_researcher_result = json.loads(iteration_researcher_raw.final_output)
                except json.JSONDecodeError as e:
                    print(f"Error parsing iteration researcher JSON for {section}: {e}")
                    iteration_researcher_result = {"facts": [], "domains_seen": [], "gap_flags": []}
                
                # Merge original and iteration facts (handle duplicates)
                all_facts = researcher_result.get("facts", [])
                iteration_facts = iteration_researcher_result.get("facts", [])
                
                # Simple deduplication by claim+entity+source
                seen_fact_keys = set()
                for fact in all_facts:
                    fact_key = f"{fact.get('entity', '')}-{fact.get('claim', '')}-{fact.get('source_url', '')}"
                    seen_fact_keys.add(fact_key)
                
                new_facts = []
                for fact in iteration_facts:
                    fact_key = f"{fact.get('entity', '')}-{fact.get('claim', '')}-{fact.get('source_url', '')}"
                    if fact_key not in seen_fact_keys:
                        new_facts.append(fact)
                        seen_fact_keys.add(fact_key)
                
                merged_facts = all_facts + new_facts
                merged_researcher_result = {
                    **researcher_result,
                    "facts": merged_facts,
                    "domains_seen": list(set(researcher_result.get("domains_seen", []) + iteration_researcher_result.get("domains_seen", [])))
                }
                
                print(f"[{section}] Merged {len(new_facts)} new facts, total: {len(merged_facts)}")
                if progress_callback:
                    await progress_callback(f"🔬 Re-analyzing **{section}** with {len(merged_facts)} total facts (added {len(new_facts)} new)...")
                
                # Re-run analyst with ALL facts (original + iteration facts)
                iteration_analyst_payload = {
                    **base_payload,  # Use base_payload for consistency
                    "facts": merged_facts,  # This contains ALL facts: original + new from iteration
                    "domains_seen": merged_researcher_result.get("domains_seen", []),
                    "gap_flags": merged_researcher_result.get("gap_flags", [])
                }
                
                print(f"[{section}] Re-running Analyst with expanded facts (total: {len(merged_facts)} facts)")
                iteration_analyst_raw = await Runner.run(self.analyst_agent, as_messages(iteration_analyst_payload))
                
                try:
                    iteration_analyst_result = json.loads(iteration_analyst_raw.final_output)
                except json.JSONDecodeError as e:
                    print(f"Error parsing iteration analyst JSON for {section}: {e}")
                    iteration_analyst_result = analyst_result  # fallback to original
                
                # Update the final facts and analysis for editor
                print(f"[{section}] Iteration complete - updated facts and analysis ready for Editor")
                researcher_result = merged_researcher_result
                analyst_result = iteration_analyst_result
                
                # Update facts_to_url_mapping with new facts
                for fact in new_facts:
                    fact_id = fact["fact_id"]
                    source_url = fact["source_url"]
                    if fact_id not in facts_to_url_mapping:
                        facts_to_url_mapping[fact_id] = []
                    facts_to_url_mapping[fact_id].append(source_url)

            # ---------- Step 7: Editor (Always Runs Once at the End) ----------
            if progress_callback:
                iteration_status = "with iteration enhancements" if (self.enable_critic and needs_iteration and len(gap_queries_raw) > 0) else "with original analysis"
                await progress_callback(f"✏️ Finalizing **{section}** section brief ({iteration_status})...")
            
            editor_payload = {
                **base_payload,
                "analyst_json": analyst_result,  # This is either original or iteration-enhanced
                "facts": researcher_result.get("facts", []),  # This is either original or merged facts
                "critic_json": critic_result  # Pass critic assessment to editor
            }
            
            iteration_status = "after iteration" if (self.enable_critic and needs_iteration and len(gap_queries_raw) > 0) else "no iteration"
            print(f"[{section}] Running Editor ({iteration_status})")
            
            editor_raw = await Runner.run(self.editor_agent, as_messages(editor_payload))
            
            try:
                editor_section = json.loads(editor_raw.final_output)
            except json.JSONDecodeError as e:
                print(f"Error parsing editor JSON for {section}: {e}")
                editor_section = {"section": section, "highlights": [], "facts_ref": [], "gaps_next": [], "confidence": critic_confidence}

            # Update facts_ref mapping
            if 'facts_ref' in editor_section and len(editor_section['facts_ref'])>0:
                updated_facts_ref = {}
                for fact_referred_id in editor_section['facts_ref']:
                    if fact_referred_id in facts_to_url_mapping:
                        updated_facts_ref[fact_referred_id] = facts_to_url_mapping[fact_referred_id]

                editor_section['facts_ref'] = deepcopy(updated_facts_ref)

            return {
                "section": section,
                "section_brief": editor_section,
                "artifacts": {
                    "complexity": complexity_result,
                    "queries": query_gen_result,
                    "facts": researcher_result,
                    "analysis": analyst_result,
                    "critic": critic_result,
                    "facts_to_url_mapping": facts_to_url_mapping,
                    "iteration_triggered": self.enable_critic and needs_iteration and len(gap_queries_raw) > 0
                }
            }
