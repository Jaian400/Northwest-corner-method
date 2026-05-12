from flask import Flask, render_template, request, jsonify
from nw_corner_solver import nw_corner_solver

app = Flask(__name__)

@app.route('/p/solve-nw-c', methods=['POST'])
def solve_nw_c():
    num_rows = int(request.form.get('num_rows'))
    num_cols = int(request.form.get('num_cols'))
    
    supply = []
    demand = []
    costs = []

    for i in range(num_rows):
        val = int(request.form.get(f'supply_{i}'))
        supply.append(val)

    for j in range(num_cols):
        val = int(request.form.get(f'demand_{j}'))
        demand.append(val)

    for i in range(num_rows):
        row_costs = []
        for j in range(num_cols):
            val = int(request.form.get(f'cost_{i}_{j}'))
            row_costs.append(val)
        costs.append(row_costs)

    allocations, total_cost = nw_corner_solver(supply, demand, costs)

    results = {
        "supply": supply,
        "demand": demand,
        "costs": costs,
        "allocations": allocations,
        "total_cost": total_cost
    }

    return jsonify(results)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)