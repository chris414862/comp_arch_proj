
import sys
import os
import math
from os import path
import argparse
import logging
from ctypes import c_uint
import random
from collections import Counter
import time


DEFAULT_EXECUTION_CYCLES = 2 # Number of cycle necessary to execute every instruction
DEFAULT_MEM_ACCESS_CYCLES = 3 # Cycles to access main memory
BUS_SIZE = 4
GLOBAL_CLOCK = 0
DEBUG = False
DEBUG_ITERS = 10 # Number of memory accesses to look at

# Alignment variables
ALIGN = 30
H_ALIGN = 20
H_SIZE = 50
DEBUG_ALIGN = 15
REP_STRINGS = {'RND':'Random', 'RR':'Round Robin', 'LRU':'Least Recently Used'}

def main():	
	args = parse_args()
	print_header(sys.argv, args)
	cache = Cache(cache_size=args.cache_size, block_size=args.block_size, associativity=args.associativity
				 , rep_policy=args.rep_policy)
	cache.display()
	full_instructions = read_instructions(args.trace_file)
	results = cache_simulator(cache, full_instructions)
	print_results(*results)
	if DEBUG:
		print_samples(full_instructions, num_print=DEBUG_ITERS)   


def cache_simulator(cache, full_instructions):
	num_instructions = len(full_instructions)
	tot_mem_accesses = tot_hits = tot_misses = tot_comp_misses = tot_cycles = 0

	# iterate instructions. each include the instruction memory access and the read and write accesses (if available)
	for i, full_instruction in enumerate(full_instructions):
		
		# get the number of memory accesses for this instruction
		num_remaining_requests = full_instruction.get_num_mem_requests()
		while num_remaining_requests > 0:
			next_request, num_remaining_requests = full_instruction.next_mem_request()

			# check cache 
			hits, misses, cycles, comp_misses = process_request(next_request, cache)
			tot_hits += hits 
			tot_misses += misses 
			tot_cycles += cycles
			tot_mem_accesses += hits +misses
			tot_comp_misses += comp_misses

		# Stop short for debugging
		if DEBUG:
			if i >= DEBUG_ITERS:
				num_instructions = i 
				break

	return tot_cycles, num_instructions, tot_hits, tot_misses, tot_mem_accesses, tot_comp_misses

def process_request(mem_access_request, cache):
	global GLOBAL_CLOCK

	# Cycle for just 'executing' the memory access (not sure why its added for data read/writes)
	cycles = DEFAULT_EXECUTION_CYCLES
	bytes_to_read = mem_access_request.length
	address = mem_access_request.address
	if DEBUG:
		logging.debug(f"\n       {'start address:':{DEBUG_ALIGN}}{address:x}")
		logging.debug(f"{'start address:':{DEBUG_ALIGN}}{address:b}")

	hits = misses = comp_misses = 0
	while bytes_to_read > 0:
		GLOBAL_CLOCK = GLOBAL_CLOCK + 1
		if DEBUG:
			logging.debug(f"{'new address:':{DEBUG_ALIGN}}{address:x}")
			logging.debug(f"{'new address:':{DEBUG_ALIGN}}{address:b}")
			logging.debug(f"{'bytes to read:':{DEBUG_ALIGN}}{bytes_to_read}")
			logging.debug(f"{'global clock:':{DEBUG_ALIGN}}{GLOBAL_CLOCK}")

		# check cache and try to read some bytes
		bytes_read, hit_status= cache.read_from_cache(address, bytes_to_read)
		if hit_status == 'hit':  
			cycles += 1
			hits += 1
			if DEBUG:
				ng.debug(f"{'HIT!':{DEBUG_ALIGN}}")
		else: # miss
			misses += 1
			if DEBUG:
				logging.debug(f"{'MISS!':{DEBUG_ALIGN}} ")

			# if bytes_read is -1 then it was a compulsory miss
			if hit_status == 'compulsory':
				comp_misses += 1

			# run replacement policy after miss
			cache.replace_block(address)
			
			# add the penalty for repopulating a block
			cycles += DEFAULT_MEM_ACCESS_CYCLES * math.ceil(cache.block_size/BUS_SIZE)
		

		if DEBUG:
			logging.debug(f"{'bytes read from cache:':{DEBUG_ALIGN}}{bytes_read}")
			logging.debug(f"{'cycles:':{DEBUG_ALIGN}}{cycles}")
			logging.debug(f"{'bytes remaining to read:':{DEBUG_ALIGN}}{bytes_to_read}")

		# after an access all of the bytes in the block are brought back to the cpu
		bytes_to_read -= bytes_read
		address += bytes_read
		
	return hits, misses, cycles, comp_misses

	


