import sys
import os

# -f <trace file name>     [ name of text file with the trace ]
# -s <cache block size>    [ 1 KB to 8 MB ]
# -b <block size>          [ 4 bytes to 64 bytes ]
# -a <associativity>       [ 1, 2, 4, 8, 16 ]
# -r <replacement policy>  [RR or RND or LRU for bonus points]



if len(sys.argv) < 11:
    print("Not enough arguments")
    sys.exit(1)

if len(sys.argv) > 11:
    print("Too many arguments")
    sys.exit(1)


        
