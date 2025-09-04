# ReallyDeepResearch

A **multi-agent research system** that conducts comprehensive topic analysis through parallel section exploration and intelligent fact synthesis.

## What It Does

- **Parallel Research Pipeline**: 7 specialized agents per research section working simultaneously
- **Self-Healing Research**: Quality assessment with automatic iteration loops for incomplete findings  
- **Framework-Driven Analysis**: Structured exploration via `big-idea` (market landscape) or `specific-idea` (business viability) frameworks
- **Fact Deduplication**: Cross-section intelligence with conflict detection and resolution
- **Publishable Reports**: Executive summaries with source verification and downloadable formats

## How It's Different

| Feature | ReallyDeepResearch | Perplexity Pro | OpenAI Deep Research |
|---------|-------------------|----------------|-----------|
| **Research Depth** | 7-step pipeline per section | Single-pass queries | Chain-of-thought reasoning |
| **Parallel Processing** | Multi-section simultaneous | Sequential search | Linear processing |
| **Quality Control** | Critic agent + self-healing | Manual refinement | Built-in verification |
| **Structured Output** | Framework-specific analysis | General summaries | Problem-specific responses |
| **Fact Verification** | Cross-source validation | Source citations | Integrated fact-checking |

## Quick Start

### Prerequisites
```bash
python 3.9+
```

### Installation
```bash
git clone https://github.com/yourusername/ReallyDeepResearch
cd ReallyDeepResearch
pip install -r requirements.txt
```

### Environment Setup
```bash
cp .env.sample .env
# Add your API keys:
# - OPENAI_API_KEY=your_key
# - SERPER_API_KEY=your_key  
# - DEFAULT_MODEL_NAME=gpt-4
```

### Run
```bash
python app.py
```

Open `http://localhost:7860` → Enter topic → Choose framework → Get comprehensive research report.

## Architecture

```
Topic Input → Framework Selection → Parallel Section Processing
                                          ↓
Complexity Assessment → Query Generation → Web Research → Analysis → Quality Check → Editor
                                          ↓
Self-Healing Loop (if needed) → Final Report Generation → Export (JSON/Markdown)
```

**7 Research Sections** (specific-idea framework):
- Problem/Pain Analysis
- Buyer/Budget Identification  
- ROI Evidence
- Competitive Landscape
- Go-to-Market Channels
- Risk Assessment
- Defensibility Analysis

## Tech Stack

- **Agents**: OpenAI Agents SDK
- **Web Research**: Serper + Playwright
- **UI**: Gradio with async streaming
- **Architecture**: Async/await Python with progress callbacks

---

**Research depth meets execution speed.**