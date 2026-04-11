---
name: reading-guide
description: >
  Structured learning navigator for blog posts and articles. Produces an OKR-based
  learning plan with gap analysis, a knowledge tree, and learning path — all saved
  as Markdown + multiple presentation-ready SVG visualizations. Use this skill whenever
  the user shares a blog post, article, tutorial, or technical write-up and wants to
  understand what they need to learn, what prerequisites they're missing, or how to build
  a study plan around it. Also trigger when the user says things like "帮我拆解一下这篇文章",
  "我该怎么学这个", "reading guide for this post", "what do I need to know before reading this",
  "帮我做个学习计划", "这篇文章的知识体系是什么", or provides a URL/text and asks
  to "break it down", "make a study plan", "figure out what I'm missing".
---

# Reading Guide — Structured Learning Navigator

You help users turn a blog post or article into a structured, actionable learning plan.
The core problem this skill solves: when someone reads a technical article, they often
don't realize what prerequisite knowledge they're missing, what they should focus on,
or how to systematically close the gap between where they are and where the article
assumes they should be.

## Overall Workflow

```
Input (article) → Comprehension → Interactive Gap Analysis → Structured Output → Diagram Draft → User Approval → SVGs
```

1. **Comprehend the article** — extract its core concepts, structure, and implicit prerequisites
2. **Define learning objectives** — OKR-style: Goal → Key Results → Prerequisites
3. **Interactive gap analysis** — ask the user targeted questions to assess their current level
4. **Build learning path** — structured, prioritized list of what to study
5. **Generate Markdown report** — the structured text output
6. **Draft diagram blueprints** — write a `diagram-drafts.md` describing every SVG's content and layout in plain text. Present to the user for review. **Do NOT draw SVGs until the user approves the drafts.**
7. **Generate SVGs via subagents** — once drafts are approved, spawn one subagent per
   diagram to draw the SVGs. Each subagent receives only its own diagram description and
   invokes the svg-creator skill independently. **Never draw SVGs directly in the main
   session** — loading svg-creator's detailed instructions into the main context pollutes
   it and degrades instruction-following for the overall workflow. Launch all subagents
   in parallel for speed.
8. **Save everything** — into `./article-title/` directory

## Step 1: Comprehend the Article

Accept input in any of these forms:
- **URL**: fetch with WebFetch and extract content
- **Pasted text**: work with it directly
- **File path**: read with the Read tool (supports .md, .pdf, .html, .txt)

Extract the following from the article:

- **Main thesis**: what is the article fundamentally about? (1-2 sentences)
- **Core concepts**: the key ideas, frameworks, or techniques introduced (list of 5-15)
- **Concept relationships**: how concepts depend on each other (A requires understanding B)
- **Implicit prerequisites**: knowledge the author assumes you already have but doesn't explain
- **Difficulty layers**: group concepts into tiers (foundational → intermediate → advanced)

Present a brief summary to the user:
> "This article is about [thesis]. It covers [N] core concepts across [M] difficulty levels.
> I've identified [K] implicit prerequisites the author assumes you know. Let me ask you
> a few questions to figure out where to focus your study plan."

## Step 2: Define Learning Objectives (OKR-Style)

Structure the learning goals using OKR format:

### Objective (O)
What does mastering this article enable the user to do? Frame it as an actionable outcome,
not "understand X" but "be able to apply X to solve Y".

### Key Results (KR)
3-5 measurable indicators that the user has achieved the objective. Good key results are
specific and verifiable:
- "Can explain [concept] to a colleague without referencing the article"
- "Can implement [technique] in a toy project"
- "Can identify when [pattern] applies vs. when it doesn't"

### Prerequisites (P)
Knowledge or skills needed before even starting. Derived from the implicit prerequisites
identified in Step 1. Categorize each as:
- **Hard prerequisite**: must know this first, otherwise the article won't make sense
- **Soft prerequisite**: helpful context, but can be picked up along the way

## Step 3: Interactive Gap Analysis

This is the most important step — and the one that requires real conversation with the user.

Use `AskUserQuestion` to assess the user's current level against each prerequisite and
core concept cluster. The goal is to build a picture of what they already know vs. what
they need to learn.

