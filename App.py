from flask import Flask, request, jsonify, render_template
import numpy as np

app = Flask(__name__)

# Validación de las entradas: equilibrar supply y demand si no coinciden
def balancear_supply_demand(supply, demand, costs):
    if supply.sum() > demand.sum():
        # Agregar columna ficticia (demanda)
        diff = supply.sum() - demand.sum()
        demand = np.append(demand, diff)
        costs = np.column_stack((costs, np.zeros(costs.shape[0])))
    elif supply.sum() < demand.sum():
        # Agregar fila ficticia (suministro)
        diff = demand.sum() - supply.sum()
        supply = np.append(supply, diff)
        costs = np.row_stack((costs, np.zeros(costs.shape[1])))
    return supply, demand, costs

# Algoritmo de Mínimo Costo
def minimo_costo(supply, demand, costs):
    # Crear copia de los datos
    supply = supply.copy()
    demand = demand.copy()
    allocation = np.zeros_like(costs)
    
    # Usar máscara para manejar valores infinitos
    masked_costs = np.ma.MaskedArray(costs, mask=np.isinf(costs))
    
    while np.any(supply > 0) and np.any(demand > 0):
        # Encuentra el índice del menor costo
        i, j = np.unravel_index(np.argmin(masked_costs), costs.shape)
        
        # Asignar el mínimo entre suministro y demanda
        asignacion = min(supply[i], demand[j])
        allocation[i, j] = asignacion
        
        # Actualizar suministro y demanda
        supply[i] -= asignacion
        demand[j] -= asignacion
        
        # Marcar la celda como no disponible (inf)
        costs[i, j] = np.inf
        masked_costs.mask[i, j] = True  # Actualizar la máscara

    return allocation


# Algoritmo de Aproximación de Vogel (VAM)
def vogel_approximation(supply, demand, costs):
    supply = supply[:]  # Hacer una copia de supply
    demand = demand[:]  # Hacer una copia de demand
    allocation = [[0] * len(demand) for _ in supply]  # Crear una matriz de asignación

    iteration = 0  # Añadimos un contador de iteraciones para depuración

    while sum(supply) > 0 and sum(demand) > 0:
        iteration += 1
        print(f"Iteración {iteration}")
        print(f"Suministro: {supply}")
        print(f"Demanda: {demand}")

        penalties = []  # Lista para almacenar las penalizaciones

        # Calcular penalizaciones para filas
        for i, s in enumerate(supply):
            if s > 0:  # Solo calcular para filas con suministro positivo
                row = sorted((c, j) for j, c in enumerate(costs[i]) if demand[j] > 0)
                if len(row) > 1:
                    penalty = row[1][0] - row[0][0]  # Penalización de fila
                else:
                    penalty = row[0][0]  # Si solo hay un valor, usarlo como penalización
                penalties.append((penalty, i, 'row'))

        # Calcular penalizaciones para columnas
        for j, d in enumerate(demand):
            if d > 0:  # Solo calcular para columnas con demanda positiva
                col = sorted((costs[i][j], i) for i in range(len(supply)) if supply[i] > 0)
                if len(col) > 1:
                    penalty = col[1][0] - col[0][0]  # Penalización de columna
                else:
                    penalty = col[0][0]  # Si solo hay un valor, usarlo como penalización
                penalties.append((penalty, j, 'col'))

        penalties.sort(reverse=True)  # Ordenar las penalizaciones de mayor a menor
        print(f"Penalizaciones calculadas: {penalties}")

        if not penalties:  # Si no hay penalizaciones válidas, romper el ciclo
            break

        _, idx, mode = penalties[0]  # Elegir la mejor penalización

        if mode == 'row':
            i = idx
            j = min((j for j, d in enumerate(demand) if d > 0), key=lambda j: costs[i][j])
        else:
            j = idx
            i = min((i for i, s in enumerate(supply) if s > 0), key=lambda i: costs[i][j])

        qty = min(supply[i], demand[j])  # Determinar la cantidad a asignar
        allocation[i][j] = qty  # Asignar la cantidad en la celda correspondiente
        supply[i] -= qty  # Actualizar el suministro
        demand[j] -= qty  # Actualizar la demanda

        print(f"Asignando {qty} a la celda ({i}, {j})")
        print(f"Suministro actualizado: {supply}")
        print(f"Demanda actualizada: {demand}")
    
    return allocation

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    try:
        # Leer los datos de la petición
        data = request.json
        supply = np.array([int(x) for x in data['supply'].split(',')])
        demand = np.array([int(x) for x in data['demand'].split(',')])
        costs = np.array([[int(cell) for cell in row.split(',')] for row in data['costs'].strip().split('\n')])

        method = data['method']
        
        # Llamar al método adecuado
        if method == 'minimo_costo':
            allocation = minimo_costo(supply, demand, costs.copy())
        elif method == 'vam':
            allocation = vogel_approximation(supply, demand, costs.copy())
        else:
            return jsonify({'error': 'Método desconocido'}), 400

        total_cost = np.sum(allocation * costs)  # Calcular el costo total de la asignación

        # Asegurarse de que `allocation` sea un array de numpy para realizar operaciones
        allocation = np.array(allocation)  # Convertir la asignación a un array de numpy si no lo es
        allocation_list = allocation.astype(int).tolist()  # Convertir la matriz de numpy a lista de Python con enteros
        total_cost = float(total_cost)  # Convertir el costo total a un tipo estándar float

        return jsonify({'allocation': allocation_list, 'total_cost': total_cost})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