class Block():
	def __init__(self, tag=None, valid=0, col_index=0):
		global GLOBAL_CLOCK
		self.tag=tag
		self.valid=valid
		self.col=col_index
		self.last_used = GLOBAL_CLOCK

	def update_clock(self):
		global GLOBAL_CLOCK
		self.last_used = GLOBAL_CLOCK

	def to_string(self):
		return 'tag: '+str(self.tag)+' valid: '+str(self.valid)+' col_index: '+str(self.col)\
			 +' last_used: '+str(self.last_used)


class CacheRow():
	def __init__(self, associativity, col_index ):
		self.associativity = associativity
		self.col_index = col_index
		self.cols = {idx:Block(col_index=idx) for idx in range(associativity)}
		self.next_for_round_robin = 0


	def is_full(self):
		return [k for k in self.cols if not self.cols[k].valid] == []
		

	def contains_valid_tag(self, tag, p=False):
		block = self.cols.get(tag, None)
		return False if block == None or not block.valid else True

	def replace(self, idx, tag):
		self.cols.pop([k for k in self.cols if self.cols[k].col == idx][0])
		self.cols[tag] = Block(tag=tag, valid=1, col_index=idx)


class Cache():
	def __init__ (self, cache_size=0, block_size=0, associativity=0, rep_policy=None):
		self.cache_size = cache_size * 1024
		self.block_size = block_size
		self.associativity = associativity
		self.rep_policy = rep_policy
		if not math.log2(self.cache_size).is_integer():
			self.cache_size = 2**math.floor(math.log(self.cache_size,2))
			logging.warning("Cache size is not a power of 2. Reducing cache size to"+
							f"{self.cache_size//1024} kb")
		self.total_blocks = self.cache_size // self.block_size
		self.number_of_indeces = math.ceil(self.cache_size  /(self.block_size * self.associativity))  
		self.block_offset_bits = math.ceil(math.log(block_size, 2)) # get the offset bits
		self.index_bits = math.ceil(math.log(self.number_of_indeces, 2))  # get the index bits
		self.tag_bits = 32 - self.block_offset_bits - self.index_bits  #tag bits
		self.overhead = self.total_blocks*(1 + self.tag_bits)//8
		self.implementation = self.overhead +self.cache_size
		self.rows = [CacheRow(self.associativity, i) for i in range(self.number_of_indeces)]


	def replace_block(self, address):
		'''
		This finds the index to replace depending on the replacement policy
		'''
		tag, idx, b_offset = self.get_address_pieces(address)

		row = self.rows[idx]
		if self.rep_policy == 'RND':
			rem_idx = random.randint(0, row.associativity-1)

			# Make sure invalid blocks are filled first
			while not row.is_full() and row.cols[rem_idx].valid:
				rem_idx = random.randint(0, row.associativity-1)

		elif self.rep_policy == 'RR':
			rem_idx = row.next_for_round_robin
			row.next_for_round_robin = (row.next_for_round_robin+1) % row.associativity

		elif self.rep_policy == 'LRU':
			rem_idx = min([row.cols[k] for k in row.cols], key=lambda x: x.last_used).col

		row.replace(rem_idx, tag)
	


	def read_from_cache(self, address, bytes_to_read):
		'''
		This checks if an address is in the cache. Returns bytes read and the type of hit/miss
		'''
		tag, idx, b_offset = self.get_address_pieces(address)
		row = self.rows[idx]
		if row.contains_valid_tag(tag):
			hit_status = 'hit'
		elif not row.is_full(): # compulsory miss
			hit_status = 'compulsory'
		else: # conflict miss
			hit_status = 'conflict'
			
		bytes_read = self.block_size - b_offset
		return bytes_read, hit_status 


	def get_address_pieces(self, address):
		return self.get_tag(address), self.get_index(address), self.get_block_offset(address)

	def get_tag(self, address):
		return address >> (self.block_offset_bits + self.index_bits)

	def get_block_offset(self, address):
		return address % 2**self.block_offset_bits

	def get_index(self, address):
		idx = address >> self.block_offset_bits
		idx = idx % 2**self.index_bits
		return idx


	def display(self):
		print(f"\n{'Cache Input Parameters':-^{H_SIZE}}\n")
		print(f"{'Cache Size:':<{ALIGN}}{self.cache_size/1024:,} kb")
		print(f"{'Block Size:':<{ALIGN}}{self.block_size:,} bytes")
		print(f"{'Associativity:':<{ALIGN}}{self.associativity}")
		print(f"{'Replacement Policy:':<{ALIGN}}{REP_STRINGS[self.rep_policy]}")
		print(f"\n{'Cache Calculated Parameters':-^{H_SIZE}}\n")
		print(f"{'Total # Blocks:':<{ALIGN}}{self.total_blocks:,}")
		print(f"{'Total # Rows:':<{ALIGN}}{self.number_of_indeces:,}")
		print(f"{'Tag Bits:':<{ALIGN}}{self.tag_bits}")
		print(f"{'Index Bits:':<{ALIGN}}{self.index_bits}")
		print(f"{'Overhead Memory Size:':<{ALIGN}}{self.overhead:,} bytes")
		print(f"{'Implementation Memory Size:':<{ALIGN}}{self.implementation//1024:,} kb")	


