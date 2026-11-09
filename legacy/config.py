# coding: utf-8
YEARS = [1999, 2002, 2005, 2008, 2011, 2014, 2017, 2020]

NUM_ELECTORATES = {2002: 69, 2005: 69, 2008: 70, 2011: 70, 2014: 71, 2017: 71, 2020: 72}

PARTIES = dict()
PARTIES[2020] = [
    "ACT New Zealand",
    "Advance NZ",
    "Green Party",
    "Labour Party",
    "Māori Party",
    "National Party",
    "New Conservative",
    "New Zealand First Party",
    "The Opportunities Party (TOP)"]
PARTIES[2017] = [
    u"ACT New Zealand",
    u"Green Party",
    u"Labour Party",
    u"Māori Party",
    u"National Party",
    u"New Zealand First Party",
    u"The Opportunities Party (TOP)"]
PARTIES[2014] = [
    u"ACT New Zealand",
    u"Conservative",
    u"Green Party",
    u"Internet MANA",
    u"Labour Party",
    u"Māori Party",
    u"National Party",
    u"New Zealand First Party",
    u"United Future"]
PARTIES[2011] = [
    u"ACT New Zealand",
    u"Conservative Party",
    u"Green Party",
    u"Mana",
    u"Labour Party",
    u"Māori Party",
    u"National Party",
    u"New Zealand First Party",
    u"United Future"]
PARTIES[2008] = [
    u"ACT New Zealand",
    u"Green Party",
    u"Labour Party",
    u"Maori Party",
    u"National Party",
    u"New Zealand First Party",
    u"United Future"]

PARTIES[2005] = [
    u"ACT New Zealand",
    u"Green Party",
    u"Jim Anderton's Progressive",
    u"Labour Party",
    u"M�ori Party",
    u"National Party",
    u"New Zealand First Party",
    u"United Future New Zealand"]
PARTIES[2002] = [
    u"ACT",
    u"Green Party",
    u"Labour Party",
    u"National Party",
    u"NZ First",
    u"Progressive Coalition",
    u"United Future"]
PARTIES[1999] = [
    u"ACT New Zealand",
    u"Alliance",
    u"Green Party",
    u"Labour Party",
    u"National Party",
    u"New Zealand First Party",
    u"United NZ"]

MAJOR_PARTIES = [
    u"Green Party",
    u"Labour Party",
    u"National Party",
]

# The files for 1999 are, annoyingly, named by electorate.
ELECTORATE_NAMES_1999 = [
    u"Albany",
    u"Aoraki",
    u"Auckland Central",
    u"Banks Peninsula",
    u"Bay of Plenty",
    u"Christchurch Central",
    u"Christchurch East",
    u"Clutha-Southland",
    u"Coromandel",
    u"Dunedin North",
    u"Dunedin South",
    u"East Coast",
    u"Epsom",
    u"Hamilton East",
    u"Hamilton West",
    u"Hunua",
    u"Hutt South",
    u"Ilam",
    u"Invercargill",
    u"Kaikoura",
    u"Karapiro",
    u"Mana",
    u"Mangere",
    u"Manukau East",
    u"Manurewa",
    u"Maungakiekie",
    u"Mt Albert",
    u"Mt Roskill",
    u"Napier",
    u"Nelson",
    u"New Plymouth",
    u"North Shore",
    u"Northcote",
    u"Northland",
    u"Ohariu-Belmont",
    u"Otago",
    u"Otaki",
    u"Pakuranga",
    u"Palmerston North",
    u"Port Waikato",
    u"Rakaia",
    u"Rangitikei",
    u"Rimutaka",
    u"Rodney",
    u"Rongotai",
    u"Rotorua",
    u"Tamaki",
    u"Taranaki-King Country",
    u"Taupo",
    u"Tauranga",
    u"Te Atatu",
    u"Titirangi",
    u"Tukituki",
    u"Waimakariri",
    u"Wairarapa",
    u"Waitakere",
    u"Wellington Central",
    u"West Coast-Tasman",
    u"Whanganui",
    u"Whangarei",
    u"Wigram",
    u"Hauraki",
    u"Ikaroa-Rawhiti",
    u"Te Tai Hauauru",
    u"Te Tai Tokerau",
    u"Te Tai Tonga",
    u"Waiariki",
]
NUM_ELECTORATES[1999] = len(ELECTORATE_NAMES_1999)