**How to ask good questions:**

- Don't ask "do you know X?" — people overestimate their knowledge
- Instead, ask scenario-based or application-based questions that reveal actual understanding
- Group related concepts to keep the number of questions manageable (3-5 rounds max)
- Offer concrete options that map to different familiarity levels

**Example question structure:**

Round 1 — Prerequisites:
> "The article assumes familiarity with [topic A] and [topic B]. Which best describes you?"
> - "I've used A and B in projects before" (strong foundation)
> - "I've read about them but never applied them" (conceptual only)
> - "These are new to me" (need to learn from scratch)

Round 2 — Core concepts:
> "The article's main technique builds on [concept C]. How familiar are you?"
> - "I could explain it to someone else" (solid)
> - "I've seen it mentioned but couldn't explain it" (surface level)
> - "First time hearing about it" (new)

Round 3 — Adjacent knowledge:
> "The article also touches on [D] and [E] as applications. Any experience with those areas?"

After the Q&A, synthesize the user's profile:
- **Strengths**: concepts they already grasp well
- **Gaps**: concepts they need to learn, ranked by importance and dependency order
- **Stretch goals**: advanced topics they might explore after mastering the basics

## Step 4: Build the Learning Path

Based on the gap analysis, create a structured learning path. Organize it as modules
with clear dependencies:

```
Module 1: [Foundation] — prerequisite concepts the user is missing
  ├── Topic 1.1: ...
  ├── Topic 1.2: ...
  └── Estimated effort: X hours

Module 2: [Core] — the article's main concepts
  ├── Topic 2.1: ...  (depends on 1.1)
  ├── Topic 2.2: ...  (depends on 1.2, 2.1)
  └── Estimated effort: X hours

Module 3: [Application] — putting it into practice
  ├── ...
  └── Estimated effort: X hours

Module 4: [Extension] — advanced topics for going deeper (optional)
  ├── ...
  └── Estimated effort: X hours
```

For each topic, include:
- What to learn (1-2 sentences)
- Why it matters for understanding the article
- Suggested resources (if known) or search terms

## Step 5: Generate Outputs

### 5.1 Markdown Report

Save as `./article-title/report.md` with this structure:

```markdown
# Reading Guide: [Article Title]

> Source: [URL or file path]
> Generated: [date]

## Article Summary
[2-3 paragraph summary of the article's main points]

## Learning Objectives

### Objective
[The actionable outcome]

### Key Results
1. [KR1]
2. [KR2]
3. [KR3]

### Prerequisites
| Prerequisite | Type | Your Level | Priority |
|---|---|---|---|
| [concept] | Hard/Soft | Strong/Weak/New | High/Medium/Low |

## Gap Analysis
### Your Strengths
- ...
### Key Gaps
- ...

## Learning Path

### Module 1: [Name] (estimated X hours)
#### 1.1 [Topic]
- **What**: ...
- **Why**: ...
- **Resources**: ...

[...more modules...]

## Quick Reference: Core Concepts
[A concise glossary of the article's key terms and concepts]
```

### 5.2 Diagram Blueprint — Draft Before Drawing

**This is a hard requirement: never jump straight to SVG.** Before drawing any diagram,
write a `diagram-drafts.md` file that describes every diagram's content, layout, and
text in plain Markdown. Save it alongside `report.md`. Present it to the user for review.

Only after the user approves (or modifies) the drafts should you proceed to draw SVGs.
This separates **content decisions** (what goes in each diagram) from **styling decisions**
(how it looks), so mistakes in structure are caught early and cheaply.

Each draft entry should include:
- **Filename**: e.g., `00-overview.svg`
- **Title**: the exact title text that will appear on the diagram
- **Layout**: the spatial arrangement (left-to-right flow, top-down tree, parallel columns, etc.)
- **Elements**: every box/node listed with its exact text content
- **Connections**: every arrow, with source → target and optional label
- **Notes**: any special styling (which elements are highlighted, grayed out, dashed, etc.)

