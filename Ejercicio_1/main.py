def Find_last_position(N: int, M: int) -> str:
    if(N > M):
        return "U" if M % 2 == 0 else "D"
    else:
        return "L" if N % 2 == 0 else "R"
        
if __name__ == "__main__":
    cases = int(input("Number of test cases: "))
    for _ in range(cases):
        N, M = map(int, input().split())
        print(f"Result: {Find_last_position(N, M)}")