class MemAccessRequest():
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
		self.mem_accesses = [self.instruction, self.read, self.write]
		self.curr_mem_request = self.instruction
		self.instruct_line = instruct_line
		self.rw_line=rw_line


	def next_mem_request(self):
		next_mem_request = self.curr_mem_request
		num_remaining = self._get_num_remaining()
		self._update_curr_request()
		return next_mem_request, num_remaining


	def _get_num_remaining(self):
		curr_idx = self.mem_accesses.index(self.curr_mem_request)
		num_remaining = 0
		for i in range(curr_idx+1, len(self.mem_accesses)):
			if self.mem_accesses[i] is not None:
				num_remaining += 1
		return num_remaining


	def _update_curr_request(self):
		'''
		sets the self.curr_mem_request field to the next MemAccessRequest object in self.mem_accesses
		that has a valid address. 
		'''
		curr_idx = self.mem_accesses.index(self.curr_mem_request)
		i = None
		for i in range(curr_idx+1, len(self.mem_accesses)):
			if self.mem_accesses[i] is not None:
				break 
		if i is not None:
			self.curr_mem_request = self.mem_accesses[i]


	def set_mem_accesses(self):
		self.mem_accesses = [self.instruction, self.read, self.write]


	def get_num_mem_requests(self):
		accesses = 0
		for mem_access in self.mem_accesses:
			if mem_access != None:
				accesses += 1
		return accesses


	def display(self, num_print=3):
		instruction_count = 1

		logging.debug('***instruction request:')
		logging.debug('from line: '+str(self.instruct_line))

		print(self.instruction.to_string())
		

		# Used to make sure only 20 total accesses are printed
		if instruction_count == num_print:
			return instruction_count

		logging.debug('write request:')
		logging.debug('from line: '+str(self.rw_line))
		if self.write is not None:
			instruction_count += 1
			print(self.write.to_string())
		else:
			logging.debug(self.write)


		# Used to make sure only 20 total accesses are printed
		if instruction_count == num_print:
			return instruction_count

		logging.debug('read request:')
		logging.debug('from line: '+str(self.rw_line))
		if self.read is not None:
			instruction_count += 1
			print(self.read.to_string())
		else:
			logging.debug(self.read)
		       

		return instruction_count

    
def print_header(cmd_args, parsed_args):
    print(f"\n{'Cmd Line:':<{H_ALIGN}}{' '.join(cmd_args)}")
    print(F"{'Trace File:':<{H_ALIGN}}{parsed_args.trace_file}")


