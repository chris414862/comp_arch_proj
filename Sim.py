
import sys
import os
import math
from os import path
import argparse
import logging


# -f <trace file name>     [ name of text file with the trace ]
# -s <cache block size>    [ 1 KB to 8 MB ]
# -b <block size>          [ 4 bytes to 64 bytes ]
# -a <associativity>       [ 1, 2, 4, 8, 16 ]
# -r <replacement policy>  [RR or RND or LRU for bonus points]
DEBUG=False

def main():
		args = parse_args()
		print_header(sys.argv, args)
		cache = Cache(cache_size=args.cache_size, block_size=args.block_size, associativity=args.associativity
					 , rep_policy=args.rep_policy)
		cache.display()
		full_instructions = read_instructions(args.trace_file)
		#hit_rate, miss_rate, cpi = cache_simulator(cache, full_instructions)
		print_results()
		if args.debug:
			print_samples(full_instructions, num_print=20)   

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
        if args.debug:
        	logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.DEBUG)
        	DEBUG = True
        else:
        	logging.basicConfig(filename=sys.argv[0]+'.log', format='%(levelname)s: %(message)s')

        return args


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

	def display(self, num_print=3):
		instruction_count = 1

		logging.debug('***instruction request:')
		print(self.instruction.to_string())
		logging.debug('from line: '+str(self.instruct_line))

		# Used to make sure only 20 total accesses are printed
		if instruction_count == num_print:
			return instruction_count

		logging.debug('write request:')
		if self.write is not None:
			instruction_count += 1
			print(self.write.to_string())
		else:
			logging.debug(self.write)
		logging.debug('from line: '+str(self.rw_line))

		# Used to make sure only 20 total accesses are printed
		if instruction_count == num_print:
			return instruction_count

		logging.debug('read request:')
		if self.read is not None:
			instruction_count += 1
			print(self.read.to_string())
		else:
			logging.debug(self.read)
		logging.debug('from line: '+str(self.rw_line))       

		return instruction_count


    
def print_header(cmd_args, parsed_args):
    print('\nCmd Line:', ' '.join(cmd_args))
    print('Trace File:', parsed_args.trace_file)




def print_results():
    #TODO: fill out results once cache is implemented
    print('----- Results -----')
    print('Cache Hit Rate:')
    print('Cache Miss Rate:')
    print('CPI:', '\n')


def print_samples(instructions, num_print=20):
    count = 0
    for instruct in instructions:
            count+= instruct.display(num_print=(num_print-count))
            if count >= num_print:
                    logging.debug('num_print reached: '+str(num_print))
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


class Block():
	def __init__(self, tag=None, valid=0):
		self.tag=tag
		self.valid=valid


class CacheRow():
	def __init__(self, associativity, index ):
		self.associativity = associativity
		self.index = index
		self.cols = [Block() for a in range(associativity)]

class Cache():
	def __init__ (self, cache_size=0, block_size=0, associativity=0, rep_policy=None):
		self.cache_size = cache_size
		self.block_size = block_size
		self.associativity = associativity
		self.rep_policy = rep_policy
		self.total_blocks = self.cache_size // self.block_size
		if self.cache_size % self.block_size != 0:
			self.cache_size = self.total_blocks * self.block_size
			print('WARNING: Cache size not divisible by block size. Reducing cache size to '+str(self.cache_size))
		self.number_of_indeces = cache_size  // (block_size * associativity) * 1024 # of indexes with associativity
		self.block_offset_bits = int(math.log(block_size, 2)) # get the offset bits
		self.index_bits = int(math.log(self.number_of_indeces, 2))  # get the index bits
		self.tag_bits = 32 - self.block_offset_bits - self.index_bits  #tag bits
		self.overhead = self.total_blocks*(1 + self.tag_bits)//8
		self.implementation = self.overhead +self.cache_size
		self.c = [CacheRow(self.associativity, i) for i in range(self.number_of_indeces)]


	def display(self):
		#TODO: fill out actual values after implementing calculations
		print('Cache Size:', self.cache_size)
		print('Block Size:', self.block_size)
		print('Associativity:', self.associativity)
		print('R-Policy:', self.rep_policy)
		print('----- Calculated Values -----')
		print('Total #Blocks:', int(self.total_blocks)  )
		print('Tag Size:', self.tag_bits)
		print('Index Size:', int(self.index_bits))
		print('Overhead Memory Size:', self.overhead)
		print('Implementation Memory Size:', self.implementation)


 


if __name__ == '__main__':
        main()