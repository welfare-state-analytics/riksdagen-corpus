#!/bin/bash
read -r -d '' DOCSTR << EOM
_____________________________________________________
 < After creating a qualtiy control sample,          >
 < this script stages the selected files in git...   >
 < for optimal laziness.                             >
 <                                                   >
 < But you need to provide a single argument, that   >
 < is, the first year of the decade sample.          >
 <                                                   >
 < Run from project root as with the python scripts. > 
  ------------------------------------------------------
    \                                  ___-------___
     \                             _-~~             ~~-_
      \                         _-~                    /~-_
             /^\__/^\         /~  \                   /    \\
           /|  o|| o|        /      \_______________/        \\
          | |___||__|      /       /                \          \\
          |          \    /      /                    \          \\
          |   (_______) /______/                        \_________ \\
          |         / /         \                      /            \\
           \         \^\\         \                  /               \     /
             \         ||           \______________/      _-_       //\__//
               \       ||------_-~~-_ ------------- \ --/~   ~\    || __/
                 ~-----||====/~     |==================|       |/~~~~~
                  (_(__/  ./     /                    \_\      \.
                         (_(___/                         \_____)_)

EOM

if [ -z ${1+x} ]; then
	echo "$DOCSTR"
else

sample_file=input/quality-control/sample_$1.txt

if [ -f $sample_file ]; then

	echo "Input $sample_file exists."
	while read -r line
	do
		echo "git adding $line"
		git add "$line"
	done < "$sample_file"

else

	read -r -d '' ERRSTR << EOM
 ___________________________________________________________________ 
 | You turkey!                                                    |
 | No input file at $sample_file exists. |
 | Find your input file and try again!                            |
 ------------------------------------------------------------------
  \                                  ,+*^^*+___+++_X
   \                           ,*^^^^              )
    \                       _+*                     ^**+_
     \                    +^       _ _++*+_+++_,         )
              _+^^*+_    (     ,+*^ ^          \+_        )
             {       )  (    ,(    ,_+--+--,      ^)      ^\\
            { (@)    } f   ,(  ,+-^ __*_*_  ^^\_   ^\       )
           {:;-/    (_+*-+^^^^^+*+*<_ _++_)_    )    )      /
          ( /  (    (        ,___    ^*+_+* )   <    <      \\
           U _/     )    *--<  ) ^\-----++__)   )    )       )
            (      )  _(^)^^))  )  )\^^^^^))^*+/    /       /
          (      /  (_))_^)) )  )  ))^^^^^))^^^)__/     +^^
         (     ,/    (^))^))  )  ) ))^^^^^^^))^^)       _)
          *+__+*       (_))^)  ) ) ))^^^^^^))^^^^^)____*^
          \             \_)^)_)) ))^^^^^^^^^^))^^^^)
           (_             ^\__^^^^^^^^^^^^))^^^^^^^)
             ^\___            ^\__^^^^^^))^^^^^^^^)\\
                  ^^^^^\uuu/^^\uuu/^^^^\^\^\^\^\^\^\^\\
                     ___) >____) >___   ^\_\_\_\_\_\_\)
                    ^^^//\\_^^//\\_^       ^(\_\_\_\)
                      ^^^ ^^ ^^^ ^
EOM
	echo "$ERRSTR"

fi
fi
