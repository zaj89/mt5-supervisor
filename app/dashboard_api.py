from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.performance_tracker import performance_tracker
from app.mt5_manager import mt5_manager
from app.risk_manager import risk_manager
from app.trading_hours import trading_hours
from app.logger import logger

app = FastAPI()

connected = mt5_manager.initialize()

if connected:
    logger.info("Dashboard connected to MT5")
else:
    logger.error("Dashboard failed to connect to MT5")


@app.get("/api/status")
def get_status():
    account = mt5_manager.get_account_info()

    if account is None:
        return {
            "error": "MT5 disconnected"

        }

    state = risk_manager.get_state()

    return {
        "balance": account.balance,
        "equity": account.equity,
        "margin_free": account.margin_free,

        "trading_blocked": state["trading_blocked"],
        "block_reason": state["block_reason"],

        "daily_profit_target": state["daily_profit_target"],
        "daily_loss_limit": state["daily_loss_limit"],

        "trading_time": trading_hours.is_trading_time(),

        "positions": mt5_manager.get_positions()
    }


@app.get("/", response_class=HTMLResponse)
def dashboard():
    return """

    <html>

    <head>

    <title>MT5 Supervisor</title>

    <style>

    body {
        background: #0f1117;
        color: #e6edf3;
        font-family: Arial;
        padding: 20px;
    }

    h1 {
        margin-bottom: 30px;
    }

    .grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 20px;
    }

    .card {
        background: #1c2128;
        padding: 20px;
        border-radius: 12px;
    }

    .label {
        font-size: 14px;
        color: #8b949e;
        margin-bottom: 10px;
    }

    .value {
        font-size: 32px;
        font-weight: bold;
    }

    .green {
        color: #3fb950;
    }

    .red {
        color: #f85149;
    }

    .orange {
        color: orange;
    }

    .positions {
        margin-top: 30px;
        background: #1c2128;
        border-radius: 12px;
        padding: 20px;
    }

    table {
        width: 100%;
        border-collapse: collapse;
    }

    th, td {
        padding: 12px;
        border-bottom: 1px solid #30363d;
        text-align: left;
    }

    </style>

    </head>

    <body>

    <h1>MT5 Supervisor Dashboard</h1>

    <div class="grid">

        <div class="card">
            <div class="label">Balance</div>
            <div class="value" id="balance">-</div>
        </div>

        <div class="card">
            <div class="label">Equity</div>
            <div class="value" id="equity">-</div>
        </div>

        <div class="card">
            <div class="label">Trading Status</div>
            <div class="value" id="blocked">-</div>
        </div>

        <div class="card">
            <div class="label">Trading Hours</div>
            <div class="value" id="trading_time">-</div>
        </div>

    </div>
<div
    class="card"
    style="margin-top:30px;"
>

    <h2>Performance Growth</h2>

    <canvas id="performanceChart"></canvas>

</div>
    <div class="positions">

        <h2>Open Positions</h2>

        <table>

            <thead>
                <tr>
                    <th>Ticket</th>
                    <th>Symbol</th>
                    <th>Type</th>
                    <th>Lot</th>
                    <th>Profit</th>
                </tr>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            </thead>

            <tbody id="positions_table">

            </tbody>

        </table>

    </div>

    <script>

    async function updateDashboard() {

        const response = await fetch('/api/status');

        const data = await response.json();

        if (data.error) {
            console.log(data.error);
            return;
        }

        document.getElementById('balance').innerText =
            data.balance.toFixed(2);

        document.getElementById('equity').innerText =
            data.equity.toFixed(2);

        document.getElementById('blocked').innerText =
            data.trading_blocked ? 'BLOCKED' : 'ACTIVE';

        document.getElementById('blocked').className =
            'value ' + (data.trading_blocked ? 'red' : 'green');

        document.getElementById('trading_time').innerText =
            data.trading_time ? 'OPEN' : 'CLOSED';

        document.getElementById('trading_time').className =
            'value ' + (data.trading_time ? 'green' : 'orange');

        const table = document.getElementById('positions_table');

        table.innerHTML = '';

        data.positions.forEach(position => {

            const row = `
                <tr>
                    <td>${position.ticket}</td>
                    <td>${position.symbol}</td>
                    <td>${position.type}</td>
                    <td>${position.volume}</td>
                    <td class="${position.profit >= 0 ? 'green' : 'red'}">
                        ${position.profit}
                    </td>
                </tr>
            `;

            table.innerHTML += row;
        });
    }
let chart;


async function loadPerformanceChart() {

    const response =
        await fetch('/api/performance');

    const data = await response.json();

    const labels =
        data.map(x => x.date);

    const balance =
        data.map(x => x.balance);

    const target =
        data.map(x => x.target_curve);

    const deposit =
        data.map(x => x.deposit);

    const ctx =
        document.getElementById(
            'performanceChart'
        );

    if (chart) {
        chart.destroy();
    }

    chart = new Chart(ctx, {

        type: 'line',

        data: {

            labels: labels,

            datasets: [

                {
                    label: 'Balance',
                    data: balance,
                    borderWidth: 3
                },

                {
                    label: '1% Daily Target',
                    data: target,
                    borderDash: [5, 5],
                    borderWidth: 2
                },

                {
                    label: 'Deposit',
                    data: deposit,
                    borderWidth: 2
                }
            ]
        },

        options: {

            responsive: true,

            scales: {

                y: {
                    beginAtZero: false
                }
            }
        }
    });
}
    updateDashboard();

loadPerformanceChart();

setInterval(loadPerformanceChart, 60000);

    setInterval(updateDashboard, 1000);

    </script>

    </body>

    </html>

    """


@app.get("/api/performance")
def get_performance():
    return performance_tracker.get_performance_data()
