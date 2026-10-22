lst = ['a','c','xyz', 5, 9, 'z', 'x', 5, 'a']

mydict = {}

for i in lst:
    mydict[i] = mydict.get(i,0)+1
print(mydict)
