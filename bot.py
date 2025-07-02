import requests

def get_briefing():
    # Получаем курс USD/PLN
    try:
        rate_resp = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=PLN")
        usd_pln = round(rate_resp.json()["rates"]["PLN"], 4)
    except:
        usd_pln = "н/д"

    # Получаем цену нефти Brent с Yahoo Finance (через YFinance)
    try:
        price_resp = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/CL=F?range=1d&interval=1h")
        data = price_resp.json()
        close = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
        brent = round([p for p in reversed(close) if p][0], 2)
    except:
        brent = "н/д"

    # Сформировать сводку
    return (
        f"📡 *Геополитическая сводка — обновление*\n\n"
        f"🌍 *Ближний Восток*\n"
        f"- Иран усиливает киберактивность, Ормуз без обострений.\n"
        f"- Ливан и Израиль: нестабильное перемирие, риски сохраняются.\n\n"
        f"💱 *Финансовые рынки*\n"
        f"- USD/PLN: *{usd_pln}* PLN\n"
        f"- Brent: *{brent}* USD\n"
        f"- DXY: понижается (источник не подключён)\n\n"
        f"🔮 *Прогноз*\n"
        f"- При снижении риска в регионе доллар может немного ослабнуть.\n"
        f"_Обновлено автоматически ботом_"
    )
