import math
def required_bits(n: int) -> int:
    if n == 0:
        return 1
    return n.bit_length()


def enumerate_compositions(target, val_range):
    solutions = []

    def backtrack(current, current_sum):
        if current_sum == target:
            solutions.append(current.copy())
            return
        if current_sum > target:
            return

        for num in val_range:
            if current_sum + num <= target:
                current.append(num)
                backtrack(current, current_sum + num)
                current.pop()

    backtrack([], 0)
    return solutions



def enumerate_bit_compositions(target, val_range):
    """
    Enumerate all compositions using integers from val_range such that
    2^(sum of the composition) equals the target.
    
    Parameters:
      target (int): The target decimal value (should be a power of 2).
      val_range (iterable of int): Allowed integers, each treated as a bit count.
      
    Returns:
      list of lists: Each inner list is a composition whose parts sum to log2(target).
    """
    # Check if target is a power of 2
    if target <= 0 or (target & (target - 1)) != 0:
        raise ValueError("Target must be a power of 2.")
    
    bit_target = int(math.log2(target))
    solutions = []
    
    def backtrack(current, current_sum):
        # If the sum of parts equals bit_target, we have a valid composition.
        if current_sum == bit_target:
            solutions.append(current.copy())
            return
        # If we exceed the required bit sum, backtrack.
        if current_sum > bit_target:
            return

        # Try each allowed value.
        for num in val_range:
            if current_sum + num <= bit_target:
                current.append(num)
                backtrack(current, current_sum + num)
                current.pop()

    backtrack([], 0)
    return solutions



# 8, 16, 32 or 64
max_addr_size = 16
n_bytes = [4,6,8]
ab = [4,5,6,7,8] # allowed addr bits
an = [2,3,4,5,6] # allowed addr bit mult
allowed_schema_bits = [ 4, 5, 6, 7, 8]
addr_bits = 8
addr_n = 2

# schema byte = NUMBER, REFERENCE HARDCODED, NOT LITERALLY IN THE CODE
# just find how many ways you can split addr_size to represent values

segment = [8] * addr_bits * addr_n
ps = []
for i in segment:
    ps.append(f"uint{i}_t")

tot = []

schemas = []
addr_size = addr_n * addr_bits
addr_space = 2**addr_size
compositions = enumerate_bit_compositions(addr_space, allowed_schema_bits)
compositions.sort(reverse=True)
#print()
#print(f"Compositions of {addr_size} using integers {ab}:")

#print('Network schemas')
#print(f"N        Words    Composition          Address         Nodes      Groups")
md = []
for combo in compositions:
    #print(combo)
    addr = ""
    seqs = []
    tn = 1
    for j in combo:
        qwe = (2**j) - 1
        seqs.append(qwe)
        tn = tn * qwe
        addr += str(qwe)+"."
    seqs.pop()
    tnt = 1
    for j in seqs:
        tnt = tnt * j
    addr = addr[:len(addr)-1]
    #print(f"{compositions.index(combo):<8} {len(combo):<8} {str(combo):<20} {addr:<15} {tn:<10} {tnt:<10}")
    schemas.append([combo, f"{compositions.index(combo)+1:<8} {len(combo):<8} {str(combo):<20} {addr:<15} {tn:<10} {tnt:<10}"])
    md.append(f"| {compositions.index(combo)+1} | {len(combo)} | {str(combo)} | {addr} | {tn} | {tnt} |")
#print(f"Total number of compositions: {len(compositions)}")


schema_bits = required_bits(len(compositions))
segment_size = 8 + (addr_size*2)

if segment_size <= (8 + (max_addr_size*2)): 
    print()
    print("#" * 24)
    print(f"Address: {addr_size} bits ({addr_bits} bit * {addr_n})")
    print(f"Address space: {addr_space:,}")
    print(f"Total Address representation bits (Addr * 2): {addr_size*2}")
    print()
    print('Network schemas')
    print(f"N        Words    Bits combo           Address         Nodes      Groups")
    for i, j in schemas:
        print(j)
    print(f"Possible network schemas: {len(compositions)}")
    print(f"Schema representation bits: {schema_bits}")
    print(f"Segment size: {segment_size/8} bytes")
    #print('Segment space:', segment_space, 'bits')
    print('Packet segment: ',ps)
    print()
    # print(f"Packet segment: [Schema ({schema_bits} bits), Sender ({addr_size} bits), Destination ({addr_size} bits)] ({segment_space} bits)")
else:
    pass
    #print(f"- Too big: Packet segment utilization: {segment_size} / {segment_space}")

x= []
for combo, _ in schemas:
    x.append(combo)
print(x)
print()
for i in md:
    print(i)