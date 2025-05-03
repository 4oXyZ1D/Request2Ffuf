import argparse
import re
from urllib.parse import urlparse, parse_qs, urlencode, unquote

def parse_raw_http_request(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    method, path, _ = lines[0].split()
    headers = {}
    body = ""
    collecting_body = False

    for line in lines[1:]:
        if line.strip() == "":
            collecting_body = True
            continue
        if collecting_body:
            body += line + "\n"
        else:
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()

    return method, path, headers, body.strip()

def extract_dollar_fuzz_params(data):
    return set(re.findall(r'\$(\w+)\$', data))

def parse_fuzz_targets(fuzz_arg, auto_params=None):
    fuzz_targets = {"params": {}, "headers": {}}
    auto_params = auto_params or {"params": set(), "headers": set()}
    
    # Add auto-detected params
    for param in auto_params["params"]:
        fuzz_targets["params"][param] = "FUZZ"
    
    # Process manual entries
    entries = fuzz_arg.split(",") if fuzz_arg else []
    for entry in entries:
        if entry.startswith("param:"):
            key, val = entry[len("param:"):].split("=", 1)
            fuzz_targets["params"][key] = val
        elif entry.startswith("header:"):
            key, val = entry[len("header:"):].split("=", 1)
            fuzz_targets["headers"][key] = val
    
    return fuzz_targets

def extract_fuzz_slots(fuzz_targets):
    slots = set()
    for mapping in (fuzz_targets["params"], fuzz_targets["headers"]):
        for fuzz_val in mapping.values():
            slots.update(re.findall(r'FUZZ\d*', fuzz_val))
    return sorted(slots)

def apply_param_fuzzing(params_dict, fuzz_map):
    for key, fuzz_value in fuzz_map.items():
        if key in params_dict:
            params_dict[key] = [fuzz_value]
    return params_dict

def generate_ffuf_command(method, path, headers, body, fuzz_targets, wordlists, extra_flags):
    host = headers.get("Host", "localhost")
    scheme = "https" if headers.get("X-Forwarded-Proto") == "https" or ":443" in host else "http"
    
    # Process $params$ in path and body
    path = re.sub(r'\$(\w+)\$', r'FUZZ', unquote(path))
    parsed_url = urlparse(path)
    
    # Process query params
    query = parse_qs(parsed_url.query)
    for param in fuzz_targets["params"]:
        if param in query:
            query[param] = [fuzz_targets["params"][param]]
    fuzzed_query = urlencode(query, doseq=True)
    
    # Build URL
    url = f"{scheme}://{host}{parsed_url.path}?{fuzzed_query}".rstrip("?")
    
    # Headers
    header_args = []
    for key, val in headers.items():
        if key in fuzz_targets["headers"]:
            val = fuzz_targets["headers"][key]
        if key.lower() != "host":
            header_args.append(f'-H "{key}: {val}"')
    header_str = " ".join(header_args)
    
    # Body processing
    body_str = ""
    if method.upper() == "POST":
        body = re.sub(r'\$(\w+)\$', r'FUZZ', unquote(body))
        post_data = parse_qs(body)
        for param in fuzz_targets["params"]:
            if param in post_data:
                post_data[param] = [fuzz_targets["params"][param]]
        body_str = f"-d '{urlencode(post_data, doseq=True)}'"
    
    # Wordlists
    slots = extract_fuzz_slots(fuzz_targets)
    wordlist_args = [f'-w {wordlists.get(slot.lower(), "wordlist.txt")}:{slot}' for slot in slots]
    wordlist_str = " ".join(wordlist_args)
    
    # Build final command
    base_cmd = f'ffuf -X {method} -u "{url}" {body_str} {wordlist_str} {header_str} {extra_flags}'
    return re.sub(r'\s+', ' ', base_cmd).strip()

def main():
    parser = argparse.ArgumentParser(description="Convert raw HTTP request to ffuf command")
    parser.add_argument("file", help="Path to raw HTTP request file")
    parser.add_argument("-f", "--fuzz", default="", help="Fuzz targets, e.g. param:user=FUZZ1,header:Authorization=FUZZ2")
    parser.add_argument("-w", "--wordlist", default="wordlist.txt", help="Default wordlist")
    
    for i in range(1, 10):
        parser.add_argument(f"-w{i}", help=f"Wordlist for FUZZ{i}")
    
    parser.add_argument("--mc", help="Match status codes")
    parser.add_argument("--fc", help="Filter status codes")
    parser.add_argument("--fs", help="Filter response size")
    
    args = parser.parse_args()
    
    # Auto-detect $params$ in request
    method, path, headers, body = parse_raw_http_request(args.file)
    auto_params = {
        "params": extract_dollar_fuzz_params(path + body)
    }
    
    # Wordlists configuration
    wordlists = {"fuzz": args.wordlist}
    for i in range(1, 10):
        wl = getattr(args, f"w{i}")
        if wl: wordlists[f"fuzz{i}"] = wl
    
    # Extra flags
    extra_flags = ""
    if args.mc: extra_flags += f"-mc {args.mc} "
    if args.fc: extra_flags += f"-fc {args.fc} "
    if args.fs: extra_flags += f"-fs {args.fs} "
    
    fuzz_targets = parse_fuzz_targets(args.fuzz, auto_params)
    cmd = generate_ffuf_command(method, path, headers, body, fuzz_targets, wordlists, extra_flags)
    
    print("\nGenerated ffuf command:\n")
    print(cmd)

if __name__ == "__main__":
    main()
