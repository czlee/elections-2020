"""Scrapes the 2023 preliminary count from the Wayback Machine's copies of the
Electoral Commission's results pages, and writes tidy CSVs.

The 2023 preliminary XML feed is gone (see NOTES.md), but the Wayback Machine
archived the HTML page for each electorate,
electionresults_2023_preliminary/electorate-details-NN.html. These pages give
electorate totals only: candidate votes, party votes, informals and totals. They
don't give results by voting place.

The pages don't say which party each candidate belongs to, and they use parties'
full names. So candidates and parties are matched against the official 2023 XML
feed (candidates.xml, parties.xml, electorates.xml), which means the CSVs use
the same names as `download.py --election 2023` and the two can be joined.

Raw HTML is saved under <outdir>/raw/ and CSVs are written to <outdir>/
(default: results/2023-prelim).
"""
import gzip
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request

from download import ELECTIONS, INDEPENDENT_PARTY_NO, USER_AGENT, fetch, write_csv

PRELIM_PATH = "electionresults_2023_preliminary/"
OFFICIAL_BASE = ELECTIONS["2023"]
CDX_URL = "https://web.archive.org/cdx/search/cdx"
# The Wayback Machine refuses connections for a while after more than about 15
# requests a minute (checked 10 November 2026: 1 s spacing got blocked after 17).
WAYBACK_DELAY = 5.0  # seconds between requests to the Wayback Machine
RETRY_WAITS = [60, 120, 300, 600]  # seconds to wait before each retry

ROW_RE = re.compile(
    r'<div class="item (?:odd|even)">\s*<span>(.*?)</span>\s*<span class="float-right">(.*?)</span>', re.S)
SUBTOTAL_RE = re.compile(r'<label[^>]*>\s*(.*?)\s*</label>\s*<span class="float-right">(.*?)</span>', re.S)


def get(url):
    """Downloads url, retrying after connection errors and HTTP 429/5xx."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for wait in RETRY_WAITS + [None]:
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if wait is None or (e.code != 429 and e.code < 500):
                raise
            error = e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if wait is None:
                raise
            error = e
        print("{0}; waiting {1} s before retrying".format(error, wait))
        time.sleep(wait)


def number(text):
    return int(text.replace(",", "").strip())


def find_captures():
    """Returns {e_no: (timestamp, original_url)} for the latest successful
    capture of each electorate page, using the Wayback Machine's CDX index."""
    query = urllib.parse.urlencode({
        "url": "electionresults.govt.nz/" + PRELIM_PATH + "electorate-details-*",
        "output": "json", "fl": "timestamp,original", "filter": "statuscode:200",
    })
    rows = json.loads(get(CDX_URL + "?" + query))[1:]  # first row is the header
    captures = {}
    for timestamp, original in rows:
        match = re.search(r"electorate-details-(\d+)\.html$", original)
        if match:
            e_no = str(int(match.group(1)))
            if e_no not in captures or timestamp > captures[e_no][0]:
                captures[e_no] = (timestamp, original)
    return captures


def fetch_capture(timestamp, original, filename, force=False):
    """Downloads the archived page as originally served (the "id_" form, which
    leaves out the Wayback Machine's toolbar) and returns its text."""
    if force or not os.path.exists(filename):
        content = get("https://web.archive.org/web/{0}id_/{1}".format(timestamp, original))
        if content[:2] == b"\x1f\x8b":  # the "id_" form keeps the original gzip encoding
            content = gzip.decompress(content)
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(content)
        print("downloaded {0} (captured {1})".format(os.path.basename(filename), timestamp))
        time.sleep(WAYBACK_DELAY)
    with open(filename, encoding="utf-8") as f:
        return f.read()


def parse_page(text):
    """Parses an electorate details page. Returns a dict with the electorate's
    number and name, how many results were counted, candidate and party votes
    (lists of (name, votes)), and the informals and totals."""
    title = re.search(r"<h2>(.*?)\s*-\s*Preliminary Count</h2>", text, re.S)
    counted = re.search(r"Electorate No\.\s*(\d+)\s*-\s*(\d+)\s*of\s*(\d+)\s*results counted", text)
    table = re.search(r'<table id="partyCandidatesResultsTable">(.*?)</table>', text, re.S)
    assert title and counted and table, "page layout not recognised"

    candidates, parties = [], []
    for row in re.findall(r"<tr>(.*?)</tr>", table.group(1), re.S):
        cells = ROW_RE.findall(row)
        if len(cells) != 2:
            continue  # header, informals or totals row
        for (name, votes), out in zip(cells, (candidates, parties)):
            name = html.unescape(name).strip()
            if name:
                out.append((name, number(votes)))

    subtotals = {}
    for label, value in SUBTOTAL_RE.findall(table.group(1)):
        subtotals.setdefault(label.rstrip(":"), []).append(number(value))
    cand_total, party_total = subtotals["TOTAL"]

    return {
        "e_no": counted.group(1),
        "name": html.unescape(title.group(1)).strip(),
        "results_counted": int(counted.group(2)),
        "total_results": int(counted.group(3)),
        "candidates": candidates,
        "parties": parties,
        "candidate_informals": subtotals["Candidate Informals"][0],
        "party_informals": subtotals["Party Informals"][0],
        "candidate_total": cand_total,
        "party_total": party_total,
    }


