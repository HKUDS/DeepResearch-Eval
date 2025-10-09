import copy
import os
import re
import json
import argparse
from tqdm import tqdm
from typing import Dict, Any

from Atools import SearchAgent, check_factual


def normalize_url(raw_key: str) -> str:
    """
    Input may be like "https://a.com/x](https://a.com/x)" or contain markdown fragments,
    normalize to a usable http(s) URL.
    Strategy: prioritize the last URL fragment starting with http(s)://.
    """
    # Match http or https links, try to exclude extra ) or ] at the end
    candidates = re.findall(r"https?://[^\s)\]]+", raw_key)
    if not candidates:
        return raw_key.strip()
    # Take the last one, usually the real URL
    return candidates[-1]

def process_obj(agent: SearchAgent, data: Dict[str, Any], provider: str) -> Dict[str, Any]:
    """
    Process a single JSON object (like { url_key: {"contexts": [...], ...}, ... }).
    Return an object with normalized URL as key and 'md' field added.
    """
    normalized_data: Dict[str, Any] = {}
    for raw_url, payload in tqdm(data.items()):
        url = normalize_url(raw_url)
        payload_copy: Dict[str, Any] = copy.deepcopy(payload)
        try:
            page_content = agent.scrape(url, provider=provider)
        except Exception as e:
            page_content = f"__SCRAPE_ERROR__: {e}"
        payload_copy['md'] = page_content
        normalized_data[url] = payload_copy

    return normalized_data

def process_record_judge(agent: SearchAgent, obj: Dict[str, Any], provider: str):
    """
    Process a record (like { raw_url: {"contexts": [...], ...} }):
    - Normalize URL
    - Scrape md
    - Call check_factual for each context, output {url, context, label}
    Return: List[Dict]
    """
    if not isinstance(obj, Dict) or len(obj) != 1:
        return [{
            "__PARSE_ERROR__": "Each line must contain exactly one key (url).",
            "__raw__": obj
        }]
    (raw_url, payload), = obj.items()
    url = normalize_url(raw_url)
    contexts = []
    if isinstance(payload, dict):
        contexts = payload.get("contexts", [])
    try:
        page_content = agent.scrape(url, provider=provider)
    except Exception as e:
        page_content = f"__SCRAPE_ERROR__: {e}"
    results = []
    for c in contexts:
        if not isinstance(c, str):
            continue
        try:
            label = check_factual(c, page_content)
        except Exception as e:
            label = f"__ERROR__: {e}"
        results.append({"url": url, "context": c, "label": label})
    return results

def main():
    parser = argparse.ArgumentParser(description="Compare contexts with scraped pages and summarize -1/0/1.")
    parser.add_argument("--inputpath", required=True, help="Input .jsonl file path, process line by line")
    parser.add_argument("--outputpath", required=True, help="Output file path or directory (will generate same-named .out.jsonl or .judge.jsonl in directory)")
    parser.add_argument("--provider", choices=["firecrawl", "jina"], default="jina", help="Scraping provider")
    parser.add_argument("--limit", type=int, default=3, help="SearchAgent.num_limit_pages")
    parser.add_argument("--task", choices=["scrape", "judge"], default="judge", help="scrape only scrapes and outputs objects with md; judge directly outputs judgment results")
    args = parser.parse_args()

    input_abs = os.path.abspath(args.inputpath)
    output_abs = os.path.abspath(args.outputpath)

    agent = SearchAgent(num_limit_pages=args.limit)

    # Only support .jsonl streaming processing
    if not (input_abs.lower().endswith(".jsonl") and os.path.isfile(input_abs)):
        raise ValueError("--inputpath must be an existing .jsonl file")

    # Determine output path: if given a directory, create same-named .out.jsonl or .judge.jsonl in it
    if os.path.isdir(output_abs):
        base = os.path.splitext(os.path.basename(input_abs))[0]
        suffix = "judge.jsonl" if args.task == "judge" else "out.jsonl"
        out_jsonl = os.path.join(output_abs, f"{base}.{suffix}")
    else:
        # Treat as file path
        os.makedirs(os.path.dirname(output_abs) or ".", exist_ok=True)
        out_jsonl = output_abs

    count = 0
    with open(input_abs, "r", encoding="utf-8") as fin, \
         open(out_jsonl, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                fout.write(json.dumps({"__PARSE_ERROR__": str(e), "__raw__": line}, ensure_ascii=False) + "\n")
                continue
            if args.task == "scrape":
                result = process_obj(agent, obj, provider=args.provider)
                fout.write(json.dumps(result, ensure_ascii=False) + "\n")
            else:
                results = process_record_judge(agent, obj, provider=args.provider)
                for r in results:
                    fout.write(json.dumps(r, ensure_ascii=False) + "\n")
            count += 1
    print(f"Saved JSONL: {out_jsonl} (lines: {count})")
    return


if __name__ == "__main__":
    main()


