
import sys
import os
import math
from os import path
import argparse
import logging
from ctypes import c_uint
import random
from collections import Counter

# -f <trace file name>     [ name of text file with the trace ]
# -s <cache block size>    [ 1 KB to 8 MB ]
# -b <block size>          [ 4 bytes to 64 bytes ]
# -a <associativity>       [ 1, 2, 4, 8, 16 ]
# -r <replacement policy>  [RR or RND or LRU for bonus points]

DEFAULT_EXECUTION_CYCLES = 2
DEFAULT_MEM_ACCESS_CYCLES = 3
BUS_SIZE = 4
GLOBAL_CLOCK = 0

def main():
	
	args = parse_args()
	print_header(sys.argv, args)
	cache = Cache(cache_size=args.cache_size, block_size=args.block_size, associativity=args.associativity
				 , rep_policy=args.rep_policy)
	cache.display()
	full_instructions = read_instructions(args.trace_file)
	hit_rate, miss_rate, cpi, tot_hits, tot_misses,tot_accesses = cache_simulator(cache, full_instructions)
	print_results(hit_rate, miss_rate, cpi, tot_hits, tot_misses, tot_accesses)
	if args.debug:
		print_samples(full_instructions, num_print=20)   


def cache_simulator(cache, full_instructions):
	num_instructions = len(full_instructions)
	tot_mem_accesses = 0
	tot_hits = 0
	tot_misses = 0
	tot_cycles = 0
	counts = Counter()
	for g, full_instruction in enumerate(full_instructions):
		num_remaining_requests = full_instruction.get_num_mem_requests()
		
		counts[num_remaining_requests] +=1
		#print(num_remaining_requests)
		while num_remaining_requests > 0:
			next_request, num_remaining_requests = full_instruction.next_mem_request()
			# print('curr request:', next_request.to_string())
			# print('num_remaining:', num_remaining_requests)
			hits, misses, cycles = process_request(next_request, cache,g)
			hits = hits #if hits <= 1 else 1
			misses = misses #if misses <= 1 else 1
			tot_hits += hits #if hits <= 1 else 1
			tot_misses += misses #if misses <= 1 else 1
			tot_cycles += cycles
			tot_mem_accesses += hits +misses
			#counts[cycles] +=1 
			#print(hits, misses, cycles)
		# if g >= 1000:
		# 	num_instructions = g
		# 	break
		# 	print(tot_hits, tot_misses, tot_cycles)
		# 	sys.exit()
	print(counts)
	# s = sum([int(val)*int(key) for key,val in counts.items()])
	# [print(str(key)+': '+str(int(val)*int(key)/s)) for key,val in counts.items()]
	# print(num_instructions)
	denom = tot_hits + tot_misses
	return tot_hits/denom, tot_misses/denom, tot_cycles/num_instructions, tot_hits, tot_misses, tot_mem_accesses

def process_request(mem_access_request, cache, n):
	global GLOBAL_CLOCK
	#print('global clock:', GLOBAL_CLOCK)
	cycles = DEFAULT_EXECUTION_CYCLES
	bytes_to_read = mem_access_request.length
	address = mem_access_request.address
	hits = 0
	misses = 0
	#t = 0
	# print('\nxxxxxxx start address:%x'%address)
	# print('xxxxxxx start address:', bin(address))
	while bytes_to_read > 0:
		# print('xxxxxxx new address:%x'%address)
		# print('xxxxxxx new address:', bin(address))
		# print('bytes to read:', bytes_to_read)
		GLOBAL_CLOCK = GLOBAL_CLOCK + 1
		# print('global clock:', GLOBAL_CLOCK)
		bytes_read= cache.read_from_cache(address, bytes_to_read)
		
		
		if bytes_read <= 0: # miss
			# print('MISS!', n)
			cache.replace_block(address)
			bytes_read= cache.read_from_cache(address, bytes_to_read)
			misses += 1
			
			cycles += DEFAULT_MEM_ACCESS_CYCLES * math.ceil(cache.block_size/BUS_SIZE)+1
			

		else: # hit 
			# print('HIT!')
			cycles += 1
			hits += 1
		# print('bytes read from cache:', bytes_read)
		# print('cycles:', cycles)
		bytes_to_read -= bytes_read
		address += bytes_read
		# print('bytes remaining to read:', bytes_to_read)
		# t += 1
		# if t >5:
		# 	return hits, misses, cycles
	return hits, misses, cycles

	


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
		self.cols = [Block(col_index=a) for a in range(associativity)]
		self.next_for_round_robin = 0
		

	def contains_valid_tag(self, tag, p=False):
		# if p:
		# 	print('####CHECKING####', tag)
		for block in self.cols:
			# if p:
			# 	print(block.to_string())
			if block.tag == tag and block.valid:
				block.update_clock()
				return True
		return False

	def replace(self, idx, tag):
		if type(idx) != int:
			idx = int(idx)
		x = self.cols.pop(idx)
			# print(tag, 'clock for evicted:', x.last_used, ' curr clock:', GLOBAL_CLOCK)

		self.cols.insert(idx, Block(tag=tag, valid=1, col_index=idx))

