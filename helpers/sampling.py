import numpy as np


def get_contrastive_examples(
    cluster_id: int,
    grouped_clusters: dict[int, list[dict]],
    desired_count: int = 10,
) -> dict[int, list[dict]]:
    other_clusters = [c for c in grouped_clusters.keys() if c != cluster_id]

    if len(other_clusters) == 0:
        raise ValueError("No other clusters to compare against")

    # Get all examples from other clusters
    all_examples = []
    for cluster in other_clusters:
        all_examples.extend(grouped_clusters[cluster])

    # If we don't have enough examples, use replacement
    if len(all_examples) < desired_count:
        return all_examples

    # Otherwise sample without replacement
    return list(np.random.choice(all_examples, size=desired_count, replace=False))
