def balance_problem(supply, demand, profit):
    total_supply = sum(supply)
    total_demand = sum(demand)

    balanced_supply = supply.copy()
    balanced_demand = demand.copy()
    balanced_profit = [row.copy() for row in profit]

    dummy_demand_amount = max(0, total_supply - total_demand)
    dummy_supply_amount = max(0, total_demand - total_supply)

    balanced_demand.append(dummy_demand_amount)
    for row in balanced_profit:
        row.append(0)

    balanced_supply.append(dummy_supply_amount)
    balanced_profit.append([0] * len(balanced_demand))

    balance_note = (
        f"Dodano fikcyjnego odbiorcę o popycie {dummy_demand_amount} "
        f"i fikcyjnego dostawcę o podaży {dummy_supply_amount}."
    )

    return (
        balanced_supply,
        balanced_demand,
        balanced_profit,
        True,
        balance_note,
        dummy_supply_amount,
        dummy_demand_amount,
    )


def northwest_corner_allocation(supply, demand):
    rows = len(supply)
    cols = len(demand)
    allocations = [[0 for _ in range(cols)] for _ in range(rows)]

    i = 0
    j = 0
    remaining_supply = supply.copy()
    remaining_demand = demand.copy()

    while i < rows and j < cols:
        quantity = min(remaining_supply[i], remaining_demand[j])
        allocations[i][j] = quantity
        remaining_supply[i] -= quantity
        remaining_demand[j] -= quantity

        if remaining_supply[i] == 0 and remaining_demand[j] == 0:
            if i < rows - 1 and j < cols - 1:
                i += 1
                j += 1
            elif i < rows - 1:
                i += 1
            else:
                j += 1
        elif remaining_supply[i] == 0:
            i += 1
        else:
            j += 1

    return allocations


def calculate_total_profit(allocations, profit):
    total_profit = 0
    for i in range(len(allocations)):
        for j in range(len(allocations[0])):
            total_profit += allocations[i][j] * profit[i][j]
    return total_profit


def build_basic_cells(allocations):
    rows = len(allocations)
    cols = len(allocations[0])
    basic = {(i, j) for i in range(rows) for j in range(cols) if allocations[i][j] > 0}
    target = rows + cols - 1

    def connected(row, col, edges):
        visited_rows = {row}
        visited_cols = set()
        row_queue = [row]
        while row_queue:
            r = row_queue.pop()
            for c in range(cols):
                if (r, c) in edges and c not in visited_cols:
                    visited_cols.add(c)
                    for rr in range(rows):
                        if (rr, c) in edges and rr not in visited_rows:
                            visited_rows.add(rr)
                            row_queue.append(rr)
        return col in visited_cols

    for i in range(rows):
        for j in range(cols):
            if len(basic) >= target:
                break
            if allocations[i][j] == 0 and (i, j) not in basic and not connected(i, j, basic):
                basic.add((i, j))
        if len(basic) >= target:
            break

    return basic


def calculate_uv_potentials(basic_cells, profit):
    rows = len(profit)
    cols = len(profit[0])
    u = [None] * rows
    v = [None] * cols

    u[0] = 0
    changed = True
    while changed:
        changed = False
        for i, j in basic_cells:
            if u[i] is not None and v[j] is None:
                v[j] = profit[i][j] - u[i]
                changed = True
            if v[j] is not None and u[i] is None:
                u[i] = profit[i][j] - v[j]
                changed = True

    for idx in range(rows):
        if u[idx] is None:
            u[idx] = 0
    for idx in range(cols):
        if v[idx] is None:
            v[idx] = 0

    return u, v


def compute_reduced_costs(basic_cells, cost, profit, blocked_suppliers=None):
    if blocked_suppliers is None:
        blocked_suppliers = []
    rows = len(cost)
    cols = len(cost[0])
    u, v = calculate_uv_potentials(basic_cells, cost)

    reduced_costs = []
    for i in range(rows):
        for j in range(cols):
            # If supplier is blocked, disallow allocation to dummy column
            if blocked_suppliers and i in blocked_suppliers and j == cols - 1:
                continue
            if (i, j) in basic_cells:
                continue
            reduced_cost = cost[i][j] - u[i] - v[j]
            reduced_profit = -reduced_cost
            reduced_costs.append({
                "cell": (i, j),
                "profit": profit[i][j],
                "reduced_cost": reduced_cost,
                "reduced_profit": reduced_profit,
            })

    reduced_costs.sort(key=lambda item: item["reduced_profit"], reverse=True)
    return reduced_costs, u, v


