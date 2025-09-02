section_information_schema = """
{
  "framework": "big-idea | specific-idea",
  "topic_or_idea": "string",
  "section_descriptor": {
    "section": "string",                      // e.g., "tech_stack"
    "description": "string",                  // what to find/synthesize
    "facets": ["string", "..."],              // what dimensions matter
    "example_queries": ["string", "..."]      // 2–5 seeds for flavor
  },
  "run_params": {
    "depth": "shallow | standard | deep",
    "lookback_days": 540,
    "langs": ["en","de","ja"],                // optional
    "k_per_query": 6,                         // top-K per query
    "max_queries": 12
  }
}
"""