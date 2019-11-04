import sys
import os
from os import path
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
				   , required=True
				   , help='Size of cache in kb. Range is 1 to 8192')
parser.add_argument('-b', dest='block_size', metavar='block size',type=int
				   , required=True
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
if not (1 <= args.cache_size <= 8192):
	parser.error('-s cache size is out of range.  int between 1 and 8192') 

if not (1 <= args.block_size <= 64):
	parser.error('-b block size is out of range. Select int between 1 and 64') 

print(args)

trace_file = args.trace_file
cache_size = args.cache_size
block_size = args.block_size
associativity = args.associativity
rep_policy = args.rep_policy


#File validation and parse
if not path.exists(trace_file):
        print("File '", trace_file, "' doen't exist")
        exit()

with open(trace_file) as f:
        count = 0 # to complete one block of EIP and dstM
        length = 0;         #bytes read
        br = 0;             #bytes to read
        hex_value1 = ''
        hex_write = ''
        hex_read = ''
        return_statement = " "
        for line in f:
                datarw = 0 # 1 for read, 2 for write, 3 for read/write
                length = 0;         #bytes read
                if line[0] == 'E':
                        line = line.rstrip('\n')
                        #print(line)
                        br = int(line[5 : 7], 16)
                        hex_value1 = line[10 : 18]
                        #start line 19 for codes
                        for x in line:
                                if x == ' ' and line[length + 1] == ' ':
                                        break
                                else:
                                        length = length + 1
                        #print(line[19 : length])
                        #
                        #Need to finish the length because it changes
                        #
                        count += 1
                        

                if line[0] == 'd':
                        
                        line = line.rstrip('\n')
                        #print(line)

                        hex_write = line[6 : 14]
                        if hex_write != '00000000':
                                if datarw == 2:
                                        datarw = 3
                                if datarw == 0:
                                        datarw = 1

                        hex_read = line[33 : 41]
                        if hex_read != '00000000':
                                if datarw == 1:
                                        datarw = 3
                                if datarw == 0:
                                        datarw = 2
                        
                        count += 1
                if count == 2:
                        return_statement = "Address: 0x" + hex_value1 + ", length = " + str(br)
                        if datarw == 0:
                                return_statement = return_statement + ". No data writes/reads occurred."
                        if datarw == 2:
                                return_statement = return_statement + ". Data read at 0x" + hex_read + ", length = 4 bytes."
                        if datarw == 3:
                                return_statement = return_statement + ". Data write at 0x" + hex_write + ", length = 4 bytes."
                        if datarw == 3:
                                return_statement = return_statement + ". Data write at 0x" + hex_write + ", length = 4 bytes, data read at 0x" + hex_read + ", length = 4 bytes."
                        count = 0
                        print(return_statement + '\n')
                        return_statement = " "
                        #get rid of to load rest of the file        
                        
                        




f.close()


