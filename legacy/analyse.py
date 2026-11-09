# coding: utf-8
"""New Zealand General Elections analysis.

Chuan-Zheng Lee <czlee@stanford.edu>
November 2014
"""
import argparse
from electorate import ElectorateStatistics
from config import *

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("year", nargs="?", type=int, default=2014)
actions = parser.add_argument_group("actions")
actions.add_argument("-t", "--total", action="store_true", help="National totals")
actions.add_argument("-e", "--electorate", nargs="+", metavar="ID", type=int, default=[], help="Specific electorate, ID is the electorate number")
actions.add_argument("-r", "--compare-overall", action="store_true", help="National specials comparisons for all years")
actions.add_argument("-s", "--compare-electorate", action="store_true", help="Specials comparisons by electorate")
options = parser.add_argument_group("options")
options.add_argument("-d", "--diffs", action="store_true", help="Use differences instead of ratios in overseas vs specials comparisons")
options.add_argument("-v", "--votes", action="store_true", help="In --total or --electorate, also print raw vote counts")
options.add_argument("-P", "--all-parties", action="store_true", help="Print all parties, not just significant ones")
args = parser.parse_args()

if not any([args.total, args.compare_electorate, args.compare_overall, args.electorate]):
    parser.print_usage()

def print_stats(stats, type="percentage"):
    functions = {
        "percentage": lambda x: "{0:8.2%}".format(getattr(stats, x).percentages[party]),
        "votes"     : lambda x: str(getattr(stats, x).votes[party]).rjust(8),
    }
    attributes = ["ordinary", "ordinary_polling_places", "advance", "domestic", "specials", "specials_domestic", "overseas", "totals"]
    print("Party".ljust(35) + "Ordinary   Polling   Advance  Domestic  Specials  DomSpecs  Overseas     Total")
    parties = args.all_parties and stats.parties or PARTIES[args.year]
    for party in parties:
        print(party[:35].ljust(35) + "  ".join(map(functions[type], attributes)))

def print_comparison(stats, line, type):
    for party in MAJOR_PARTIES:
        overseas = stats.overseas.percentages[party]
        domestic = stats.domestic.percentages[party]
        specials_domestic = stats.specials_domestic.percentages[party]
        specials = stats.specials.percentages[party]
        ordinary = stats.ordinary.percentages[party]
        if type == "ratio":
            line += "     {0:>7.4f}  {1:>7.4f}  {2:>7.4f}  {3:>7.4f}  {4:>7.4f}".format(
                    overseas/domestic, overseas/specials_domestic,
                    overseas/ordinary, specials_domestic/ordinary,
                    specials/ordinary)
        elif type == "diff":
            line += "     {0:>+7.2%}  {1:>+7.2%}  {2:>+7.2%}  {3:>+7.2%}  {4:>+7.2%}".format(
                    overseas-domestic, overseas-specials_domestic,
                    overseas-ordinary, specials_domestic-ordinary,
                    specials-ordinary)
        else:
            raise ValueError("Unrecognized type: {0!r}".format(type))
    print(line)

if args.total:
    total = ElectorateStatistics(args.year, 1)
    for elec_id in range(2, NUM_ELECTORATES[args.year]+1):
        total += ElectorateStatistics(args.year, elec_id)
    print("National statistics for {0:d} election:".format(args.year))
    print_stats(total, "percentage")
    if args.votes:
        print()
        print_stats(total, "votes")

if args.compare_overall or args.compare_electorate:
    print("All {type}s are percentage-to-percentage.\n".format(type=args.diffs and "difference" or "ratio"))
    compare_type = args.diffs and "diff" or "ratio"
    COMPARISONS_HEADER = "     Ovs/Dom   Ovs/DS  Ovs/Ord   DS/Ord Spec/Ord" * len(MAJOR_PARTIES)
    if args.diffs:
        COMPARISONS_HEADER = COMPARISONS_HEADER.replace("/", "-")

    if args.compare_overall:
        print(" " * 27 + "Greens" + " " * 42 + "Labour" + " " * 41 + "National")
        print("Year" + COMPARISONS_HEADER)
        for year in YEARS:
            total = ElectorateStatistics(year, 1)
            for elec_id in range(2, NUM_ELECTORATES[year]+1):
                total += ElectorateStatistics(year, elec_id)
            line = str(year)
            print_comparison(total, line, compare_type)

    if args.compare_electorate:
        print("Election {0:d}".format(args.year) + " " * 31 + "Greens" + " " * 42 + "Labour" + " " * 41 + "National")
        print("Electorate           " + COMPARISONS_HEADER)
        for elec_id in range(1, NUM_ELECTORATES[args.year]+1):
            es = ElectorateStatistics(args.year, elec_id)
            line = es.name.rjust(21)
            print_comparison(es, line, compare_type)

for elec_id in args.electorate:
    es = ElectorateStatistics(args.year, elec_id)
    print("Statistics for electorate {0:d} - {1:s} in {2:d} election".format(es.id, es.name, args.year))
    print_stats(es)
    if args.votes:
        print()
        print_stats(total, "votes")
