import sys
import os
import argparse

# -f <trace file name>     [ name of text file with the trace ]
# -s <cache block size>    [ 1 KB to 8 MB ]
# -b <block size>          [ 4 bytes to 64 bytes ]
# -a <associativity>       [ 1, 2, 4, 8, 16 ]
# -r <replacement policy>  [RR or RND or LRU for bonus points]


parser = argparse.ArgumentParser()
parser.add_argument('-f', dest='trace_file', metavar='filename', type=str
				   , required=True, help='filename of the trace file')
parser.add_argument('-s', dest='cache_size', metavar='cache size',type=int
				   , choices=range(1,8193), required=True
				   , help='Size of cache in kb. Range is 1 to 8192')
parser.add_argument('-b', dest='block_size', metavar='block size',type=int
				   , choices=range(4,65), required=True
				   , help='Size of blocks in kb. Range is 4 to 64')
parser.add_argument('-a', dest='associativity', metavar='associativity'
				   ,type=int, choices=[1,2,4,8,16], required=True
				   , help='Sets the associativity. Acceptable'\
				   +' values are: 1, 2, 4, 8, 16')
parser.add_argument('-r', dest='rep_policy', metavar='replacement',type=str
				   , choices=['RR','RND','LRU'], required=True
				   , help='Replacement policy. Acceptable values: RR (round'\
				   +' robin), RND (random), LRU (least recently used)')
args = parser.parse_args()
print(args)
# if len(sys.argv) < 11:
#     print("Not enough arguments")
#     sys.exit(1)

# if len(sys.argv) > 11:
#     print("Too many arguments")
#     sys.exit(1)


        
