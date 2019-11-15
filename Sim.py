
import sys
import os
import math
from os import path
import argparse


# -f <trace file name>     [ name of text file with the trace ]
# -s <cache block size>    [ 1 KB to 8 MB ]
# -b <block size>          [ 4 bytes to 64 bytes ]
# -a <associativity>       [ 1, 2, 4, 8, 16 ]
# -r <replacement policy>  [RR or RND or LRU for bonus points]

def parse_args():
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
        parser.add_argument('-d', dest='debug', action='store_true', help='Add extra print statements')
        args = parser.parse_args()
        if not (1 <= args.cache_size <= 8192):
        	parser.error('-s cache size is out of range.  int between 1 and 8192') 

        if not (4 <= args.block_size <= 64):
        	parser.error('-b block size is out of range. Select int between 4 and 64') 

        return args

#### Script style implementation
args = parse_args()       
print(args)

trace_file = args.trace_file
cache_size = args.cache_size
block_size = args.block_size
associativity = args.associativity
rep_policy = args.rep_policy
group_number = 14
total_blocks = cache_size / block_size
number_of_indexes = (cache_size * 1000 ) / (block_size * associativity) # of indexes with associativity
block_offset_bits = int(math.log(block_size, 2)) # get the offset bits
index_bits = int(math.log(number_of_indexes, 2))+1  # get the index bits
tag_bits = 32 - block_offset_bits - index_bits  #tag bits 

# File validation
if not path.exists(trace_file):
        print("File '", trace_file, "' doen't exist")
        exit()


#
# Creating Cache
#
# python3 Sim.py -f TestTrace.trc -s 1024 -b 16 -a 2 -r RR
#
# Based on this implementation of cache, there will be a dictionary of dictionaries

#empty cache set
cache = {}

#This creates the cache using index size with associativity
cache = {i : {a : (0, None) for a in range(int(associativity))} for i in range(int(number_of_indexes))}

#print (cache) 


#parsing file
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
                        br = int(line[5 : 7], 16)
                        hex_value1 = line[10 : 18]
                        #start line 19 for codes
                        for x in line:
                                # *** CC: I added a check to make sure the string isn't
                                # accessed out of range
                                if x == ' ' and len(line) > length + 1 and line[length + 1] == ' ':
                                        break
                                else:
                                        length = length + 1
                        count += 1

                if line[0] == 'd':
                        
                        line = line.rstrip('\n')

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
                        #print(return_statement + '\n') 
                        return_statement = " "


f.close()

#### Object Oriented Implementation \w some modularization ####
class mem_access_request():
    def __init__(self, address=None, access_type=None, length=None):
        # Error handling for address. (To catch programmer errors)
        if type(address) is not None and type(address) != str and type(address) != int:
            raise ValueError("address must either be a string or a base 16 int")
        if type(address) == str:
            try:
                address = int(address, 16)
            except ValueError as e:
                print('address was not a number')
                raise e

        self.address = address

        # Error handling for access_type
        if (type(access_type) == str and access_type not in ['i','w','r']) \
            and type(access_type) is not None:
                raise ValueError("access_type must be 'i' (instruction), 'w' (write),"
                                 +" 'r' (read). "+str(access_type)+" is an invalid value.")

        self.access_type = access_type

        if self.access_type == 'w' or self.access_type == 'r':
            self.length = 4
        else:
            try:
                self.length = int(length)
            except ValueError as e:
                print('length was not a number')
                raise e

    def to_string(self):
        s = '0x%x'%(self.address)+' ('+str(self.length)+')'
        return s


