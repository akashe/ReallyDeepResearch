def big_idea_sections():
    return {
        "landscape": {
            "section": "landscape",
            "description": "Identify all key companies, startups, incumbents, research labs, and OSS projects in this industry. For each, note their product focus, funding stage (if public), and positioning.",
            "facets": ["companies", "founding_dates", "funding", "product_focus", "geographies"],
            "example_queries": [
                "\"<TOPIC>\" companies landscape 2025",
                "\"<TOPIC>\" ecosystem map filetype:ppt",
                "\"<TOPIC>\" startups funding OR acquisitions"
            ]
        },
        "product_categories": {
            "section": "product_categories",
            "description": "Classify what kinds of products exist in this industry. Group them into categories by workflow (e.g., generation, editing, distribution, monetization). Highlight what problems each solves.",
            "facets": ["use_cases", "workflows", "customer_segments", "problem_solved"],
            "example_queries": [
                "\"<TOPIC>\" categories generation editing distribution",
                "\"<TOPIC>\" workflow automation case study"
            ]
        },
        "tech_stack": {
            "section": "tech_stack",
            "description": "Describe the common technologies powering this industry: models, datasets, frameworks, infra. Look for technical benchmarks, latency issues, compute requirements, training methods.",
            "facets": ["model_types", "architectures", "datasets", "benchmarks", "infra", "latency"],
            "example_queries": [
                "\"<TOPIC>\" transformer diffusion benchmark",
                "site:arxiv.org <TOPIC> dataset",
                "\"<TOPIC>\" real-time latency"
            ]
        },
        "research_frontier": {
            "section": "research_frontier",
            "description": "Survey the academic and industrial research frontier. What new papers, prototypes, benchmarks, and gaps are being explored? Contrast commercial products vs research-only prototypes.",
            "facets": ["recent_papers", "benchmarks", "open_problems", "academic_vs_commercial_gap"],
            "example_queries": [
                "site:arxiv.org <TOPIC> 2024",
                "\"<TOPIC>\" unsolved problems research gaps"
            ]
        },
        "market_signals": {
            "section": "market_signals",
            "description": "Collect market activity: funding rounds, partnerships, acquisitions, pricing models. Who pays for what and how? What are the active business models?",
            "facets": ["funding", "partnerships", "acquisitions", "pricing", "business_models"],
            "example_queries": [
                "\"<TOPIC>\" Series A OR funding OR raise 2025",
                "\"<TOPIC>\" pricing subscription licensing"
            ]
        },
        "unmet_needs": {
            "section": "unmet_needs",
            "description": "Find evidence of customer pain points, frictions, or unsolved problems. Include user complaints, reviews, legal/regulatory blocks, and underserved customer segments.",
            "facets": ["pain_points", "frictions", "complaints", "regulation_issues", "underserved_segments"],
            "example_queries": [
                "\"<TOPIC>\" problems challenges limitations",
                "site:reddit.com <TOPIC> workflow issues"
            ]
        },
        "opportunity_theses": {
            "section": "opportunity_theses",
            "description": "Based on the above sections, synthesize opportunity hypotheses: 'If X is true, then Y is the whitespace'. Each should have a counter-thesis too.",
            "facets": ["thesis", "counter_thesis", "supporting_evidence"],
            "example_queries": [
                "\"<TOPIC>\" future opportunity OR whitespace",
                "\"<TOPIC>\" industry projections 2025"
            ]
        },
    }