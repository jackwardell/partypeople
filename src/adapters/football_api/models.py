from __future__ import annotations

from typing import List
from typing import Optional
from typing import TypedDict


class _FixturesResponseFixturePeriods(TypedDict):
    first: Optional[int]
    second: Optional[int]


class _FixturesResponseFixtureStatus(TypedDict):
    elapsed: Optional[int]
    long: str
    short: str


class _FixturesResponseFixtureVenue(TypedDict):
    id: Optional[int]
    city: str
    name: str


class _FixturesResponseFixture(TypedDict):
    id: str
    date: str
    periods: _FixturesResponseFixturePeriods
    referee: Optional[str]
    status: _FixturesResponseFixtureStatus
    timestamp: int
    timezone: str
    venue: _FixturesResponseFixtureVenue


class _FixturesResponseGoals(TypedDict):
    away: Optional[int]
    home: Optional[int]


class _FixturesFixturesResponseLeague(TypedDict):
    id: int
    country: str
    flag: Optional[str]
    logo: str
    name: str
    round: str
    season: int


class _FixturesResponseScorePattern(TypedDict):
    away: Optional[int]
    home: Optional[int]


class _FixturesResponseScore(TypedDict):
    extratime: _FixturesResponseScorePattern
    fulltime: _FixturesResponseScorePattern
    halftime: _FixturesResponseScorePattern
    penalty: _FixturesResponseScorePattern


class _FixturesResponseTeamPattern(TypedDict):
    id: int
    logo: str
    name: str
    winner: Optional[bool]


class _FixturesResponseTeams(TypedDict):
    home: _FixturesResponseTeamPattern
    away: _FixturesResponseTeamPattern


class GETFixturesResponse(TypedDict):
    fixture: _FixturesResponseFixture
    goals: _FixturesResponseGoals
    league: _FixturesFixturesResponseLeague
    score: _FixturesResponseScore
    teams: _FixturesResponseTeams


class _TeamInformationResponseTeam(TypedDict):
    id: int
    name: str
    code: str
    country: str
    founded: int
    national: bool
    logo: bool


class _TeamInformationResponseVenue(TypedDict):
    id: int
    name: str
    address: str
    city: str
    capacity: int
    surface: str
    image: str


class GETTeamInformationResponse(TypedDict):
    team: _TeamInformationResponseTeam
    venue: _TeamInformationResponseVenue


class _PlayerResponsePlayerBirth(TypedDict):
    date: str
    place: str
    country: str


class _PlayerResponsePlayer(TypedDict):
    id: int
    name: str
    firstname: str
    lastname: str
    age: int
    birth: _PlayerResponsePlayerBirth
    nationality: str
    height: str
    weight: str
    injured: bool
    photo: str


class _PlayerResponseStatisticsTeam(TypedDict):
    id: str
    name: str
    logo: str


class _PlayerResponseStatisticsLeague(TypedDict):
    id: Optional[int]
    name: str
    country: str
    logo: str
    flag: Optional[str]
    season: int


class _PlayerResponseStatisticsGames(TypedDict):
    appearences: int
    lineups: int
    minutes: int
    number: Optional[int]
    position: str
    rating: Optional[str]
    captain: bool


class _PlayerResponseStatisticsSubstitutes(TypedDict):
    in_: int
    out: int
    bench: int


class _PlayerResponseStatisticsShots(TypedDict):
    total: Optional[int]
    on: Optional[int]


class _PlayerResponseStatisticsShotsGoals(TypedDict):
    total: int
    conceded: int
    assists: Optional[int]
    saves: Optional[int]


class _PlayerResponseStatisticsShotsPasses(TypedDict):
    total: Optional[int]
    key: Optional[int]
    accuracy: Optional[int]


class _PlayerResponseStatisticsShotsTackles(TypedDict):
    total: Optional[int]
    blocks: Optional[int]
    interceptions: Optional[int]


class _PlayerResponseStatisticsDuels(TypedDict):
    total: Optional[int]
    won: Optional[int]


class _PlayerResponseStatisticsDribbles(TypedDict):
    attempts: Optional[int]
    success: Optional[int]
    past: Optional[int]


class _PlayerResponseStatisticsFouls(TypedDict):
    drawn: Optional[int]
    committed: Optional[int]


class _PlayerResponseStatisticsCards(TypedDict):
    yellow: Optional[int]
    yellowred: Optional[int]
    red: Optional[int]


class _PlayerResponseStatisticsPenalty(TypedDict):
    won: Optional[int]
    commited: Optional[int]
    scored: Optional[int]
    missed: int
    saved: Optional[int]


class _PlayerResponseStatistics(TypedDict):
    team: _PlayerResponseStatisticsTeam
    league: _PlayerResponseStatisticsLeague
    games: _PlayerResponseStatisticsGames
    substitutes: _PlayerResponseStatisticsSubstitutes
    shots: _PlayerResponseStatisticsShots
    goals: _PlayerResponseStatisticsShotsGoals
    passes: _PlayerResponseStatisticsShotsPasses
    tackles: _PlayerResponseStatisticsShotsTackles
    duels: _PlayerResponseStatisticsDuels
    dribbles: _PlayerResponseStatisticsDribbles
    fouls: _PlayerResponseStatisticsFouls
    cards: _PlayerResponseStatisticsCards
    penalty: _PlayerResponseStatisticsPenalty


class GETPlayerResponse(TypedDict):
    player: _PlayerResponsePlayer
    statistics: List[_PlayerResponseStatistics]


class _FixturesEventResponseTime(TypedDict):
    elapsed: int
    extra: Optional[int]


class _FixturesEventResponseTeam(TypedDict):
    id: int
    name: str
    logo: str


class _FixturesEventResponsePlayer(TypedDict):
    id: int
    name: str


class _FixturesEventResponseAssist(TypedDict):
    id: int
    name: str


class GETFixturesEventResponse(TypedDict):
    time: _FixturesEventResponseTime
    team: _FixturesEventResponseTeam
    player: _FixturesEventResponsePlayer
    assist: _FixturesEventResponseAssist
    type: Optional[str]
    detail: Optional[str]
    comments: Optional[str]
