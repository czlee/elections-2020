# Notes

Working notes for this repo: facts we've established about the Electoral
Commission's results website, and (later) plans. Dates are when something was
checked; the site changes, so re-check anything old before relying on it.

## Facts

### Site access (checked 8–9 November 2026)

- **Everything except the XML feeds is blocked to scripts.** Cloudflare returns
  a 403 "Sorry, you have been blocked" page (about 4.8–6 KB of HTML) for the
  homepage, the `statistics/` pages and the per-voting-place CSVs, on both
  `www.electionresults.govt.nz` and `archive.electionresults.govt.nz`. Checked
  for 2002, 2014, 2017, 2020 and 2023. Claude's web-fetch tool, which runs from a
  different network, was blocked too, so it isn't specific to one IP address.
  Leaving out the User-Agent doesn't help.
- **The `/xml/` paths are reachable** with a custom User-Agent (we use
  `Elections Analysis`) or curl's default. **Python's default User-Agent
  (`Python-urllib/3.x`) gets a 403 even on `/xml/`**, so scripts must set one.
- **Use the main host, not the archive host.**
  `https://www.electionresults.govt.nz/electionresults_YYYY/xml/` serves files
  *and* directory listings. On `archive.electionresults.govt.nz` the same paths
  serve individual files but listings return 403 (a 1.3 KB origin error, not the
  Cloudflare page).
- Courtesy delay between requests: 0.4 s.

### Which years have XML

| Election | Base URL | Contents |
|---|---|---|
| 2026 | `https://www.electionresults.govt.nz/electionresults_2026_preliminary/xml/` | preliminary count. The live feed was at `https://electionresults.govt.nz/xml/` on 8 November 2026 and has since moved. |
| 2023 | `https://www.electionresults.govt.nz/electionresults_2023/xml/` | official results (`updated="2024-11-10"`) |
| 2020 | `https://www.electionresults.govt.nz/electionresults_2020/xml/` | official results (`updated="2020-11-20"`) |
| 2017 | `https://www.electionresults.govt.nz/electionresults_2017/xml/` | official results (`updated="2017-10-07"`), 71 electorates, same layout (checked 10 November 2026) |
| 2014, 2011, 2008 | none: `electionresults_YYYY/xml/election.xml` gives a 404 | CSVs only, which are blocked |

No 2023 preliminary feed found: `electionresults_2023_preliminary` gives a 404
on both hosts.

### XML layout (the same for 2017, 2020, 2023 and 2026)

- Top level: `election.xml`, `electorates.xml`, `parties.xml`,
  `candidates.xml`, `statistics.xml`, `votingplaces.xml`.
  - `election.xml`: national statistics and party totals and seats.
    `total_special_votes` and `total_minimal_votes` are national figures only.
    In official results (2023) `total_special_votes` is 0.
  - `electorates.xml`: `e_no` → electorate name.
  - `parties.xml`: `p_no` → abbreviation, short name, full name, whether
    registered.
  - `candidates.xml`: `c_no` → name, electorate, party, list number. **Party
    `0` means independent and isn't listed in `parties.xml`.** Electorate `0`
    means list-only.
  - `votingplaces.xml`: `vp_id`, `vp_e_no` (the place's home electorate),
    address, lat/lon. It has **no** `vp_no` and doesn't say which electorates'
    votes a place took, so voting-place file names can't be built from it. Use
    the directory listings.
- `eNN/eNN.xml` (two-digit electorate number): electorate statistics (votes
  cast, party informals, candidate informals, etc.), plus party and candidate
  votes keyed by `p_no` / `c_no`. Attributes include `final` and `updated`.
- `eNN/votingplaces/NN-VVPPP.xml`: one file per voting place per electorate
  whose votes it took. `NN` = the electorate, `VV` = the voting place's home
  electorate, `PPP` = `vp_no`. For example, `01-47017` is a place in electorate
  47 that took Auckland Central votes. Contains ballot papers issued,
  informals, and party and candidate votes. `vp_no` 200+ and `vp_no` 0 entries
  exist (e.g. `01-23000`, with 0 ballots issued); what they mean is unknown.
  Numbering has gaps.

### Deriving per-electorate special votes

- **Voting-place files contain ordinary votes only.** Check: for 2026 Auckland
  Central (preliminary, 69 files), the voting-place sums equal `e01.xml`
  exactly for every party and candidate, and party informals match too
  (100 = 100).
- So in an official-results feed, **specials per electorate (by party, by
  candidate) = `eNN.xml` totals − the sum of that electorate's voting-place
  files.** For 2023 Auckland Central (61 files): 35,463 votes cast vs 23,488
  ballot papers issued at voting places; 12,046 special party votes and 11,227
  special candidate votes. Not yet checked against a published 2023 special-vote
  figure.
- The XML gives **one** special-vote total. Unlike the CSVs it doesn't split
  specials into overseas, before polling day, on polling day and party-only
  (see `SPECIAL_ROW_NAMES` in `electorate.py`).
- Size: 2023 has about 10,655 voting-place results (`total_voting_places_counted`),
  about 72 minutes at 0.4 s per request. 2026 preliminary has 9,389.

### Quirks in the 2026 preliminary data (8 November 2026 snapshot)

- In every electorate, exactly one of (party valid + party informals) and
  (candidate valid + candidate informals) equals `total_votes_cast`, and the
  other is short by up to 401 votes (4,279 in total). This is probably ballots
  with one half left blank. So `total_votes_cast` = the larger of the two.
- The electorates' `total_votes_cast` values sum to 2,433,679, but
  `election.xml` says 2,432,403 (a difference of 1,276). Not explained.
- Party votes summed over electorates match `election.xml`'s party totals
  exactly.

### Electorates

- 2023: 72 electorates. 2026: 71 electorates, some renamed or new (e.g.
  Glendene is electorate 11 in 2026). No 2023 → 2026 correspondence table has
  been looked for yet.

## Code status

- `download.py`: downloads the top-level and `eNN/eNN.xml` files for one
  feed into `<outdir>/raw/` and writes `candidate_votes.csv`,
  `party_votes.csv`, `electorate_stats.csv` and `national_stats.csv`. Pick a
  feed with `--election` (`2026-prelim` (default), `2023`, `2020`, `2017`) or
  `--base URL`; the output defaults to `results/<election>`. It doesn't fetch
  voting-place files. Checked 10 November 2026: it runs for 2017, 2020 and 2023,
  and party votes summed over electorates match `election.xml` for each.
- `legacy/` (`download.py`, `electorate.py`, `analyse.py`): the original CSV-based code (1999
  onwards). Can't currently be run because the CSVs are blocked. Expected to be
  rewritten or replaced with XML-based code. Keep them in case the CSVs become
  reachable again, since the CSVs are the only source for pre-2017 elections and
  for the breakdown of special votes by category.

## Plans

None yet. This section will hold the plan for the 2026 special-votes
projection and any refactoring.