def main(outdir, force=False):
    rawdir = os.path.join(outdir, "raw")
    officialdir = os.path.join(rawdir, "official")
    electorates = {e.get("e_no"): e.findtext("electorate_name")
                   for e in fetch(OFFICIAL_BASE, "electorates.xml", officialdir)}
    parties_xml = fetch(OFFICIAL_BASE, "parties.xml", officialdir)
    short_names = {p.findtext("party_name").strip(): p.findtext("short_name") for p in parties_xml}
    party_names = {p.get("p_no"): p.findtext("short_name") for p in parties_xml}
    party_names[INDEPENDENT_PARTY_NO] = "Independent"
    cand_party = {(c.findtext("electorate"), c.findtext("candidate_name")): party_names[c.findtext("party")]
                  for c in fetch(OFFICIAL_BASE, "candidates.xml", officialdir)}

    captures = find_captures()
    print("found captures for {0} of {1} electorates".format(len(captures), len(electorates)))

    cand_rows, party_rows, stats_rows, problems = [], [], [], []
    for e_no in sorted(electorates, key=int):
        name = electorates[e_no]
        if e_no not in captures:
            problems.append("{0} {1}: no capture in the Wayback Machine".format(e_no, name))
            continue
        timestamp, original = captures[e_no]
        page = parse_page(fetch_capture(timestamp, original,
                                        os.path.join(rawdir, "electorate-details-{0:02d}.html".format(int(e_no))),
                                        force))
        assert page["e_no"] == e_no, "electorate number mismatch in page {0}".format(e_no)
        if page["name"] != name:
            problems.append("{0}: page says {1!r}, official feed says {2!r}".format(e_no, page["name"], name))
        if page["results_counted"] != page["total_results"]:
            problems.append("{0} {1}: only {2} of {3} results counted in capture {4}".format(
                e_no, name, page["results_counted"], page["total_results"], timestamp))

        cand_sum = sum(v for _, v in page["candidates"]) + page["candidate_informals"]
        party_sum = sum(v for _, v in page["parties"]) + page["party_informals"]
        if cand_sum != page["candidate_total"] or party_sum != page["party_total"]:
            problems.append("{0} {1}: votes don't add up to the totals (candidates {2} vs {3}, parties {4} vs {5})"
                            .format(e_no, name, cand_sum, page["candidate_total"], party_sum, page["party_total"]))

        for cand, votes in page["candidates"]:
            party = cand_party.get((e_no, cand))
            if party is None:
                problems.append("{0} {1}: candidate {2!r} not in official candidates.xml".format(e_no, name, cand))
            cand_rows.append([e_no, name, cand, party, votes])
        for party, votes in page["parties"]:
            if party not in short_names:
                problems.append("{0} {1}: party {2!r} not in official parties.xml".format(e_no, name, party))
            party_rows.append([e_no, name, short_names.get(party, party), votes])
        stats_rows.append([e_no, name, timestamp, page["results_counted"], page["total_results"],
                           max(page["candidate_total"], page["party_total"]), page["candidate_total"],
                           page["party_total"], page["candidate_informals"], page["party_informals"]])

    key = ["elec_id", "elec_name"]
    write_csv(os.path.join(outdir, "candidate_votes.csv"), key + ["candidate", "party", "votes"], cand_rows)
    write_csv(os.path.join(outdir, "party_votes.csv"), key + ["party", "votes"], party_rows)
    write_csv(os.path.join(outdir, "electorate_stats.csv"),
              key + ["wayback_timestamp", "results_counted", "total_results", "total_votes_cast",
                     "candidate_total", "party_total", "total_candidate_informals", "total_party_informals"],
              stats_rows)

    if problems:
        print("\n{0} problem(s):".format(len(problems)))
        for problem in problems:
            print("  " + problem)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("outdir", nargs="?", default=os.path.join("results", "2023-prelim"),
                        help="output directory (default: %(default)s)")
    parser.add_argument("-f", "--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()
    main(args.outdir, args.force)
