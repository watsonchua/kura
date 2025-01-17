# Index

## What is Kura?

Kura is a library that aims to help you make sense of user data. By using language models to iteratively summarise and cluster conversations, it provides a modular and flexible way for you to understand broad high level trends in your user base.

### Why is it useful?

Traditional approaches like BERTopic are incredibly useful for understanding the underlying structure of your data. However, they are not always the best tool for the job. Kura implements a modular approach that integrates language models at each step of the process to help provide structure and insights.

Key Features

- A modular approach that allows you to fully customise the summarisation, clustering and embedding models used
- A CLI tool that makes it easy to get started and visualise your data clusters
- Extendable API that allows you to extract additional metadata from conversations and clusters in your own analysis.

Here is the rough road map of what I'm working on, contributions are welcome!

- [ ] Support heatmap visualisation
- [ ] Support ChatGPT conversations
- [ ] Support hooks that can be ran on individual conversations and clusters to extract metadata
- [ ] Show how we can use Kura with other configurations such as UMAp instead of KMeans

It's currently under active development and I'm working on adding more features to it but the eventual goal is to make it a very modular tool that you can use to understand general trends in your user base. If you face any issues or have any suggestions, please feel free to open an issue or a PR.

## Technical Ideas

It's built with the same ideas as [CLIO](https://www.anthropic.com/research/clio) but open-sourced so that you can try it on your own data. I've written a [walkthrough of the code](https://ivanleo.com/blog/understanding-user-conversations) that you can read to understand the high level ideas behind CLIO.

I've also recorded a technical deep dive into what Kura is and the ideas behind it if you'd rather watch than read.

<iframe width="560" height="315" src="https://www.youtube.com/embed/TPOP_jDiSVE?si=uvTond4LUwJGOn4F" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>

## Getting Started

To get started with Kura, you'll need to install our python package.

```bash
pip install kura
```

Once you've done so, you can run your first clustering job either with our CLI tool that provides a react frontend with the associated visualisations or you can use the Python package to do it programatically.

Either way, make sure that you've defined a `GOOGLE_API_KEY` environment variable to use the Google Gemini API. We ship by default with the `gemini-1.5-flash` model which works reasonbly well for this task.

### Using the CLI

You can boot up our CLI tool with the following command:

```bash
> kura
INFO:     Started server process [41539]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

This will start a local FastAPI server that you can interact with to upload your data and visualise the clusters. It roughly takes ~1 min for ~1000 conversations with a semaphore of around 50 requests at any given time. If you have higher concurrency, you can increase the semaphore to speed up the process.

### Using the Python API

You can also use the Python API to do the same thing.

```python
from kura import Kura
from asyncio import run

kura = Kura()
kura.load_conversations_from_file("conversations.json")
run(kura.cluster_conversations())
```

We assume here that you have a `conversations.json` file in your current working directory which contains data in the format of the Claude Conversation Dump. You can see a guide on how to export your conversation history from the Claude app [here](https://support.anthropic.com/en/articles/9450526-how-can-i-export-my-claude-ai-data).

Support for other formats is coming soon. Until then you can also manually set conversations in the `Kura` class by doing

```python
kura = Kura()
kura.conversations = # conversations go here
```

All you need is to pass in a list of `Conversation` objects which you can import from `from kura.types import Conversation`.
