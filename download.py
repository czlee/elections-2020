"""Downloads electorate-level results from the Electoral Commission's XML feed
and writes tidy CSVs.

XML feeds exist for 2017, 2020 and 2023 (official results) and 2026
(preliminary results); all share the same layout. Earlier elections have no XML
feed, only CSVs (see legacy/). Choose a feed with --election, or give any feed's
URL with --base. Raw XML is saved under <outdir>/raw/ and tidy CSVs are written
to <outdir>/ (default: results/<election>).

Per-voting-place files are not downloaded.
"""
import csv
import os
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

# Known XML feeds. Use the www host, not archive.electionresults.govt.nz (see NOTES.md).
ELECTIONS = {
    "2026-prelim": "https://www.electionresults.govt.nz/electionresults_2026_preliminary/xml/",
    "2023": "https://www.electionresults.govt.nz/electionresults_2023/xml/",
    "2020": "https://www.electionresults.govt.nz/electionresults_2020/xml/",
    "2017": "https://www.electionresults.govt.nz/electionresults_2017/xml/",
}
DEFAULT_ELECTION = "2026-prelim"
# Python's default User-Agent is blocked by the server, so always send this one.
USER_AGENT = "Elections Analysis"
DELAY = 0.4  # seconds between requests, as a courtesy to the server
TOP_LEVEL_FILES = ["election.xml", "electorates.xml", "parties.xml", "candidates.xml", "statistics.xml"]
INDEPENDENT_PARTY_NO = "0"  # used in candidates.xml, but absent from parties.xml

ELECTORATE_STATS = ["total_voting_places", "total_voting_places_counted", "percent_voting_places_counted",
                    "total_votes_cast", "percent_votes_cast", "total_party_informals",
                    "total_candidate_informals", "total_candidates"]


def fetch(base, path, rawdir, force=False):
    """Downloads base + path to rawdir/path, unless it already exists, and
    returns the parsed XML root element."""
    filename = os.path.join(rawdir, path)
    if force or not os.path.exists(filename):
        request = urllib.request.Request(base + path, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request) as response:
            content = response.read()
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "wb") as f:
            f.write(content)
        print("downloaded {0}".format(path))
        time.sleep(DELAY)
    return ET.parse(filename).getroot()


def write_csv(filename, header, rows):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print("wrote {0} ({1} rows)".format(filename, len(rows)))


def main(base, outdir, force=False):
    rawdir = os.path.join(outdir, "raw")
    roots = {name: fetch(base, name, rawdir, force) for name in TOP_LEVEL_FILES}

    electorates = {e.get("e_no"): e.findtext("electorate_name") for e in roots["electorates.xml"]}
    parties = {p.get("p_no"): p.findtext("short_name") for p in roots["parties.xml"]}
    parties[INDEPENDENT_PARTY_NO] = "Independent"
    candidates = {c.get("c_no"): (c.findtext("candidate_name"), c.findtext("party"), c.findtext("electorate"))
                  for c in roots["candidates.xml"]}

    cand_rows, party_rows, stats_rows = [], [], []
    for e_no in sorted(electorates, key=int):
        name = electorates[e_no]
        root = fetch(base, "e{0:02d}/e{0:02d}.xml".format(int(e_no)), rawdir, force)
        assert root.get("e_no") == e_no, "e_no mismatch in electorate {0}".format(e_no)

        stats = root.find("statistics")
        stats_rows.append([e_no, name, root.get("final"), root.get("updated")] +
                          [stats.findtext(s) for s in ELECTORATE_STATS])

        for party in root.find("partyvotes"):
            p_no = party.get("p_no")
            party_rows.append([e_no, name, parties.get(p_no, "p_no " + p_no), int(party.findtext("votes"))])

        for cand in root.find("candidatevotes"):
            c_no = cand.get("c_no")
            cand_name, p_no, cand_elec = candidates[c_no]
            assert cand_elec == e_no, "candidate {0} listed in electorate {1}, not {2}".format(c_no, cand_elec, e_no)
            cand_rows.append([e_no, name, cand_name, parties.get(p_no, "p_no " + p_no), int(cand.findtext("votes"))])

    key = ["elec_id", "elec_name"]
    write_csv(os.path.join(outdir, "candidate_votes.csv"), key + ["candidate", "party", "votes"], cand_rows)
    write_csv(os.path.join(outdir, "party_votes.csv"), key + ["party", "votes"], party_rows)
    write_csv(os.path.join(outdir, "electorate_stats.csv"), key + ["final", "updated"] + ELECTORATE_STATS, stats_rows)

    election = roots["election.xml"]
    national = [[child.tag, child.text] for child in election.find("statistics")]
    write_csv(os.path.join(outdir, "national_stats.csv"), ["statistic", "value"],
              [["updated", election.get("updated")]] + national)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("outdir", nargs="?", help="output directory (default: results/<election>)")
    parser.add_argument("-e", "--election", choices=ELECTIONS, default=DEFAULT_ELECTION,
                        help="which election's feed to download (default: %(default)s)")
    parser.add_argument("--base", help="base URL of the XML feed, overriding --election")
    parser.add_argument("-f", "--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()
    base = args.base or ELECTIONS[args.election]
    outdir = args.outdir or os.path.join("results", args.election)
    main(base, outdir, args.force)