def print_results(tot_cycles, num_instructions, tot_hits, tot_misses, tot_mem_accesses, tot_comp_misses):
    print(f"\n{'Cache Calculated Parameters':-^{H_SIZE}}\n")
    print(f"{'Cache Hit Rate:':<{ALIGN}}{tot_hits/tot_mem_accesses:.3%}")
    print(f"{'Cache Miss Rate:':<{ALIGN}}{tot_misses/tot_mem_accesses:.3%}")
    print(f"{'CPI:':<{ALIGN}}{tot_cycles/num_instructions:.3f}")
    print(f"{'Total Cache Accesses:':<{ALIGN}}{tot_mem_accesses:,}")
    print(f"{'Total Hits:':<{ALIGN}}{tot_hits:,}")
    print(f"{'Total Misses:':<{ALIGN}}{tot_misses:,}")
    print(f"----{'Total Compulsory Misses:':<{ALIGN-4}}{tot_comp_misses:,}")
    print(f"----{'Total Conflict Misses:':<{ALIGN-4}}{tot_misses -tot_comp_misses:,}")


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
                            instruction = MemAccessRequest(address=address
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
                                    write = MemAccessRequest(address=write_address
                                                                , access_type='w')
                            
                            read_address = line[33:41]
                            read = None
                            if read_address != '00000000':
                                    read = MemAccessRequest(address=read_address
                                                            , access_type='r')

                            next_full_instruct.write = write
                            next_full_instruct.read = read
                            next_full_instruct.rw_line = line
                            next_full_instruct.set_mem_accesses()
                            if next_full_instruct.instruction.length >= 0:
                                if next_full_instruct.instruction.length == 0:
                                    next_full_instruct.instruction.length =1
                                instruction_list.append(next_full_instruct)

                            # reset for next set of instructions
                            next_full_instruct = None
    return instruction_list


def parse_args():
	global DEBUG
	global DEBUG_ITERS
	parser = argparse.ArgumentParser()
	parser.add_argument('-f', dest='trace_file', metavar='filename', type=str
					   , required=True, help='filename of the trace file')
	parser.add_argument('-s', dest='cache_size', metavar='cache size',type=int
					   , required=True
					   , help='Size of cache in kb. Range is 1 to 8192')
	parser.add_argument('-b', dest='block_size', metavar='block size',type=int
					   , required=True
					   , help='Size of blocks in bytes. Range is 4 to 64')
	parser.add_argument('-a', dest='associativity', metavar='associativity'
					   ,type=int, choices=[1,2,4,8,16], required=True
					   , help='Sets the associativity. Acceptable'\
					   +' values are: 1, 2, 4, 8, 16')
	parser.add_argument('-r', dest='rep_policy', metavar='replacement',type=str
					   , choices=['RR','RND','LRU'], required=True
					   , help='Replacement policy. Acceptable values: RR (round'\
					   +' robin), RND (random), LRU (least recently used)')
	parser.add_argument('-d', dest='debug', default=-1, nargs='?', const=DEBUG_ITERS
					   ,help='Add extra print statements')
	args = parser.parse_args()
	if not (1 <= args.cache_size <= 8192):
		parser.error('-s cache size is out of range.  int between 1 and 8192') 

	if not (4 <= args.block_size <= 64):
		parser.error('-b block size is out of range. Select int between 4 and 64') 
	if args.block_size not in [2**i for i in range(2, 7)]:
		parser.error('-b block size is not a power of 2. Select int between 4 and 64') 

	if args.debug >= 0:
			DEBUG = True
			DEBUG_ITERS = args.debug

	fmt = "%(levelname)s: %(message)s"	
	logging.basicConfig(filename=sys.argv[0]+'.log', format=fmt, level=logging.INFO)
	
	# adds logging to console (for WARNING and CRITICAL levels only)
	consoleHandler = logging.StreamHandler(sys.stdout)
	consoleHandler.setFormatter(logging.Formatter(fmt))
	if DEBUG:
		consoleHandler.setLevel(logging.DEBUG)
	else:
		consoleHandler.setLevel(logging.INFO)
	logging.getLogger().addHandler(consoleHandler)

	# shows debug logging
	if args.debug:
		logging.getLogger().setLevel(logging.DEBUG)

	return args


if __name__ == '__main__':
	start_time = time.time()
	main()
	time_str = f"{time.time() - start_time:.3f}"
	print(f"\n{time_str+' Seconds':-^{H_SIZE}}")