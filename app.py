from flask import Flask, render_template, request, jsonify
from nw_corner_solver import nw_corner_solver

app = Flask(__name__)

@app.route('/p/solve-nw-c', methods=['POST'])
def solve_nw_c():
    num_rows = int(request.form.get('num_rows'))
    num_cols = int(request.form.get('num_cols'))
    
    supply = []
    demand = []
    profits = []
    buying_price = []
    selling_price = []

    for i in range(num_rows):
        val = int(request.form.get(f'supply_{i}'))
        supply.append(val)

    for i in range(num_rows):
        val = int(request.form.get(f'buying_price_{i}'))
        buying_price.append(val)

    for j in range(num_cols):
        val = int(request.form.get(f'demand_{j}'))
        demand.append(val)

    for j in range(num_cols):
        val = int(request.form.get(f'selling_price_{j}'))
        selling_price.append(val)

    for i in range(num_rows):
        row_profits = []
        for j in range(num_cols):
            val = int(request.form.get(f'cost_{i}_{j}'))
            row_profits.append(selling_price[j] -  val - buying_price[i])
        profits.append(row_profits)
    # Odczytaj zablokowanych dostawców (wysyłane jako JSON z frontendu)
    import json
    blocked_suppliers_json = request.form.get('blocked_suppliers', '[]')
    try:
        blocked_suppliers = json.loads(blocked_suppliers_json)
    except Exception:
        blocked_suppliers = []

    result = nw_corner_solver(supply, demand, profits, blocked_suppliers=blocked_suppliers)

    results = {
        "supply": result.get("supply", supply),
        "demand": result.get("demand", demand),
        "profit": result.get("profit", profits),
        "allocations": result["allocations"],
        "total_profit": result.get("total_profit"),
        "balanced": result["balanced"],
        "dummy_added": result["dummy_added"],
        "balance_note": result["balance_note"],
        "is_optimal": result["is_optimal"],
        "optimality_details": result["optimality_details"],
    }

    return jsonify(results)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)