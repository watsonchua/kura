# Introduction

This is a simple reproduction of the analysis done in the [CLIO](https://www.anthropic.com/research/clio) paper. I've written a [walkthrough of the code](https://ivanleo.com/blog/understanding-user-conversations) that you can read to understand the high level ideas behind CLIO. The code isn't entirely optimised, I wrote it for fun over the weekend so I apologise in advance for any bugs.

## What is CLIO?

CLIO (Claude Language Insights and Observability) is a framework developed by Anthropic that enables privacy-preserving analysis of user conversations at scale. It works by combining language models and clustering techniques to generate meaningful insights while protecting user privacy. The system processes conversations through multiple stages of summarization and clustering, gradually abstracting away personal details while preserving important patterns and trends.

At its core, CLIO uses a two-step approach: first, it employs language models to create privacy-preserving summaries of individual conversations, removing any personally identifiable information (PII). Then, it uses clustering algorithms and hierarchical organization to group similar conversations together, allowing analysts to understand broad usage patterns and user needs without accessing sensitive user data. This methodology achieved a 98.5% success rate in PII removal while maintaining the ability to generate actionable insights from user interactions.

This repo shows a simplified implementation of the CLIO framework. It's not optimised and it's not designed to be used in production. I've also provided a simple FastHTML app to help visualise the clusters and generate your own visualisations.

<img src="https://r2-workers.ivanleomk9297.workers.dev/clio.gif" alt="CLIO Visualisation">

It's just a fun project to understand the ideas behind CLIO.

## Instructions

I've provided two ways to run the code

1. Using the FastHTML app - this allows you to visualise the clusters and generate your own visualisations. I recommend this since it's just nicer to use than a CLI
2. Using the scripts directly - this allows you to run it in a script and get the raw `cluster.json` file generated out

## Using the FastHTML app

1. First, you need to install the dependencies inside the `pyproject.toml` file. I recommend doing so in a virtual environment.

```bash
uv venv
source .venv/bin/activate
uv sync
```

2. Then just run the `app.py` file

```bash
python app.py
```

3. Then you want to just click the `Start Analysis` button and wait for the clusters to be generated. Depending on the number of conversations you have this could take a while. For ~800 conversations, it took around 1.5 minutes to generate the clusters with a semaphore of 50.

Once you've done so, I recommend just taking cluster.json and throwing it into something like Claude to ask more questions about the clusters.

## Using the Scripts

> Before running the scripts, make sure that you've downloaded your claude chats. A guide on how to do so can be found [here](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-ai-data).

1. First, you need to install the dependencies inside the `pyproject.toml` file. I recommend doing so in a virtual environment.

```
uv venv
source .venv/bin/activate
uv sync
```

2. Once you've done so, make sure that the claude chats are saved in a file called `conversations.json` and that you've set a `GOOGLE_API_KEY` in your shell. If not you'll have to configure it by doing

```python
import google.generativeai as genai

genai.configure(api_key=<api key goes here>)
```

Once you've done so, just run `main.py` to generate the initial clusters. Make sure to modify the following variables to your liking:

```py
SUMMARIES_PER_CLUSTER = 20 # This determines the number of summaries we want on average per cluster
CHILD_CLUSTERS_PER_CLUSTER = 10 # This determines the number of clusters we want on average to have per higher level cluster
MAX_FINAL_CLUSTERS = 10 # This represents the maximum number of clusters we want to have at the end of the process
```

Once you've done so, just run `main.py` to generate the initial clusters. This will create a file called `clusters.json` which contains the initial clusters.

```python
python main.py
```

3. Once you've done so, you can run `visualise.py` to visualise the clusters. This will create a print out that looks like a tree.

```python
python visualise.py
```

You'll see an output that looks like this:

```bash
Clusters
├── Improve text, code, and generate diverse content
│   Description: Users requested assistance with improving text and code, and generating diverse content and marketing materials.  Tasks included rewriting, debugging, analysis, and content creation across
│   various domains.
│   Contains 308 conversations
│   ├── Rewrite and improve text and code
│   │   Description: Users requested assistance with improving and rewriting various types of text, including articles, marketing materials, technical documents, and code.  Tasks ranged from enhancing clarity
│   │   and conciseness to debugging code and analyzing data.
│   │   Contains 183 conversations
│   │   ├── Rewrite articles and marketing copy related to AI and databases
│   │   │   Description: Users requested assistance rewriting articles and marketing materials about AI, databases, and related technologies.  The requests involved tasks such as improving clarity, style,
│   │   │   conciseness, and creating outlines and summaries.
│   │   │   Contains 28 conversations
│   │   ├── Rewrite or improve text
│   │   │   Description: Users requested assistance with revising, rewriting, or improving existing text, including paragraphs, articles, summaries, and other written content.  Tasks ranged from enhancing
│   │   │   clarity and conciseness to translating languages and improving writing style.
│   │   │   Contains 24 conversations
│   │   ├── Improve or create AI-related documents
│   │   │   Description: Users requested assistance with various tasks related to improving or creating documents about AI, including summarization, rewriting, clarification, and the addition of definitions.
│   │   │   These tasks focused on improving clarity,
... more clusters here
```

This is a tree representation of the clusters. The clusters are grouped by their parent cluster. The clusters are sorted by the number of conversations they contain. You can then use this tree to understand the conversations and the patterns they contain.
