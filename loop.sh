#!/bin/bash
#run through all variations



counter=1
#compare associativity
for filename in "Corruption1.trc" "TestTrace.trc" "TinyTrace.trc" "Trace1A.trc" "Trace2A.trc"; do
	echo "" > "output"$filename".txt"
	replacement="RR"
	echo "********************************************************************************************************************************************************* "$filename >> "output"$filename".txt"
	while [ $counter -le 3 ]
	do
		if [ $counter -eq 2 ]
		then
			replacement="RND"
		fi
		
		if [ $counter -eq 3 ]
		then
			replacement="LRU"
		fi
		echo "###################################################################################################################### Replacement " $replacement >> "output"$filename".txt"
		((c_size=8))
		while [ $c_size -le 1024 ]
		do	
			echo "******************************************************************************************************** Cache Size Change" >> "output"$filename".txt"
			((b_size=4))
			while [ $b_size -le 64  ]
			do
				echo "&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&& Block Size Change" >> "output"$filename".txt"
				((assoc=1))
				while [ $assoc -le 16 ]
				do
					python Sim.py -f $filename -s $c_size -b $b_size -a $assoc -r $replacement >> "output"$filename".txt"
					((assoc=assoc*2))
				done
				((b_size=b_size*4))
			done
			((c_size=c_size*4))
		done
		
		((counter++))
	done
	((counter=1))
done


echo "All done";