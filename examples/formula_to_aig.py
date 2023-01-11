import aiger

a,b,c,d,e,f,g,h = aiger.atoms('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h')

aig1 = (a | (b & c)) & ((b & c).implies(d | e)) 

c3 = aiger.to_aig(aig1)
print(c3)