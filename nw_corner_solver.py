def nw_corner_solver(supply, demand, costs):
    s = supply.copy()
    d = demand.copy()
    
    rows = len(s)
    cols = len(d)
    
    allocations = [[0 for _ in range(cols)] for _ in range(rows)]
    
    i = 0 
    j = 0 
    
    while i < rows and j < cols:
        quantity = min(s[i], d[j])
        
        allocations[i][j] = quantity
        
        s[i] -= quantity
        d[j] -= quantity
        
        if s[i] == 0:
            i += 1
        elif d[j] == 0:
            j += 1

    total_cost = 0
    for r in range(rows):
        for c in range(cols):
            total_cost += allocations[r][c] * costs[r][c]
            
    return allocations, total_cost

if __name__ == "__main__":
    supply = [300, 400, 500]
    demand = [250, 350, 400, 200]
    costs = [
        [3, 1, 7, 4],
        [2, 6, 5, 9],
        [8, 3, 3, 2]
    ]

    result, cost = nw_corner_solver(supply, demand, costs)
    
    print("Macierz przydziałów:")
    for row in result:
        print(row)
        
    print(f"\nCałkowity koszt: {cost}")