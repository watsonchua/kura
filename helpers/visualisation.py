from datetime import datetime, timedelta
import pandas as pd
from fasthtml.common import Script
import json
from typing import List
from helpers.types import Conversation


def generate_cumulative_chart(conversations: List[Conversation]) -> Script:
    """
    Generate a cumulative word count chart for human messages in conversations.
    Returns a Script element containing the Plotly visualization.
    """
    # Create DataFrame from messages
    messages_data = []
    for conv in conversations:
        for msg in conv.messages:
            if msg.role == "human":
                messages_data.append(
                    {
                        "datetime": pd.to_datetime(
                            msg.created_at.replace("Z", "+00:00")
                        ),
                        "words": len(msg.content.split()),
                    }
                )

    df = pd.DataFrame(messages_data)
    df["week_start"] = df["datetime"].dt.to_period("W-MON").dt.start_time

    # Calculate weekly and cumulative word counts
    weekly_df = df.groupby("week_start")["words"].sum().reset_index()
    weekly_df["cumulative_words"] = weekly_df["words"].cumsum()
    weekly_df["week_start"] = weekly_df["week_start"].dt.strftime("%Y-%m-%d")

    data = json.dumps(
        {
            "data": [
                {
                    "x": weekly_df["week_start"].tolist(),
                    "y": weekly_df["cumulative_words"].tolist(),
                    "type": "scatter",
                    "mode": "lines",
                    "name": "Cumulative Words in Human Messages",
                    "line": {"color": "red"},
                }
            ],
            "layout": {
                "title": "Cumulative Words in Human Messages by Week",
                "xaxis": {"title": "Week Starting"},
                "yaxis": {"title": "Total Words"},
                "showlegend": True,
                "hovermode": "closest",
            },
        }
    )

    return Script(f"var data = {data}; Plotly.newPlot('myDiv', data);")


def generate_messages_per_chat_chart(conversations):
    # Create DataFrame from messages
    messages_data = []
    for conv in conversations:
        for msg in conv.messages:
            if msg.role == "human":
                messages_data.append(
                    {
                        "datetime": pd.to_datetime(
                            msg.created_at.replace("Z", "+00:00")
                        ),
                        "chat_id": conv.chat_id,
                    }
                )

    df = pd.DataFrame(messages_data)
    df["week_start"] = df["datetime"].dt.to_period("W-MON").dt.start_time

    # Calculate messages and unique chats per week
    weekly_messages = df.groupby("week_start").size().reset_index(name="message_count")
    weekly_chats = (
        df.groupby("week_start")["chat_id"].nunique().reset_index(name="chat_count")
    )

    # Merge and calculate average
    weekly_df = pd.merge(weekly_messages, weekly_chats, on="week_start")
    weekly_df["avg_messages"] = weekly_df["message_count"] / weekly_df["chat_count"]
    weekly_df["week_start"] = weekly_df["week_start"].dt.strftime("%Y-%m-%d")

    data = json.dumps(
        {
            "data": [
                {
                    "x": weekly_df["week_start"].tolist(),
                    "y": weekly_df["avg_messages"].tolist(),
                    "type": "scatter",
                    "mode": "lines+markers",
                    "name": "Average Messages per Chat",
                    "line": {"color": "coral"},
                    "marker": {"size": 6},
                }
            ],
            "layout": {
                "title": "Average Number of Messages per Chat by Week",
                "xaxis": {"title": "Week Starting"},
                "yaxis": {"title": "Average Messages per Chat"},
                "showlegend": True,
                "hovermode": "closest",
            },
        }
    )

    return Script(
        f"var messages_data = {data}; Plotly.newPlot('messagesDiv', messages_data);"
    )


def generate_messages_per_week_chart(conversations: List[Conversation]):
    messages_data = []
    for conv in conversations:
        for msg in conv.messages:
            messages_data.append(
                {
                    "datetime": pd.to_datetime(msg.created_at.replace("Z", "+00:00")),
                    "chat_id": conv.chat_id,
                }
            )

    df = pd.DataFrame(messages_data)
    df["week_start"] = df["datetime"].dt.to_period("W-MON").dt.start_time

    # Calculate messages per week
    weekly_messages = df.groupby("week_start").size().reset_index(name="message_count")
    weekly_messages["week_start"] = weekly_messages["week_start"].dt.strftime(
        "%Y-%m-%d"
    )

    data = json.dumps(
        {
            "data": [
                {
                    "x": weekly_messages["week_start"].tolist(),
                    "y": weekly_messages["message_count"].tolist(),
                    "type": "bar",
                    "name": "Messages per Week",
                    "marker": {"color": "coral"},
                }
            ],
            "layout": {
                "title": "Messages per Week",
                "xaxis": {"title": "Week Starting"},
                "yaxis": {"title": "Number of Messages"},
                "showlegend": True,
                "hovermode": "closest",
                "bargap": 0.15,
            },
        }
    )

    return Script(
        f"var messages_per_week = {data}; Plotly.newPlot('messagesPerWeekDiv', messages_per_week.data, messages_per_week.layout);"
    )


def generate_new_chats_per_week_chart(conversations: List[Conversation]):
    # Calculate new chats per week
    chat_starts = pd.DataFrame(
        [
            {
                "datetime": pd.to_datetime(conv.created_at.replace("Z", "+00:00")),
                "chat_id": conv.chat_id,
            }
            for conv in conversations
        ]
    )
    chat_starts["week_start"] = (
        chat_starts["datetime"].dt.to_period("W-MON").dt.start_time
    )
    weekly_chats = (
        chat_starts.groupby("week_start").size().reset_index(name="chat_count")
    )
    weekly_chats["week_start"] = weekly_chats["week_start"].dt.strftime("%Y-%m-%d")

    data = json.dumps(
        {
            "data": [
                {
                    "x": weekly_chats["week_start"].tolist(),
                    "y": weekly_chats["chat_count"].tolist(),
                    "type": "bar",
                    "name": "New Chats per Week",
                    "marker": {"color": "skyblue"},
                }
            ],
            "layout": {
                "title": "New Chats Created per Week",
                "xaxis": {"title": "Week Starting"},
                "yaxis": {"title": "Number of New Chats"},
                "showlegend": True,
                "hovermode": "closest",
                "bargap": 0.15,
            },
        }
    )

    return Script(
        f"var chats_per_week = {data}; Plotly.newPlot('chatsPerWeekDiv', chats_per_week.data, chats_per_week.layout);"
    )