Example draft format:
```markdown
### 00-overview.svg
**Title:** "Seeing Like an Agent: How We Design Tools in Claude Code"
**Layout:** Central thesis at top → 5 concept clusters below in a row
**Elements:**
1. [Thesis] 站在模型视角设计 Tool
2. [Cluster] Tool 设计框架 — 粒度平衡：一个万能 vs 五十个细碎
3. [Cluster] AskUserQuestion 迭代 — 三次尝试：失败→失败→成功
...
**Connections:**
- Thesis → each Cluster (solid arrows)
**Notes:** Each cluster uses a distinct color that carries through to detail diagrams
```

### 5.3 SVG Visualizations — Design Principles

These diagrams are meant to be **shown to others** (presentations, team shares, study
groups). Every diagram must follow these principles:

#### Content Principles

1. **Objective, not subjective.** Diagrams should describe the article's content as-is.
   Don't inject "you already know this" or "your gap" into structural diagrams like the
   overview or knowledge tree. Personalized assessment belongs only in the gap analysis
   diagram and the Markdown report.

2. **Use the article's own title.** The overview diagram's title should be the article's
   actual title, not a generic label like "文章结构总览". Readers should immediately know
   which article this diagram is about.

3. **Let the diagram speak for itself.** Don't add meta-annotations like "虚线 = ..."
   legends unless the meaning is genuinely unclear. If you need a legend to explain your
   visual language, the visual language is too complex. Annotations should be content, not
   instructions about how to read the diagram.

4. **Don't force hierarchies that don't exist.** Not every diagram needs a single root
   node. If the content is naturally a flat list, a timeline, or parallel tracks, use that
   structure. A tree with a forced root (like "知识树详情 · 用户交互设计") that adds no
   information just wastes space. Use the most natural structure for the content:
   - **Timeline/flow**: for iterative processes (e.g., three attempts at a design)
   - **Tree**: for genuine parent-child concept hierarchies
   - **Parallel columns**: for independent modules at the same level
   - **Comparison**: for before/after or old/new contrasts

5. **Integrate explanations into the diagram.** If there's a key insight or takeaway,
   don't put it in a separate box at the bottom — annotate it directly on the relevant
   elements. For example, instead of a "关键洞察" box that says "模型视角 is the entry
   point", label the "模型视角" node itself with "→ 入口". Information should be where
   the reader's eyes already are.

6. **Be specific, not abstract.** Each element should contain enough text that a reader
   understands what it means without reading the full article. "粒度" alone means nothing;
   "Tool 粒度：一个万能 vs 五十个细碎 → 找中间地带" tells the story.

#### Visual / Styling Principles

7. **One diagram, one message.** Each SVG communicates exactly one idea. Max 7-9 elements
   at the same level; if more, split into multiple diagrams.

8. **Generous whitespace.** At least 60px between elements. Padding inside containers 40px+.

9. **Legible at a glance.** A viewer should get the message within 5 seconds.

10. **Consistent fonts.** English text always uses the `.label-en` class (Comic Sans MS).
    Chinese text uses Ma Shan Zheng. Never mix — if a box contains both "Tool" and "设计",
    both should be styled correctly via their respective font classes. Check every text
    element before finalizing.

11. **Verify all arrows.** After writing SVG, check every arrow's coordinates: does it
    actually connect the right elements? Do start/end points land near the shape edges?
    Never apply `filter` to arrows — it makes thin lines disappear.

12. **Check text boundaries.** All text and elements must be within the SVG's viewBox.
    Left-aligned text needs enough x-offset (50px+ from left edge). Long text should be
    broken into multiple `<text>` elements rather than overflowing.

### 5.4 The SVG Series

The exact number of SVGs depends on the article's complexity, but follow this structure:

#### Layer 1: Overview (always 1 diagram)

**`00-overview.svg`** — Article Overview
- **Title = the article's actual title** (e.g., "Seeing Like an Agent: How We Design Tools
  in Claude Code"), not a generic label
- Shows the article's top-level structure: 3-6 major concept clusters
- Arrows show the reading/dependency flow between clusters
- Each cluster box has a descriptive title + 1-2 line summary of what's inside
- Color-code each cluster (these colors carry through to detail diagrams)

#### Layer 2: Detail Diagrams (N diagrams, one per major topic)

