# coding: utf-8
"""New Zealand General Elections analysis.
Electorate statistics class.

Chuan-Zheng Lee <czlee@stanford.edu>
November 2014
"""

import download
import csv
import itertools

class VoteCounts(object):
    """Vote counts for each party."""

    def __init__(self, stats, votes):
        self.stats = stats
        self._votes = votes

    @property
    def parties(self):
        return self.stats.parties

    @property
    def votes(self):
        return dict(zip(self.parties, self._votes))

    @property
    def percentages(self):
        total_votes = sum(self._votes) or 0.1
        percentages = [float(votes)/total_votes for votes in self._votes]
        return dict(zip(self.parties, percentages))

    def iter_votes(self):
        return zip(self.parties, self._votes)

    def iter_percentages(self):
        total_votes = sum(self._votes) or 0.1
        for party, votes in self.iter_votes():
            yield party, float(votes)/total_votes

    def __add__(self, other):
        """Add votes party-by-party"""
        assert(isinstance(other, VoteCounts))
        assert(self.parties == other.parties)
        votes = list(map(sum, list(zip(self._votes, other._votes))))
        return VoteCounts(self.stats, votes)

    def __eq__(self, other):
        return self.parties == other.parties and self._votes == other._votes

    def __ne__(self, other):
        return self.parties != other.parties or self._votes != other._votes

    @staticmethod
    def blank(stats):
        return VoteCounts(stats, [0] * len(stats.parties))

class PollingPlaceResults(VoteCounts):
    """Vote counts for a particular polling place."""

    def __init__(self, electorate, id_no, suburb, location, votes):
        """'suburb' and 'name' are strings.
        'votes' is a list. Information about parties is not stored here, it's
        just kept in 'electorate'."""
        VoteCounts.__init__(self, electorate, votes)
        self.id = id_no
        self.suburb = suburb
        self.location = location


class GeneralStatistics(object):
    """Statistics by vote categories (ordinary, special, etc.)"""

    BASIC_FIELDS = ["ordinary_polling_places", "ordinary_advance", "special_advance",
        "less_than_6", "special_on", "overseas", "party_only", "totals"]

    def __init__(self, parties, **kwargs):
        self.parties = parties
        for key in self.BASIC_FIELDS:
            kwargs.setdefault(key, VoteCounts.blank(self))
        for key, value in kwargs.items():
            if key in self.BASIC_FIELDS:
                if isinstance(value, VoteCounts):
                    setattr(self, key, value)
                else:
                    raise TypeError("'{0!r}' should be a VoteCounts object".format(key))
            else:
                raise TypeError("__init__() got an unexpected keyword argument '{0!r}'".format(key))

    @property
    def ordinary(self):
        """All ordinary votes."""
        return self.ordinary_polling_places + self.ordinary_advance

    @property
    def advance(self):
        """All advance votes."""
        return self.ordinary_advance + self.special_advance

    @property
    def specials(self):
        """All special votes."""
        return self.special_advance + self.special_on + self.overseas + self.party_only

    @property
    def specials_domestic(self):
        """Special votes except overseas votes."""
        return self.special_advance + self.special_on + self.party_only

    @property
    def domestic(self):
        """All domestic votes."""
        return self.ordinary + self.specials_domestic

    def __add__(self, other):
        """Add vote counts field-wise."""
        assert(self.parties == other.parties)
        kwargs = dict()
        for field in self.BASIC_FIELDS:
            kwargs[field] = getattr(self, field) + getattr(other, field)
        result = GeneralStatistics(self.parties, **kwargs)
        return result


