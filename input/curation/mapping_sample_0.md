# Error analysis

## 1920s

63% accuracy

- Herr Vennersten missing from the whole MoP.csv, maybe not an MP but a minister?

- herr statsrådet Malm, also not in MoP.csv

## 1930s

80% accuracy

- "Herr Lindgren" not matched, probably multiple matches.
	- Options:
		- Anders Lindgren,Bondeförbundet, Älvsborgs läns norra, Andra kammaren
		- Adolf Lindgren,Högerpartiet,Örebro län,Första kammaren
	- The intro is in Första Kammaren, so it probably refers to Adolf. Seems that no specifications are made if there is only one MP in the chamber with that name. Though sometimes people from the other chamber might speak too?

## 1940s

58% accuracy

- "Herr Gustafsson i Tenhult" not matched, specifier "Tenhult" not in MoP.csv
- "Herr Wistrand:" not matched for unknown reason. He is the only "Wistrand" in the era.
- "Herr Norman" not matched for unknown reason. He is the only "Norman" in MoP.csv.
- "Herr Andersson i Löbbo" not matched.
	- Currently, there is only one potential match in MoP.csv:
		- Gustav Andersson,Bondeförbundet,Jönköpings län,Andra kammaren,1941,1944,,man,gustav_andersson_191cfb,i Löbbo
		- The protocol is from 1945 (outside 1941-1944) which might cause the error
	- Happens twice in a row in our sample

## 1950s

72% accuracy

- "Herr HANSSON:" not matched
	- The only Hansson in Första Kammaren at the time?
	- We are missing Första Kammaren MPs from that timepoint anyway.
- "Herr NILSSON, PATRICK (bf):" not matched
	- We are missing Första Kammaren MPs from that timepoint
	- Happens twice on the page

## 1960s

60% accuracy

- "Herr ALEXANDERSON (fp):" missed for some reason
	- Alexandersson with two S's in MoP.csv??
	- Happens twice on the page

## 1970s

100% accuracy

## 1980s

85% accuracy

- "Anf. 138 GÖREL THURDIN (c) replik:" missed for some reason
	- The full name should be matched and unique?

- "Statsrådet LENA HJELM-WALLÉN:" is interpreted as "karl-goran_biorsmark_7d1626" due to missing of a previous intro
	- Happens twice

# Sample

| package_id | pagenumber | url |  |  |  |  |  | Correct | Incorrect | Acc per decade|
| --- | --- | --- | --- | --- | --- |  ---| --- | --- | --- | --- |
|prot-1922--fk--12 | 57 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1922/prot-1922--fk--12.xml |  |  |  |  |  | 2 | 0 |
|prot-1921--fk--25 | 57 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1921/prot-1921--fk--25.xml |  |  |  |  |  | 0 | 3 |
|prot-1921--ak--46 | 77 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1921/prot-1921--ak--46.xml |  |  |  |  |  | 2 | 0 |
|prot-1926--fk--42 | 79 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1926/prot-1926--fk--42.xml |  |  |  |  |  | 2 | 0 |
|prot-1923--ak--44 | 150 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1923/prot-1923--ak--44.xml |  |  |  |  |  | 1 | 1 | 0,6363636364|
|prot-1935--fk--42 | 6 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1935/prot-1935--fk--42.xml |  |  |  |  |  | 1 | 0 |
|prot-1936--ak--25 | 24 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1936/prot-1936--ak--25.xml |  |  |  |  |  | 1 | 0 |
|prot-1934--ak--40 | 37 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1934/prot-1934--ak--40.xml |  |  |  |  |  | 1 | 0 |
|prot-1932--fk--49 | 119 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1932/prot-1932--fk--49.xml |  |  |  |  |  | 1 | 1 |
|prot-1939--fk--32 | 85 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1939/prot-1939--fk--32.xml |  |  |  |  |  | 0 | 0 | 0,8|
|prot-1948--fk--22 | 113 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1948/prot-1948--fk--22.xml |  |  |  |  |  | 3 | 0 |
|prot-1942--ak--10 | 19 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1942/prot-1942--ak--10.xml |  |  |  |  |  | 2 | 1 |
|prot-1943--ak--26 | 51 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1943/prot-1943--ak--26.xml |  |  |  |  |  | 2 | 0 |
|prot-1945--fk--15 | 94 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1945/prot-1945--fk--15.xml |  |  |  |  |  | 0 | 2 |
|prot-1945--ak--13 | 158 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1945/prot-1945--ak--13.xml |  |  |  |  |  | 0 | 2 | 0,5833333333|
|prot-1952--ak--16 | 177 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1952/prot-1952--ak--16.xml |  |  |  |  |  | 2 | 0 |
|prot-1959-höst-fk--24 | 66 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1959/prot-1959-höst-fk--24.xml |  |  |  |  |  | 3 | 0 |
|prot-1952--fk--11 | 41 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1952/prot-1952--fk--11.xml |  |  |  |  |  | 2 | 1 |
|prot-1954--ak--22 | 77 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1954/prot-1954--ak--22.xml |  |  |  |  |  | 1 | 0 |
|prot-1953-höst-fk--32 | 71 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1953/prot-1953-höst-fk--32.xml |  |  |  |  |  | 0 | 2 | 0,7272727273|
|prot-1969-höst-fk--41 | 29 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1969/prot-1969-höst-fk--41.xml |  |  |  |  |  | 0 | 0 |
|prot-1969-höst-fk--40 | 33 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1969/prot-1969-höst-fk--40.xml |  |  |  |  |  | 0 | 2 |
|prot-1963--ak--14 | 23 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1963/prot-1963--ak--14.xml |  |  |  |  |  | 1 | 0 |
|prot-1960-höst-ak--29 | 141 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1960/prot-1960-höst-ak--29.xml |  |  |  |  |  | 1 | 0 |
|prot-1960--ak--2 | 218 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1960/prot-1960--ak--2.xml |  |  |  |  |  | 1 | 0 | 0,6|
|prot-197879--144 | 27 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/197879/prot-197879--144.xml |  |  |  |  |  | 3 | 0 |
|prot-197980--94 | 50 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/197980/prot-197980--94.xml |  |  |  |  |  | 2 | 0 |
|prot-197879--60 | 25 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/197879/prot-197879--60.xml |  |  |  |  |  | 3 | 0 |
|prot-1974--106 | 51 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1974/prot-1974--106.xml |  |  |  |  |  | 5 | 0 |
|prot-1974--112 | 16 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/1974/prot-1974--112.xml |  |  |  |  |  | - | - | 1|
|prot-198283--132 | 65 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/198283/prot-198283--132.xml |  |  |  |  |  | 2 | 0 |
|prot-198687--65 | 131 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/198687/prot-198687--65.xml |  |  |  |  |  | 4 | 1 |
|prot-198283--74 | 20 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/198283/prot-198283--74.xml |  |  |  |  |  | 3 | 0 |
|prot-198687--37 | 22 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/198687/prot-198687--37.xml |  |  |  |  |  | 4 | 0 |
|prot-198990--54 | 24 | https://github.com/welfare-state-analytics/riksdagen-corpus/tree/mp/corpus/198990/prot-198990--54.xml |  |  |  |  |  | 4 | 2 | 0,85|
|  |  |  |  |  |  |  | Acc | 0,7662337662 | 