**`01-[topic-name].svg`**, **`02-[topic-name].svg`**, etc.

Each detail diagram zooms into one major topic from the overview. Choose the layout that
fits the content naturally:

- **For iterative/sequential content** (e.g., "three attempts at designing AskUserQuestion"):
  use a left-to-right timeline flow. Title = the topic's own name (e.g., "AskUserQuestion
  的三次迭代"), not "知识树详情 · XXX"
- **For hierarchical content** (e.g., "design principles and their relationships"):
  use a tree, but only if the hierarchy is real. Annotate relationships directly on nodes
  (e.g., label a node "入口" or "方法" instead of explaining in a separate box)
- **For comparison content** (e.g., "RAG vs Agent-driven search"):
  use a two-column or before→after layout. Integrate the "why" into the transition arrow
  or into the elements themselves, not in a separate explanation box

General rules for all detail diagrams:
- Max 2 levels deep per diagram
- Title should directly describe what the diagram shows, in the most natural phrasing
- No forced root nodes — if the content doesn't have a single parent, don't invent one
- Distribute explanatory text across elements rather than collecting it into a summary box

#### Layer 3: Learning Path (1 diagram, or 2 if complex)

**`0N-learning-path.svg`** — Study Sequence
- Left-to-right or top-to-bottom flow showing the modules in study order
- Each module is a container box with its topics listed inside
- Arrows between modules show dependencies
- Annotate with estimated time per module
- **Show all content objectively** — the learning path represents the article's full
  knowledge structure. Don't gray out or skip topics based on the user's current level;
  that personalization belongs in the report and gap analysis diagram only
- If more than 4 modules, split into two diagrams

#### Layer 4: Gap Analysis (1 diagram)

**`0N-gap-analysis.svg`** — Current vs. Target
- This is the **only diagram** where personal assessment appears
- A clean visual comparison: the user's current level vs. what the article requires
- Layout: horizontal bar chart style or parallel columns
- Keep to 5-8 dimensions max
- Use warm colors (orange/red) for large gaps, cool colors (green/blue) for small gaps
- **Check that all text fits within the SVG viewBox** — especially left-side labels.
  Use x=60 or greater for left-aligned text, and keep labels short (max 6 characters
  per line, use line breaks for longer labels)

### 5.5 Naming Convention & File Organization

```
./article-title/
├── report.md
├── diagram-drafts.md        ← blueprint for all diagrams (user reviews before SVGs)
├── svg/
│   ├── 00-overview.svg
│   ├── 01-[topic-name].svg
│   ├── 02-[topic-name].svg
│   ├── ...
│   ├── 0N-learning-path.svg
│   └── 0N-gap-analysis.svg
```

Use a sanitized version of the article title for the directory name (lowercase, hyphens
instead of spaces, no special characters, max 50 chars).

Number prefixes ensure diagrams sort in presentation order. Use descriptive topic names
in filenames (e.g., `01-askuserquestion-iterations.svg`, `02-rag-vs-agent-search.svg`).

## Language Handling

- Match the user's language — if they write in Chinese, produce Chinese outputs
- If the article is in English but the user writes in Chinese, produce outputs in Chinese
  with English technical terms preserved
- SVG diagrams should use the same language as the report

## Tips for Quality

- The gap analysis conversation is the key differentiator — invest time in asking good
  questions rather than rushing to output. A generic learning plan is useless; a personalized
  one is invaluable.
- When estimating effort, be realistic. "1-2 hours" for a topic means focused study time,
  not glancing at a blog post.
- The learning path should have a clear "critical path" — what's the minimum the user
  needs to learn to understand the article? Mark optional/extension topics as such.
- Concept maps are more useful when they show *why* concepts are related, not just that
  they are. Use labeled edges.
- When splitting diagrams, always make sure each standalone SVG is self-explanatory —
  include a title and brief context annotation so it makes sense even without the others.
- **Never add meta-descriptions** ("虚线表示..." / "this diagram shows...") — if the
  diagram needs explaining, simplify it.
- **Separate objective content from personal assessment.** The overview, knowledge tree,
  and learning path should be useful to anyone reading the article. Only the gap analysis
  diagram and the Markdown report should contain user-specific assessments.
