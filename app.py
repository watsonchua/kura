from fasthtml.common import (
    fast_app,
    Div,
    Titled,
    Link,
    Html,
    serve,
    H2,
    Form,
    Input,
    H1,
    Style,
    H3,
    Request,
    Script,
)
from helpers.types import Cluster
from helpers.conversation import load_conversations
from helpers.visualisation import (
    generate_cumulative_chart,
    generate_messages_per_chat_chart,
    generate_messages_per_week_chart,
    generate_new_chats_per_week_chart,
)
import os
from main import generate_clusters
import asyncio

app, rt = fast_app(
    hdrs=(
        Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js"),
        Link(
            rel="stylesheet",
            href="https://cdnjs.cloudflare.com/ajax/libs/flexboxgrid/6.3.1/flexboxgrid.min.css",
            type="text/css",
        ),
    )
)


center_style = (
    Style("""
            body { 
                font-family: system-ui, sans-serif;
                max-width: 800px;
                margin: 2rem auto;
                padding: 0 1rem;
            }
            form {
                display: flex;
                flex-direction: column;
                gap: 1rem;
                padding: 2rem;
                border-radius: 8px;
                border: 1px solid #ccc;
            }
            input[type="submit"] {
                background: #0066ff;
                color: white;
                padding: 0.5rem 1rem;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            input[type="submit"]:hover {
                background: #0052cc;
            }
            .missing-file {
                background: #fff3cd;
                border: 1px solid #ffeeba;
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 4px;
            }
            .loading {
                text-align: center;
                padding: 2rem;
                background: #f8f9fa;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin: 2rem auto;
                max-width: 400px;
            }
            .loading-spinner {
                display: inline-block;
                width: 50px;
                height: 50px;
                border: 3px solid #f3f3f3;
                border-top: 3px solid #0066ff;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 1rem;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
"""),
)


@rt("/analyze")
async def analyze():
    return Div(
        center_style,
        H1("Analyzing Your Chats", style="text-align: center;"),
        Div(
            Div(cls="loading-spinner"),
            Div(
                "Please wait while we analyze your conversations...",
                style="color: #666;",
            ),
            cls="loading",
        ),
        Script("""
            async function startAnalysis() {
                try {
                    await fetch('/start-analysis');
                    window.location.href = '/';
                } catch (error) {
                    console.error('Analysis failed:', error);
                }
            }
            startAnalysis();
        """),
    )


@rt("/start-analysis")
async def start_analysis():
    await generate_clusters()
    return "Analysis complete"


@rt("/")
async def index():
    if not os.path.exists("conversations.json"):
        return Div(
            center_style,
            H1("Chat Analysis Setup"),
            Div(
                "Please download your Anthropic chat history first", cls="missing-file"
            ),
        )

    conversations = load_conversations("conversations.json")
    clusters = None

    if not os.path.exists("clusters.json"):
        return Div(
            center_style,
            H1("Chat Analysis Setup"),
            Form(
                Input(
                    type="submit",
                    value="Start Analysis",
                    style="width: 200px; margin: 0 auto;",
                ),
                method="POST",
                action="/analyze",
                style="text-align: center;",
            ),
        )

    with open("clusters.json", "r") as f:
        clusters = [Cluster.model_validate_json(line) for line in f]

    # Create tree structure for visualization
    def build_tree(cluster):
        # Create node for current cluster
        node_id = f"{cluster.name.lower()}-{cluster.count}".replace(" ", "-")

        # Find children first to determine if we need expand button
        children = [c for c in clusters if c.parent_id == cluster.id]

        inner_elements = [
            H2(cluster.name, style="font-size: 1.2rem; margin: 0.5rem 0;"),
            Div(f"Description: {cluster.description}", style="font-size: 0.9rem;"),
            Div(
                f"Contains {cluster.count} conversations",
                style="font-size: 0.9rem;",
            ),
        ]

        # Only add expand button if there are children
        if children:
            inner_elements.append(
                Div(
                    "Expand",
                    cls="expand-btn",
                    id=f"btn-{node_id}",
                    style="""
                        font-size: 0.8rem;
                        padding: 0.2rem 0.5rem;
                        background: #eee;
                        border-radius: 4px;
                        cursor: pointer;
                        display: inline-block;
                        margin-top: 0.5rem;
                    """,
                    onclick=f"""
                        const children = document.getElementById('children-{node_id}');
                        if (children) {{
                            if (children.style.display === 'none') {{
                                children.style.display = 'block';
                                this.textContent = 'Collapse';
                            }} else {{
                                children.style.display = 'none';
                                this.textContent = 'Expand';
                            }}
                        }}
                        event.stopPropagation();
                    """,
                )
            )

        node = Div(
            Div(
                *inner_elements,
                style="text-align: left;",
            ),
            cls="cluster-node",
            id=node_id,
            style="padding: 1rem; border: 1px solid #ccc; margin: 1rem; border-radius: 4px;",
        )

        # Add children recursively if they exist
        if children:
            children_div = Div(
                *[build_tree(child) for child in children],
                style="margin-left: 2rem; display: none;",  # Hidden by default
                cls="children",
                id=f"children-{node_id}",
            )
            return Div(node, children_div)
        return node

    # Find root clusters and build tree
    root_clusters = [c for c in clusters if not c.parent_id]
    cluster_tree = Div(
        H3(
            "Cluster Analysis",
            style="width: 100%; text-align: center; margin-bottom: 2rem;",
        ),
        Div(
            Div(
                *[build_tree(root) for root in root_clusters],
                style="background: white; color: black; padding: 2rem; max-height: 800px; overflow-y: auto;",
            ),
        ),
    )

    return Titled(
        "Chat Analysis",
        Div(
            Div(
                Div(
                    cls="box",
                    id="myDiv",
                ),
                cls="col-xs-6 center-xs",
            ),
            Div(
                Div(
                    cls="box",
                    id="chatsPerWeekDiv",
                ),
                cls="col-xs-6 center-xs",
            ),
            Div(
                Div(
                    cls="box",
                    id="messagesDiv",
                ),
                cls="col-xs-6 center-xs",
            ),
            Div(
                Div(
                    cls="box",
                    id="messagesPerWeekDiv",
                ),
                cls="col-xs-6 center-xs",
            ),
            cls="row center-xs",
            style="color: #fff;",
        ),
        Style("""
            .cluster-node {
                background: #f5f5f5;
            }
            .cluster-node:hover {
                background: #e5e5e5;
            }
        """),
        cluster_tree,
        generate_cumulative_chart(conversations),
        generate_messages_per_chat_chart(conversations),
        generate_new_chats_per_week_chart(conversations),
        generate_messages_per_week_chart(conversations),
        Div(
            style="padding: 40px;",
        ),
    )


serve()