class Cache():
	def __init__ (self, cache_size=0, block_size=0, associativity=0, rep_policy=None):
		self.cache_size = cache_size * 1024
		#print('ssssss ', self.cache_size)
		self.block_size = block_size
		self.associativity = associativity
		self.rep_policy = rep_policy
		
		if not math.log2(self.cache_size).is_integer():
			self.cache_size = 2**math.floor(math.log(self.cache_size,2))
			logging.warning('Cache size is not a power of 2. Reducing cache size to '+str(self.cache_size//1024)+'kb')
		self.total_blocks = self.cache_size // self.block_size
		self.number_of_indeces = math.ceil(self.cache_size  /(self.block_size * self.associativity))  # of indexes with associativity
		self.block_offset_bits = math.ceil(math.log(block_size, 2)) # get the offset bits
		self.index_bits = math.ceil(math.log(self.number_of_indeces, 2))  # get the index bits
		self.tag_bits = 32 - self.block_offset_bits - self.index_bits  #tag bits
		self.overhead = self.total_blocks*(1 + self.tag_bits)//8
		self.implementation = self.overhead +self.cache_size
		self.c = [CacheRow(self.associativity, i) for i in range(self.number_of_indeces)]


	def replace_block(self, address):
		tag, idx, b_offset = self.get_address_pieces(address)
		row = self.c[idx]
		# print('idx:',idx)
		# row.contains_valid_tag(tag, p=True)
		# print('next for rr:', row.next_for_round_robin)
		if self.rep_policy == 'RND':
			rem_idx = random.randint(0, row.associativity-1)
			# print('rem_idx:', rem_idx)
			# row.replace(rem_idx, tag)
		elif self.rep_policy == 'RR':
			rem_idx = row.next_for_round_robin
			# print('rem_idx:', rem_idx)
			# row.replace(rem_idx, tag)
			row.next_for_round_robin = (row.next_for_round_robin+1) % row.associativity
		elif self.rep_policy == 'LRU':
			rem_idx = row.cols.index(min(row.cols, key=lambda x: x.last_used))
		# print('rem_idx:', rem_idx)
		row.replace(rem_idx, tag)

		#return BUS_SIZE if BUS_SIZE < (self.block_size - b_offset) else (self.block_size - b_offset)

	def read_from_cache(self, address, bytes_to_read):
		tag, idx, b_offset = self.get_address_pieces(address)
		# print('!!address:', bin(address))
		# print(address)
		# print('!!b_offset:', bin(b_offset))
		# print(b_offset)
		# print('!!tag:', bin(tag))
		# print(tag)
		# print('!!idx:', bin(idx))
		# print(idx)
		# print('!!bob:',self.block_offset_bits)
		# print('!!idxbits:',self.index_bits)
		# print(len(self.c))
		row = self.c[idx]
		if row.contains_valid_tag(tag):
			spill_over = (b_offset +BUS_SIZE) > self.block_size and (b_offset +bytes_to_read) > self.block_size 
			if spill_over:
				bytes_read = self.block_size - b_offset 
				#print('!!SPILL OVER!!bytes read:', bytes_read)
			else:
				bytes_read = bytes_to_read if  bytes_to_read < BUS_SIZE else BUS_SIZE
				#print('!!!!bytes read:', bytes_read)

			return bytes_read 
		else:

			return 0


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




def print_results(hit_rate, miss_rate, cpi, tot_hits, tot_misses, tot_accesses):
    #TODO: fill out results once cache is implemented
    print('----- Results -----')
    print('Cache Hit Rate: %.2f%%'%( hit_rate*100))
    print('Cache Miss Rate: %.2f%%'%(miss_rate*100))
    print('CPI: %.2f'%(cpi), '\n')
    print('tot hits:', tot_hits)
    print('tot misses:', tot_misses)
    print('tot accesses:', tot_accesses)


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
                            if next_full_instruct.instruction.length > 0:
                                    instruction_list.append(next_full_instruct)

                            # reset for next set of instructions
                            next_full_instruct = None
    return instruction_list





def parse_args():
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
	parser.add_argument('-d', dest='debug', action='store_true', help='Add extra print statements')
	args = parser.parse_args()
	if not (1 <= args.cache_size <= 8192):
		parser.error('-s cache size is out of range.  int between 1 and 8192') 

	if not (4 <= args.block_size <= 64):
		parser.error('-b block size is out of range. Select int between 4 and 64') 
	if args.block_size not in [2**i for i in range(2, 7)]:
		parser.error('-b block size is not a power of 2. Select int between 4 and 64') 

	fmt = "%(levelname)s: %(message)s"	
	logging.basicConfig(filename=sys.argv[0]+'.log', format=fmt, level=logging.INFO)
	
	# adds logging to console (for WARNING and CRITICAL levels only)
	consoleHandler = logging.StreamHandler(sys.stdout)
	consoleHandler.setFormatter(logging.Formatter(fmt))
	if args.debug:
		consoleHandler.setLevel(logging.DEBUG)
	else:
		consoleHandler.setLevel(logging.WARNING)
	logging.getLogger().addHandler(consoleHandler)

	# shows debug logging
	if args.debug:
		logging.getLogger().setLevel(logging.DEBUG)

		

	return args


if __name__ == '__main__':
        main()