from django.db import models

# Create your models here.
class Stocks(models.Model):
    ticker = models.CharField(max_length=5)
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    date = models.CharField(max_length=255)
    def __str__(self):
        return self.ticker

class StockUserData(models.Model):
    ticker = models.CharField(max_length=10)
    name = models.CharField(max_length=255)
    datebought = models.DateField()
    datesold = models.DateField()
    amountbought = models.DecimalField(decimal_places=2, max_digits=9)
    dollarchange = models.DecimalField(decimal_places=2,max_digits=10, default=0)
    percentchange = models.DecimalField(decimal_places=2, max_digits=10, default=0)

# class StockData(models.Model):
#     date = models.CharField(max_length=255)


