import MetaTrader5 as mt5

result = mt5.initialize()

print("CONNECTED:", result)

if result:
    account = mt5.account_info()

    print(account)

    mt5.shutdown()