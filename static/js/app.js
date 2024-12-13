document.getElementById('transport-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const supply = document.getElementById('supply').value;
    const demand = document.getElementById('demand').value;
    const costs = document.getElementById('costs').value;
    const method = document.getElementById('method').value;

    try {
        const response = await fetch('/solve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ supply, demand, costs, method })
        });
        const data = await response.json();
        if (response.ok) {
            // Crear tabla para mostrar la asignación
            const allocationTable = generateTable(data.allocation);

            document.getElementById('results').innerHTML = `
                <h2>Resultado</h2>
                <p>Asignación:</p>
                ${allocationTable}
                <p><b>Costo Total:</b> ${data.total_cost}</p>
            `;
        } else {
            document.getElementById('results').innerHTML = `<p>Error: ${data.error}</p>`;
        }
    } catch (error) {
        document.getElementById('results').innerHTML = `<p>Error: ${error.message}</p>`;
    }
});

// Función para generar una tabla HTML a partir de una matriz
function generateTable(matrix) {
    let table = '<table border="1" style="border-collapse: collapse; text-align: center;">';
    matrix.forEach(row => {
        table += '<tr>';
        row.forEach(cell => {
            table += `<td>${cell}</td>`;
        });
        table += '</tr>';
    });
    table += '</table>';
    return table;
}