class full_instruction():
    def __init__(self,instruction=None, read=None, write=None, instruct_line=None
                    , rw_line=None):
        self.instruction = instruction
        self.read = read
        self.write = write
        self.instruct_line = instruct_line
        self.rw_line=rw_line

    def display(self, debug=False, num_print=3):
        instruction_count = 1
        if debug:
            print('***instruction request:')

        print(self.instruction.to_string())

        if debug:
            print('from line:', self.instruct_line)
        if instruction_count == num_print:
            return instruction_count

        if debug:
            print('write request:')
        if self.write is not None:
            instruction_count += 1
            print(self.write.to_string())

        if debug:
            if self.write is None:
                print(self.write)
            print('from line:', self.rw_line)
        if instruction_count == num_print:
            return instruction_count

        if debug:
            print('read request:')
        if self.read is not None:
            instruction_count += 1
            print(self.read.to_string())
        if debug:
            if self.read is None:
                print(self.read)
            print('from line:', self.rw_line)       
                
        return instruction_count

class cache():
    def __init__ (self, total_blocks=None, number_of_indexes=None, block_offset=None, index_bits=None, tag_bits=None):
        self.total_blocks = parsed_args.cache_size / parsed_args.cache_size
        self.number_of_indexes = (cache_size * 1000 ) / (block_size * associativity) # of indexes with associativity
        self.block_offset_bits = int(math.log(block_size, 2)) # get the offset bits
        self.index_bits = int(math.log(number_of_indexes, 2))+1  # get the index bits
        self.tag_bits = 32 - block_offset_bits - index_bits  #tag bits
    
def print_header(cmd_args, parsed_args):
        print('\nCmd Line:', ' '.join(cmd_args))
        print('Trace File:', parsed_args.trace_file)
        print('Cache Size:', parsed_args.cache_size)
        print('Block Size:', parsed_args.block_size)
        print('Associativity:', parsed_args.associativity)
        print('R-Policy:', parsed_args.rep_policy)

def print_cache_info():
        #TODO: fill out actual values after implementing calculations
        print('----- Calculated Values -----')
        print('Total #Blocks:', int(total_blocks)  )
        print('Tag Size:', tag_bits)
        print('Index Size:', int(number_of_indexes))
        print('Overhead Memory Size:')
        print('Implementation Memory Size:')

def print_results():
        #TODO: fill out results once cache is implemented
        print('----- Results -----')
        print('Cache Hit Rate:')
        print('Cache Miss Rate:')
        print('CPI:', '\n')


def print_samples(instructions, num_print=20, debug=False):
        count = 0
        for instruct in instructions:
                count+= instruct.display(num_print=(num_print-count), debug=debug)
                if count >= num_print:
                        if debug:
                                print('num_print reached:', num_print)
                        break

def read_instructions(trace_file):
        if not path.exists(trace_file):
                print("File '", trace_file, "' doen't exist")
                exit()
        with open(trace_file) as f:
                instruction_list = []
                next_full_instruct = None
                for line in f:
                        if line[0] == 'E':
                                length = line[5:7]
                                address = line[10 : 18]
                                access_type = 'i'
                                instruction = mem_access_request(address=address
                                                                , access_type=access_type
                                                                , length=length)
                                next_full_instruct = full_instruction(instruction=instruction)
                                next_full_instruct.instruct_line = line
                        if line[0] == 'd':
                                if next_full_instruct == None:
                                        print('Logic error: processed read/write before '
                                            +'instruction line')
                                        raise

                                write_address = line[6:14]
                                write = None
                                if write_address != '00000000':
                                        write = mem_access_request(address=write_address
                                                                    , access_type='w')
                                
                                read_address = line[33:41]
                                read = None
                                if read_address != '00000000':
                                        read = mem_access_request(address=read_address
                                                                , access_type='r')

                                next_full_instruct.write = write
                                next_full_instruct.read = read
                                next_full_instruct.rw_line = line
                                if next_full_instruct.instruction.length > 0:
                                        instruction_list.append(next_full_instruct)

                                # reset for next set of instructions
                                next_full_instruct = None
        return instruction_list


def main():
        args = parse_args()
        print_header(sys.argv, args)

        print_cache_info()
        full_instructions = read_instructions(args.trace_file)

        print_results()
        print_samples(full_instructions, num_print=20, debug=args.debug)    


if __name__ == '__main__':
        main()