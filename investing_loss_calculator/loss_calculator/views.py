from django.shortcuts import render,HttpResponseRedirect
import yfinance as yf
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar
from pandas.tseries.offsets import CustomBusinessDay
from datetime import datetime, timedelta
from .models import StockUserData
from sqlalchemy import create_engine, text, inspect
from django.conf import settings

databaseSettings = settings.DATABASES['default']
db_url = f"postgresql+psycopg://{databaseSettings['USER']}:{databaseSettings['PASSWORD']}@{databaseSettings['HOST']}:{databaseSettings['PORT']}/{databaseSettings['NAME']}"
print("database url: " + db_url)
engine = create_engine(db_url)

YFINANCE_TABLE = 'yfinanceStockData'
USER_RECORD_TABLE = 'loss_calculator_stockuserdata'
TEMP_FINANACE_TABLE = 'temp_stock_data'
US_BUSINESS_DAY = CustomBusinessDay(calendar=USFederalHolidayCalendar())
# Create your views here.
def home(request):
    error = ""
    userStocks = ""



    prices_dataframe = pd.DataFrame()
    prices_dataframe.to_sql(TEMP_FINANACE_TABLE, engine, if_exists='replace', index=True)


    

    if request.method == "POST":

        stockticker = request.POST.get('ticker')
        name = request.POST.get('name')


        datebought = request.POST.get('datebought')
        datesold = request.POST.get('datesold')



        amountbought = request.POST.get('amountbought')

        #change date to last busness day
        startDate = pd.Timestamp(datebought)
        endDate = pd.Timestamp(datesold)
        while not US_BUSINESS_DAY.is_on_offset(startDate):
            startDate = startDate - 1 * US_BUSINESS_DAY

        while not US_BUSINESS_DAY.is_on_offset(endDate): #checks US_BUSINESS_DAY calender to see if date is not on holiday or weekend (returns false)
            endDate = endDate - 1 * US_BUSINESS_DAY
        
        
        datebought = startDate
        datesold = endDate
        
        print(f"DATE BOUGHT: {datebought} DATE SOLD: {datesold}")


        if stockticker and name and datebought and datesold and amountbought:
            try:
                stock = StockUserData(ticker=stockticker, name=name, datebought=datebought, datesold=datesold, amountbought=amountbought, dollarchange=0, percentchange=0)
                
                #['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'] #availible options

                data = yf.download(stockticker, start=datebought,end=datesold + pd.Timedelta(days=1)) #adding 1 day becasuse parameter end is non inclusive of date
                if data.empty: #error if ticker did not pull any data
                    error = "Not Valid data"
                    return render(request, 'base.html', {'stocks':userStocks, 'error' : error} )
                

                for column in ['Open', 'High', 'Low', 'Close', 'Volume']:
                    if column in data.columns:
                        prices_dataframe[f'{stockticker} {column}'] = data[column]
                    else:
                        print("no data in column")
                stock.save()
                print(prices_dataframe)
            except: # error if date and time are not correct format
                error = "Not Valid data"
                return render(request, 'base.html', {'stocks':userStocks, 'error' : error} )
                
        

        if not prices_dataframe.empty:
            #add to database
            prices_dataframe.to_sql(TEMP_FINANACE_TABLE, engine, if_exists='replace', index=True)
            print("WROTE STOCK DATA TO TEMP TABLE")

            df_list = prices_dataframe.columns.tolist()
            columns_formatted = "\"Date\", " + ', '.join(f"\"{item}\"" for item in df_list)
            
            print(f"DATAFREAME LIST FORMATTED: {columns_formatted}")


            query = f" SELECT {columns_formatted} FROM public.\"{TEMP_FINANACE_TABLE}\""
            temp_data = pd.read_sql(query, engine) 
            

            query = f" SELECT * FROM public.\"{YFINANCE_TABLE}\""
            all_data = pd.read_sql(query, engine)

            print('SELECTED COLUMNS FROM STOCK DATA TABLE temp_stock_data')

            if not all_data.empty:
                print("RUN IF STAT")
                
                all_data_merge = all_data.merge(temp_data,how='outer').sort_values('Date').drop_duplicates()
                all_data_merge.to_sql(YFINANCE_TABLE, engine, if_exists='replace', index=False)
                print(f"ALL DATA MERGERD: {all_data_merge}")
                #check and filter before joining

            else:
                print("RUN ELSE STAT")
                all_data = temp_data
                all_data.to_sql(YFINANCE_TABLE, engine, if_exists='replace', index=False)
                #write to main db

            

            print(f"EXISTING DATA: {all_data}")
            print(f"TEMP_DATA: {temp_data}")
            
            
            print("END")

        else:
            print("No data available for stock")

        userStock = StockUserData.objects.filter(ticker=stockticker, datebought=datebought, datesold=datesold, amountbought=amountbought).first()#11.33 changed and added more filters

        with engine.begin() as con:

            columnFilter = "Date"
            columnFilter2 = f"{userStock.ticker} Close"
            
            value = userStock.datebought
            startDateQuery = f"SELECT \"{columnFilter2}\" FROM public.\"{YFINANCE_TABLE}\" WHERE \"{columnFilter}\" = '{value}'"
            print(f"QUERY START: {startDateQuery}")
            beginValues = con.execute(text(startDateQuery)).fetchone()
            

            value = userStock.datesold
            endDateQuery = f"SELECT \"{columnFilter2}\" FROM public.\"{YFINANCE_TABLE}\" WHERE \"{columnFilter}\" = '{value}'"
            print(f"QUERY END: {endDateQuery}")
            endValues = con.execute(text(endDateQuery)).fetchone()


            print(f"BEGINING VALUES: {beginValues}")
            print(f"ENDING VALUES {endValues}")


        totalChange, percentChange = calculateTotalNet(beginValues, endValues, amountbought) #takes in stock values of buy and sell date and amount bought
        userStock.dollarchange = totalChange
        userStock.percentchange = percentChange
        userStock.save(update_fields=['dollarchange', 'percentchange'])
        print("CHANGED USERSTOCK") #updates stock user entry to contain percent and total gain/lss
        
        #check db for end date
        #if db returns none then pull from yfinance
        #write to db yfinance records without adding duplicates

        #take end date and start date prices
        # stock change = subtract end date price by start date price
        # number of shares = divide how much invested by start date price 
        #  multiply stock change by number of shares

        #each time form is submitted save result 
        return HttpResponseRedirect("/")
    
    # prices_dataframe.to_sql(YFINANCE_TABLE, engine, if_exists='replace', index=True)#down here becasue if above if POST will run always
    # StockUserData.objects.all().delete()# but if here, it will only run when GET

    userStocks = StockUserData.objects.all()

    return render(request, 'base.html', {'stocks':userStocks, 'error':error } )

def reset_db(request):
    if request.method == "POST":
        StockUserData.objects.all().delete()

        with engine.begin() as con:
            query = f"DELETE FROM public.\"{YFINANCE_TABLE}\""
            con.execute(text(query))  
            query = f"DELETE FROM public.{TEMP_FINANACE_TABLE}"
            con.execute(text(query))    

        return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")

def calculateTotalNet(beginValues, endValues, amountBought):
    stockChange = endValues[0] - beginValues[0]
    amountOfStock = int(amountBought) /beginValues[0] 
    totalChange = stockChange * amountOfStock
    percentChange = (stockChange/endValues[0]) * 100
    print(f"PERCENT CHANGE : {percentChange}")


    return totalChange, percentChange