class ElectorateStatistics(GeneralStatistics):
    """Statistics associated with an electorate, by polling place."""

    SPECIAL_ROW_NAMES = {
        "voting places where less than 6 votes were taken": "less_than_6",
        "polling places where less than 6 votes were taken": "less_than_6",
        "ordinary votes before polling day": "ordinary_advance",
        "special votes before polling day": "special_advance",
        "special votes on polling day": "special_on",
        "overseas special votes including defence force": "overseas",
        "votes allowed for party only": "party_only",
        "special votes allowed for party only": "party_only",
    }

    SPECIAL_FIELDS = list(set(SPECIAL_ROW_NAMES.values())) + ["totals"]

    def __init__(self, year, electorate, init=True):
        # don't call parent constructor
        self.year = year
        self.electorate = electorate

        if init:
            self.download_files()
            self.parse_party_file()

    def _warn(self, message):
        print("Warning: [{0:d}, {1:d}] {2:s}".format(self.year, self.electorate, message))

    def download_files(self):
        self.filename_party = download.download_polling_place_results(self.year, self.electorate, vote_type="party", quiet=True)

    def parse_party_file(self):
        csvfile = open(self.filename_party)
        reader = csv.reader(csvfile)

        if self.year == 1999:
            # Electorate name and party column headings
            line = next(reader)
            name, elec_id = line[0].rsplit(None, 4)[0:2]
            name = name.title()
            END_COLUMNS = 4

        else:
            try:
                next(reader) # Header line
            except:
                print(self.filename_party)
                raise

            # Electorate name line
            line = next(reader)
            name, elec_id = line[0].rsplit(None, 1)

            # Party column headings
            # First two columns are polling place names, last two are totals
            line = next(reader)
            END_COLUMNS = 2

        self.parties = [party for party in line[2:len(line)-END_COLUMNS]]
        self.name = name
        self.id = int(elec_id)

        # Polling places
        self.pprs = list()
        suburb = None
        for num, line in enumerate(reader, start=1):

            if not any(line): # skip blank lines
                continue
            if not any(line[2:]): # skip lines without vote counts
                continue

            suburb = line[0] or suburb
            location = line[1]
            votes = list(map(int, line[2:len(line)-END_COLUMNS]))
            if len(votes) == 0:
                votes = [0] * len(self.parties)

            if location.lower().strip().rsplit(None, 1) == [self.name.lower(), "total"]:
                self.totals = VoteCounts(self, votes)
                break # assume totals link is always last

            elif location.lower().split("-")[0].strip() in self.SPECIAL_ROW_NAMES:
                row_label = location.lower().split("-")[0].strip()
                existing = getattr(self, self.SPECIAL_ROW_NAMES[row_label], VoteCounts.blank(self))
                this_row = VoteCounts(self, votes)
                setattr(self, self.SPECIAL_ROW_NAMES[row_label], existing + this_row)

            else:
                ppr = PollingPlaceResults(self, num, suburb, location, votes)
                self.pprs.append(ppr)

        if self.year == 1999: # 1999 doesn't have these figures
            self.less_than_6 = VoteCounts.blank(self)
            self.party_only = VoteCounts.blank(self)

        # Check we filled all the special row cases
        for name in self.SPECIAL_FIELDS:
            if not hasattr(self, name):
                self._warn("No row found for {0!r}".format(name))
                setattr(self, name, VoteCounts(self, [0] * len(self.parties)))

        # Sanity check
        if self.ordinary + self.specials != self.totals:
            self._warn("Totals don't match")
            print((self.ordinary + self.specials).votes)
            print(self.totals.votes)

        csvfile.close()

    @property
    def ordinary_polling_places(self):
        """All ordinary votes at polling places."""
        return sum(self.pprs, self.less_than_6)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("year", type=int)
    parser.add_argument("electorate", nargs="?", type=int, default=None)
    args = parser.parse_args()

    es = ElectorateStatistics(args.year, args.electorate)

    print("Electorate {0:d}: {1:s}".format(es.id, es.name))
    attributes = ["ordinary", "ordinary_polling_places", "advance", "specials", "specials_domestic", "overseas"]
    print("Party".ljust(35) + "Ordinary   Polling   Advance  Specials Dom Specs  Overseas")
    for party in es.parties:
        print(party.ljust(35) + "  ".join([str(getattr(es, x).votes[party]).rjust(8) for x in attributes]))
