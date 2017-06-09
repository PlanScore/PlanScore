North Carolina 2014
---

*Michal Migurski, June 2017*

This model of votes in North Carolina is based on the 2014 General Election,
using [vote counts from OpenElections](https://github.com/openelections/openelections-results-nc/blob/8d4eb39ed73ecad1460f08f7cddc518f05b968ff/raw/20141104__nc__general__precinct__raw.csv)
and precinct geography from [Nathaniel Vaughn Kelso’s Election-Geodata](https://github.com/nvkelso/election-geodata/tree/47d1ab793d96546fece39f0e112d8ae504c2ceb8/data/37-north-carolina/statewide/2014).
A Jupyter Notebook with Python code detailing the process
[can be found in my Redistricting repository](https://github.com/migurski/Redistricting/blob/3b5cbbef8d4e949f30a22892f9ffbea0e889e7ec/37%20-%20North%20Carolina/NC%20Imputation%20for%20PlanScore.ipynb)
as well as in the linked files below.

Congressional votes are complete for 12 of 13 districts;
[District 9 was uncontested](https://ballotpedia.org/United_States_House_of_Representatives_elections_in_North_Carolina,_2014)
and its votes were derived from other precincts. Numerous State Senate and State
House races were uncontested, and their votes were derived from other precincts
as well.

Imputed votes were calculated using linear regression based on factors like
other races, racial demographics, age, education, and income after analyzing
known data to determine which factors best predicted outcomes.
See [this Python code for details](iPython-Notebook.html), and
[this Geopackage file for complete geographic data](NC-Imputed-2014.gpkg.gz).

#### U.S. House

With [the exception of District 9](https://ballotpedia.org/North_Carolina%27s_9th_Congressional_District_elections,_2014)
around Charlotte in the central-southern North Carolina, 12 Congressional
districts were contested in the 2014 general election. We have excellent
precinct-level vote coverage for over 90% of the state in these races, shown in
the dark red and blue areas of this map:

![U.S. House precincts](precincts-ushouse.png)

#### State Senate

29 of 50 State Senate seats were contested by candidates from both major parties
[in the 2014 general election](https://ballotpedia.org/North_Carolina_State_Senate_elections,_2014).
Light red and light blue precincts votes in this map have been imputed from
fully-contested national race votes, while dark-colored precincts have
competitive vote counts:

![State Senate precincts](precincts-sldu.png)

#### State House

59 of 120 State House seats were contested by candidates from both major parties
[in the 2014 general election](https://ballotpedia.org/North_Carolina_House_of_Representatives_elections,_2014).
Light red and light blue precincts votes in this map have been imputed from
fully-contested national race votes, while dark-colored precincts have
competitive vote counts:

![State House precincts](precincts-sldl.png)