def fix_blocked_suppliers_allocations(allocations, blocked_suppliers, real_cols_count):
    """
    For each blocked supplier, ensure there is no allocation to the dummy column
    (last column). If there is, attempt to move that quantity to real columns by
    shifting allocations from non-blocked suppliers to the dummy column.
    Returns True if all blocked suppliers were fixed, False if some remainder
    could not be reassigned.
    """
    rows = len(allocations)
    cols = len(allocations[0])
    dummy_col = cols - 1

    for i in blocked_suppliers or []:
        if i < 0 or i >= rows:
            continue
        need = allocations[i][dummy_col]
        if need <= 0:
            continue

        # Try to move `need` to real columns
        for j in range(real_cols_count):
            if need <= 0:
                break
            # Look for a supplier k (not blocked) that currently supplies column j
            for k in range(rows):
                if k == i:
                    continue
                if blocked_suppliers and k in blocked_suppliers:
                    continue
                available = allocations[k][j]
                if available <= 0:
                    continue
                transfer = min(available, need)
                # move transfer from k->j to k->dummy, and from i->dummy to i->j
                allocations[k][j] -= transfer
                allocations[k][dummy_col] += transfer
                allocations[i][j] += transfer
                allocations[i][dummy_col] -= transfer
                need -= transfer
                if need <= 0:
                    break

        # if after trying all real cols we still have need>0, we couldn't satisfy constraint
        if allocations[i][dummy_col] > 0:
            # leave as is and report failure
            return False

    return True


def find_cycle(basic_cells, start_cell, rows, cols):
    basic_set = set(basic_cells)

    def search(path, horizontal):
        current = path[-1]
        if len(path) >= 4 and current == start_cell:
            return path

        if horizontal:
            candidates = [(current[0], col) for col in range(cols) if col != current[1]]
        else:
            candidates = [(row, current[1]) for row in range(rows) if row != current[0]]

        for next_cell in candidates:
            if next_cell == start_cell:
                if len(path) >= 4:
                    return path + [next_cell]
                continue
            if next_cell in basic_set and next_cell not in path:
                result = search(path + [next_cell], not horizontal)
                if result:
                    return result

        return None

    loop = search([start_cell], True)
    if loop:
        return loop
    return search([start_cell], False)


def improve_solution(allocations, cost, profit, blocked_suppliers=None):
    rows = len(cost)
    cols = len(cost[0])
    basic_cells = build_basic_cells(allocations)
    
    # Ochrona przed nieskończoną pętlą przy degeneracji
    degeneration_counter = 0
    max_degeneration_iterations = rows + cols

    while True:
        reduced_costs, u, v = compute_reduced_costs(basic_cells, cost, profit, blocked_suppliers)
        if not reduced_costs or reduced_costs[0]["reduced_profit"] <= 0:
            optimal = True
            break

        entering = reduced_costs[0]["cell"]
        cycle = find_cycle(basic_cells, entering, rows, cols)
        if not cycle:
            optimal = False
            break

        # Usuń powtórzenie start_cell na końcu cyklu
        cycle_without_dup = cycle[:-1]
        minus_cells = cycle_without_dup[1::2]
        
        theta = min(allocations[i][j] for i, j in minus_cells)

        # Nawet gdy theta = 0 (degeneracja), przesuwamy strukturę bazowych komórek
        # Iteruj cycle[:-1] bo ostatni element to duplikat start_cell
        for idx, (i, j) in enumerate(cycle_without_dup):
            if idx % 2 == 0:
                allocations[i][j] += theta
            else:
                allocations[i][j] -= theta

        # Licznik degeneracji
        if theta == 0:
            degeneration_counter += 1
            if degeneration_counter > max_degeneration_iterations:
                # Algorytm nie robi postępu - możliwa pętla przy degeneracji
                print(f"Zatrzymanie: degeneracja przez {degeneration_counter} iteracji")
                optimal = False
                break
        else:
            degeneration_counter = 0

        # Usuń z bazy wszystkie trasy, które stały się zerowe
        zero_cells = {(i, j) for i, j in minus_cells if allocations[i][j] == 0}

        # Wybierz komórkę do usunięcia z bazy
        leaving = None
        for cell in minus_cells:
            if allocations[cell[0]][cell[1]] == 0:
                leaving = cell
                break
        
        if leaving is None and theta > 0:
            leaving = min(minus_cells, key=lambda cell: allocations[cell[0]][cell[1]])

        # Aktualizuj bazowe komórki
        basic_cells.add(entering)
        if leaving and leaving in basic_cells:
            basic_cells.remove(leaving)

        for cell in zero_cells:
            if cell in basic_cells and cell != entering:
                basic_cells.remove(cell)

        if len(basic_cells) != rows + cols - 1:
            basic_cells = build_basic_cells(allocations)

    reduced_costs, u, v = compute_reduced_costs(basic_cells, cost, profit, blocked_suppliers)
    if reduced_costs and reduced_costs[0]["reduced_profit"] > 0:
        optimal = False

    return allocations, optimal, reduced_costs


