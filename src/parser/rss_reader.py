from argparse import ArgumentParser
from typing import List, Optional, Sequence
import requests
import xml.etree.ElementTree as ET
import json as json_module
import html

class UnhandledException(Exception):
    pass

def rss_parser(
    xml: str,
    limit: Optional[int] = None,
    json: bool = False,
) -> List[str]:

    root = ET.fromstring(xml)

    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    channel = root.find("channel")
    if channel is None:
        raise UnhandledException("Channel was not found")

    def get_text(parent, tag):
        element = parent.find(tag)
        if element is not None and element.text:
            text = html.unescape(element.text.strip())
            return " ".join(text.split())
        return None

    channel_data = {}

    for tag in [
        "title",
        "link",
        "description",
        "lastBuildDate",
        "pubDate",
        "language",
        "managingEditor",
    ]:
        value = get_text(channel, tag)
        if value is not None:
            channel_data[tag] = value

    categories = [
        html.unescape(cat.text.strip())
        for cat in channel.findall("category")
        if cat.text
    ]
    if categories:
        channel_data["category"] = categories

    raw_items = channel.findall("item")
    items_data = []

    for item in raw_items:
        item_dict = {}

        title = get_text(item, "title")
        description = get_text(item, "description")

        #Skip only if both are missing
        if title is None and description is None:
            continue

        for tag in ["title", "author", "pubDate", "link", "description"]:
            value = get_text(item, tag)
            if value is not None:
                item_dict[tag] = value

        item_categories = [
            html.unescape(cat.text.strip())
            for cat in item.findall("category")
            if cat.text
        ]
        if item_categories:
            item_dict["category"] = item_categories

        items_data.append(item_dict)
    print(len(items_data))
    if limit is not None:
        if limit <= 0:
            items_data = []
        else:
            items_data = items_data[:limit]
    print(len(items_data))
    if json:
        result = dict(channel_data)

        if items_data:
            result["items"] = items_data

        return [
            json_module.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )
        ]

    output = []

    if "title" in channel_data:
        output.append(f"Feed: {channel_data['title']}")
    if "link" in channel_data:
        output.append(f"Link: {channel_data['link']}")
    if "lastBuildDate" in channel_data:
        output.append(f"Last Build Date: {channel_data['lastBuildDate']}")
    if "pubDate" in channel_data:
        output.append(f"Publish Date: {channel_data['pubDate']}")
    if "language" in channel_data:
        output.append(f"Language: {channel_data['language']}")
    if "category" in channel_data:
        output.append(f"Categories: {', '.join(channel_data['category'])}")
    if "managingEditor" in channel_data:
        output.append(f"Editor: {channel_data['managingEditor']}")
    if "description" in channel_data:
        output.append(f"Description: {channel_data['description']}")

    if items_data:
        output.append("")

    for index, item in enumerate(items_data):

        if "title" in item:
            output.append(f"Title: {item['title']}")
        if "author" in item:
            output.append(f"Author: {item['author']}")
        if "pubDate" in item:
            output.append(f"Published: {item['pubDate']}")
        if "link" in item:
            output.append(f"Link: {item['link']}")
        if "category" in item:
            output.append(f"Categories: {', '.join(item['category'])}")

        if "description" in item:
            output.append("")
            output.append(item["description"])

        if index < len(items_data) - 1:
            output.append("")

    return output


def main(argv: Optional[Sequence] = None):

    parser = ArgumentParser(
        prog="rss_reader",
        description="Pure Python command-line RSS reader.",
    )

    parser.add_argument("source", help="RSS URL", type=str)
    parser.add_argument(
        "--json",
        help="Print result as JSON in stdout",
        action="store_true",
    )
    parser.add_argument(
        "--limit",
        help="Limit news topics if this parameter provided",
        type=int,
    )

    args = parser.parse_args(argv)

    try:
        response = requests.get(
            args.source,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        response.raise_for_status()
    except requests.RequestException as e:
        raise UnhandledException(f"Network error: {e}")

    xml_content = response.text

    try:
        print("\n".join(rss_parser(xml_content, args.limit, args.json)))
        return 0
    except Exception as e:
        raise UnhandledException(e)


if __name__ == "__main__":
    main()
