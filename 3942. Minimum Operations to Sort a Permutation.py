
class Solution:
    def minOperations(self, nums: List[int]) -> int:
        n = len(nums)
        zero = nums.index(0)

        increasing = all(
            nums[(zero + i) % n] == i
            for i in range(n)
        )

        decreasing = all(
            nums[(zero - i) % n] == i
            for i in range(n)
        )

        if increasing:
            return min(zero, n - zero + 2)

        if decreasing:
            return min(zero + 2, n - zero)

        return -1