def nw_corner_solver(supply, demand, profit, blocked_suppliers=None):
    total_supply = sum(supply)
    total_demand = sum(demand)
    (
        balanced_supply,
        balanced_demand,
        balanced_profit,
        dummy_added,
        balance_note,
        dummy_supply_amount,
        dummy_demand_amount,
    ) = balance_problem(supply, demand, profit)

    internal_costs = [[-value for value in row] for row in balanced_profit]
    if blocked_suppliers is None:
        blocked_suppliers = []

    allocations = northwest_corner_allocation(balanced_supply, balanced_demand)

    # Ensure blocked suppliers do not send to dummy receiver (last column)
    real_cols = len(demand)
    blocked_ok = fix_blocked_suppliers_allocations(allocations, blocked_suppliers, real_cols)

    allocations, is_optimal, reduced_costs = improve_solution(allocations, internal_costs, balanced_profit, blocked_suppliers)

    trimmed_allocations = [row[: len(demand)] for row in allocations[: len(supply)]]
    total_profit = calculate_total_profit(trimmed_allocations, profit)

    return {
        "allocations": trimmed_allocations,
        "full_allocations": allocations,
        "total_profit": total_profit,
        "balanced": True,
        "dummy_added": True,
        "balance_note": balance_note,
        "dummy_supply_amount": dummy_supply_amount,
        "dummy_demand_amount": dummy_demand_amount,
        "is_optimal": is_optimal,
        "optimality_details": (
            "Rozwiązanie jest optymalne: wszystkie zyski alternatywne są niedodatnie."
            if is_optimal
            else f"Rozwiązanie nie jest optymalne. Największy dodatni zysk alternatywny: {reduced_costs[0]['reduced_profit']} w komórce {reduced_costs[0]['cell']}"
        ),
        "reduced_costs": reduced_costs,
        "blocked_suppliers_ok": blocked_ok,
        "blocked_suppliers": blocked_suppliers,
    }


def print_matrix(matrix, row_labels=None, col_labels=None):
    if col_labels:
        print("   ", end="")
        for label in col_labels:
            print(f"{label:>8}", end="")
        print()

    for i, row in enumerate(matrix):
        label = row_labels[i] if row_labels else str(i)
        print(f"{label:>3}", end="")
        for value in row:
            print(f"{value:>8}", end="")
        print()


if __name__ == "__main__":
    supply = [12, 12]
    demand = [10, 10]
    profit = [
        [3, 1],
        [2, -2]
    ]

    result = nw_corner_solver(supply, demand, profit)

    print("--- Dane wejściowe ---")
    print(f"Podaż: {supply}")
    print(f"Popyt: {demand}")
    print(f"Fikcyjny odbiorca: {result['dummy_demand_amount']}")
    print(f"Fikcyjny dostawca: {result['dummy_supply_amount']}")
    print(f"Uwagi balansera: {result['balance_note']}\n")

    print("--- Zyski (z prawdziwymi i fikcyjnymi trasami) ---")
    cost_labels = [f"Odb{i+1}" for i in range(len(demand))] + ["Fikcyjny"]
    supply_labels = [f"Dost{i+1}" for i in range(len(supply))] + ["Fikcyjny"]
    print_matrix(result['full_allocations'], row_labels=supply_labels, col_labels=cost_labels)

    print("\n--- Wynik alokacji ---")
    print("Realne trasy:")
    print_matrix(result['allocations'], row_labels=[f"Dost{i+1}" for i in range(len(supply))], col_labels=[f"Odb{i+1}" for i in range(len(demand))])
    print(f"\nCałkowity zysk na realnych trasach: {result['total_profit']}")
    print(f"Optymalne? {'tak' if result['is_optimal'] else 'nie'}")
    print(result['optimality_details'])
    if not result['is_optimal']:
        print("\nDodatnie zyski alternatywne:")
        for item in result['reduced_costs'][:5]:
            print(item)
