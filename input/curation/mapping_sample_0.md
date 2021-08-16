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