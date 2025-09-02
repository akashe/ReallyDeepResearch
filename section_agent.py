from copy import deepcopy
from agents import Runner, Agent, trace, gen_trace_id
from dotenv import load_dotenv
from prompts.agent_prompts import *
from utils import *
from tools.serper_tool import serper_search
from tools.playwright_tool import playwright_web_read
import os
import pdb

load_dotenv(override=True)
default_model_name = os.environ.get('DEFAULT_MODEL_NAME')

class SectionResearchManager:
    def __init__(self, section_name: str, enable_critic: bool = True) -> None:
        self.section_name = section_name
        self.enable_critic = enable_critic

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

    async def run_section_manager(self, trace_id: str, section_details: Dict) -> Dict:
        section = section_details["section_descriptor"]["section"]

        with trace(f"{section} trace", trace_id=trace_id):
            # ---------- QueryGen ----------
            query_payload = {
                "framework": section_details["framework"],
                "topic_or_idea": section_details["topic_or_idea"],
                "section_descriptor": section_details["section_descriptor"],
                "run_params": section_details.get("run_params", {})
            }
            print(f"Running QueryGen for {section}")
            query_gen_raw = await Runner.run(self.query_gen_agent, as_messages(query_payload))
            # pdb.set_trace()
            # query_gen_result = parse_json(query_gen_raw)
            # query_gen_result = ensure_keys(query_gen_result, {"queries": []})

            query_gen_result = json.loads(query_gen_raw.final_output)

            # ---------- Researcher ----------
            researcher_payload = {**query_payload, "queries": query_gen_result.get("queries", [])}
            print(f"Running Researcher for {section}")
            researcher_raw = await Runner.run(self.researcher_agent, as_messages(researcher_payload))
            # pdb.set_trace()
            # researcher_result = parse_json(researcher_raw)
            # researcher_result = ensure_keys(researcher_result, {"facts": [], "domains_seen": [], "gap_flags": []})

            researcher_result = json.loads(researcher_raw.final_output)
            facts_to_url_mapping = {}
            if 'facts' in researcher_result and len(researcher_result['facts'])>0:
                for fact in researcher_result['facts']:
                    fact_id = fact["fact_id"]
                    source_url = fact["source_url"]

                    if fact_id not in facts_to_url_mapping:
                        facts_to_url_mapping[fact_id] = []
                    facts_to_url_mapping[fact_id].append(source_url)


            # ---------- Analyst ----------
            analyst_payload = {
                **query_payload,
                "facts": researcher_result.get("facts", []),
                "domains_seen": researcher_result.get("domains_seen", []),
                "gap_flags": researcher_result.get("gap_flags", [])
            }
            print(f"Running Analyst for {section}")
            analyst_raw = await Runner.run(self.analyst_agent, as_messages(analyst_payload))
            # pdb.set_trace()
            # analyst_result = parse_json(analyst_raw)
            # analyst_result = ensure_keys(analyst_result, {
            #     "section": section,
            #     "bullets": [],
            #     "mini_takeaways": [],
            #     "conflicts": [],
            #     "gaps_next": [],
            #     "ranked_options": [],
            #     "assumptions_to_test": []
            # })

            analyst_result = json.loads(analyst_raw.final_output)

            # ---------- Critic (optional) ----------
            critic_result = {}
            if self.enable_critic:
                critic_payload = {
                    **query_payload,
                    "analyst_json": analyst_result,
                    "domains_seen": researcher_result.get("domains_seen", []),
                    "gap_flags": researcher_result.get("gap_flags", [])
                }
                print(f"Running Critic for {section}")
                critic_raw = await Runner.run(self.critic_agent, as_messages(critic_payload))

                critic_result = json.loads(critic_raw.final_output)

                # NEW: parse to dict or set to None
                # critic_parsed = parse_json_or_none(critic_raw)

                # if critic_parsed is None:
                #     # Log a short snippet so you can see what came back
                #     txt = to_text(critic_raw)
                #     print(f"[critic][{section}] non-JSON output (first 300 chars):\n{txt[:300]}")
                #     # Fallback to empty audit (MVP)
                #     critic_result = {
                #         "bias_flags": [],
                #         "coverage_warnings": [],
                #         "gap_queries": [],
                #         "stop_recommendation": True,
                #         "reason": "critic returned non-JSON"
                #     }
                # else:
                #     critic_result = ensure_keys(critic_parsed, {
                #         "bias_flags": [],
                #         "coverage_warnings": [],
                #         "gap_queries": [],
                #         "stop_recommendation": True,
                #         "reason": "n/a"
                #     })

            # ---------- Editor (section pass) ----------
            editor_section_payload = {
                **query_payload,
                "analyst_json": analyst_result,
                "facts": researcher_result.get("facts", []),
                "domains_seen": researcher_result.get("domains_seen", []),
                "gap_flags": researcher_result.get("gap_flags", []),
                # "critic_json": critic_result
            }
            print(f"Running Editor (section) for {section}")
            editor_raw = await Runner.run(self.editor_agent, as_messages(editor_section_payload))
            # pdb.set_trace()
            # editor_section = parse_json(editor_raw)
            # editor_section = ensure_keys(editor_section, {
            #     "section": section,
            #     "highlights": [],
            #     "facts_ref": [],
            #     "gaps_next": [],
            #     "confidence": 0.0
            # })

            editor_section = json.loads(editor_raw.final_output)
            if 'facts_ref' in editor_section and len(editor_section['facts_ref'])>0:
                updated_facts_ref = {}
                for fact_referred_id in editor_section['facts_ref']:
                    if fact_referred_id in facts_to_url_mapping:
                        updated_facts_ref[fact_referred_id] = facts_to_url_mapping[fact_referred_id]

                editor_section['facts_ref'] = deepcopy(updated_facts_ref)


            # Merge critic gap queries into gaps_next (strings only)
            # if critic_result and critic_result.get("gap_queries"):
            #     extra = [gq.get("q") for gq in critic_result["gap_queries"] if isinstance(gq, dict) and gq.get("q")]
            #     if extra:
            #         editor_section["gaps_next"] = list({*editor_section.get("gaps_next", []), *extra})

            return {
                "section": section,
                "section_brief": editor_section,
                "artifacts": {
                    "queries": query_gen_result,
                    "facts": researcher_result,
                    "analysis": analyst_result,
                    "critic": critic_result,
                    "facts_to_url_mapping": facts_to_url_mapping
                }
            }
