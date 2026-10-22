# Data Collections - list
# Q1. Find the length of a list.
# lst = [10, 22, 26, 35, 99]
# print(len(lst))

# Q2. Find the largest number, Q3. smallest number
# lst = [25, 66, 78, 99, 125, 108, 111, 145, 154, 25, 33, 154, 165, 25, 69, 222, 154, 98, 44]
# print(max(lst))
# print(min(lst))

# Q4. Calculate sum of all elements
# lst = [25, 66, 78, 99, 125, 108, 111, 145, 154, 25, 33, 154, 165, 25, 69, 222, 154, 98, 44]
# print(sum(lst))

# Q5. Reverse a list?
# lst = [25, 66, 78, 99, 125, 108, 111, 145, 154, 25, 33, 154, 165, 25, 69, 222, 154, 98, 44]
# print(lst[::-1])
# for string and list both are in the same way 
# s = 'automation'
# print(s[::-1])

# Q6. Remove duplicates?
# lst = [25, 66, 78, 99, 125, 108, 111, 145, 154, 25, 33, 154, 165, 25, 69, 222, 154, 98, 44]
# result = list(set(lst))
# print(result)

# Q7. Count occurrences of each element?
# lst = ['a','c','xyz', 5, 9, 'z', 'x', 5, 'a']
# from collections import Counter
# print(Counter(lst))
# for string and list both are in the same way
# s = 'automation'
# from collections import Counter
# print(Counter(s)) 

# other way without using Counter class using for loop and dictionary for elements count occurrences of each element
# lst = ['a','c','xyz', 5, 9, 'z', 'x', 5, 'a']
# mydict = {}
# for i in lst:
#     mydict[i] = mydict.get(i,0)+1
# print(mydict)

# other way without using Counter class using for loop and dictionary
# s = 'automnation'
# mydict = {}
# for i in s:
#     mydict[i] = mydict.get(i, 0)+1
# print(mydict)

# Q8. Find duplicate elements?

# lst = ['UFT','SEL','PW','UFT','SEL']
# using list
# duplicates = []
# # seen = []
# for i in lst:
#     if lst.count(i)>1:
#         if i not in duplicates:
#             duplicates.append(i)
#     # else:
#     #         seen.append(i)
# print(duplicates)
# # print(seen)

# using set
# lst = ['UFT','SEL','PW','UFT','SEL']
# duplicates = set()
# seen = set()
# for item in lst:
#     if item in seen:
#         duplicates.add(item)
#     else:
#         seen.add(item)
        
# print(duplicates)
# print(seen)

# find duplicates in a string using list - same way of find duplicate characters in list - both list and string using the same methods of way doing 

# s = 'pytonautomationtesting'
# duplicates = []

# for i in s:
#     if s.count(i)>1:
#         if i not in duplicates:
#             duplicates.append(i)
# print(duplicates)

# Find Duplicate Characters with Their Counts
# s = 'pytonautomationtesting'
# # for i in s:
#     if s.count(i)>1:
#        print(f' {i} -> {s.count(i)}')




    









# # list1 + list2 concatenates the lists into one list.
# zip() expects two or more iterables, but you're passing a single combined list.
# zip() returns a zip object, so you need to convert it to a list to see the contents.
# Q1. combine a two lists and return in tuples
# list1 = [2, 5, 6,9]
# list2 = ['a', 'b', 'd', 'g']

# list3 = list(zip(list1, list2))
# print(list3) # [(2, 'a'), (5, 'b'), (6, 'd'), (9, 'g')]

# For Python interview questions, remember:

# zip(list1, list2) pairs elements position-wise from multiple iterables.

# Q2. Combine a two list of lists?

# list1 = [2, 5, 6,9]
# list2 = ['a', 'b', 'd', 'g']

# list3 = [[x,y] for x, y in zip(list1, list2)]
# print(list3)

# Q3. combine two lists into a one list
# list1 = ['Tomota','Greenary','Carrot','Potato','Ladys finger'] 
# list2 = ['Grapes','Banana','Apples']
# print(list1+list2)

# Q4. find a duplicate elements in a list?
# list1 = ['UFT','SEL','PW','UFT','SEL','UFT','PY','AUT','PW']

# duplicates = []
# seen = []

# for i in list1:
#     if list1.count(i)>1:
#         if i not in duplicates:
#             duplicates.append(i)
#     else:
#         seen.append(i)
# print(f'Duplicate elements in a list: {duplicates}')
# print(f'Seen element only once in a list: {seen}')

# Q5. Count a repeated elments in a list?

# list1 = ['UFT','SEL','PW','UFT','SEL','UFT','PY','AUT','PW']

# duplicates = []
# seen = []

# for i in list1:
#     if list1.count(i)>1:
#         if i not in duplicates:
#             duplicates.append(i)
#     else:
#         seen.append(i)
# print(f'Duplicate elements in a list: {duplicates} : count of duplicated elements : {len(duplicates)}')
# print(f'Seen element only once in a list: {seen} : count of elements seen only once : {len(seen)}')
        
# Q6. Merge of two dictionaires?
# dict1 = {'student':'Navya','College':'S.V.U'}
# dict2 = {'Location': 'Tpt','Stream':'M.P.C'}
# print(dict1 | dict2)

# other way
# dict1 = {'student':'Navya','College':'S.V.U'}
# dict2 = {'Location': 'Tpt','Stream':'M.P.C'}
# print({**dict1, **dict2})

# Q7. Merge of two lists?
# list1 = [1,2,5,6,8]
# list2 = ['a', 'd', 'p', 11, 15]
# # print(list1+list2)
# # other way       
# list1.extend(list2)
# print(list1)

