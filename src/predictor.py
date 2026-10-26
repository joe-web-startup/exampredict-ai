def calculate_priority(topic_counts):
    priorities = {}

    max_count = max(topic_counts.values())

    for topic, count in topic_counts.items():
        score = round((count / max_count) * 100)
        priorities[topic] = score

    return priorities
