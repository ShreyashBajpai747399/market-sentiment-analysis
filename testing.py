nums=[3,3]

for i in range(0,len(nums)-1):
    num=6-nums[i]
    if num in nums[i+1:]:
        print(i,nums.index(num))
