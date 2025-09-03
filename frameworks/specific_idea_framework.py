def specific_idea_sections():
    return {
        "problem_pain": {
            "section": "problem_pain",
            "description": "Gather evidence that the stated problem exists, is painful, urgent, and repeated. Quantify impact if possible.",
            "facets": ["frequency", "severity", "customer_types", "evidence"],
            "example_queries": [
                "\"<TOPIC>\" delays costs enterprise",
                "\"<TOPIC>\" SLA breach case study"
            ]
        },
        "buyer_budget_owner": {
            "section": "buyer_budget_owner",
            "description": "Identify who buys/approves solutions. Which department owns the budget? Who influences decisions?",
            "facets": ["buyers", "budget_lines", "decision_influencers"],
            "example_queries": [
                "\"<TOPIC>\" budget owner CIO",
                "\"<TOPIC>\" procurement process"
            ]
        },
        "roi_story": {
            "section": "roi_story",
            "description": "Look for metrics and case studies showing ROI from similar solutions. Capture before/after comparisons.",
            "facets": ["baseline_cost", "improved_metric", "before_after"],
            "example_queries": [
                "\"<TOPIC>\" ROI case study",
                "\"<TOPIC>\" before after savings"
            ]
        },
        "defensibility": {
            "section": "defensibility",
            "description": "Identify moats: data, integration depth, workflow lock-in, network effects. Contrast with incumbents.",
            "facets": ["moats", "switching_costs", "integration_barriers", "data_lock_in"],
            "example_queries": [
                "\"<TOPIC>\" competitor analysis",
                "\"<TOPIC>\" defensibility"
            ]
        },
        "comp_landscape": {
            "section": "comp_landscape",
            "description": "List competitors, substitutes, adjacent solutions. Map their positioning and weaknesses.",
            "facets": ["competitors", "alternatives", "substitutes", "strengths_weaknesses"],
            "example_queries": [
                "\"<TOPIC>\" competitors",
                "\"<TOPIC>\" alternatives substitutes"
            ]
        },
        "gtm_channels": {
            "section": "gtm_channels",
            "description": "Investigate possible GTM motions: PLG, integrations, channel partners, direct enterprise sales. Rank feasibility.",
            "facets": ["plg", "integrations", "direct_sales", "partners"],
            "example_queries": [
                "\"<TOPIC>\" GTM strategy",
                "\"<TOPIC>\" marketplace integration"
            ]
        },
        "risks": {
            "section": "risks",
            "description": "Find risks: regulatory, security, adoption, BigTech incumbents solving it. Include 'if Google ships this tomorrow' thought.",
            "facets": ["regulatory_risks", "security_risks", "adoption_risks", "incumbent_threats"],
            "example_queries": [
                "\"<TOPIC>\" security issues",
                "\"BigTech\" <TOPIC> automation"
            ]
        },
        # "experiments_next_30d": {
        #     "section": "experiments_next_30d",
        #     "description": "Propose falsifiable experiments for this idea: landing pages, customer interviews, prototypes. Metrics for success.",
        #     "facets": ["experiments", "metrics", "timeline"],
        #     "example_queries": [
        #         "\"MVP <TOPIC>\" pilot study",
        #         "\"customer interviews\" <TOPIC> pain"
        #     ]
        # },
    }