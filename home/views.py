from unicodedata import name
from django.http import response
from django.db.models import Q
from django.http.response import JsonResponse
from django.views.generic import ListView, CreateView, DeleteView, UpdateView
from django.urls.base import reverse_lazy
from django.shortcuts import render, redirect
from django.conf import settings
from home.models import Asset, Portfolio
from home.forms import AssetForm, PortfolioForm

import requests
import pandas_datareader.data as web
from pandas.io.json import json_normalize
from yahoo_fin import options
import plotly.express as px
import plotly
import pandas as pd 
import datetime

# ALPHA VANTAGE API
api = settings.API_KEYS["alpha-vantage"]
url = api["host"]
key = api["key"]

class MainView(ListView):
    """
    Main view displaying accounts and assets - asset_list.html
    """
    model = Asset
    template_name = "home/asset_list.html"
    success_url = reverse_lazy('home:all')


    #def get_context_data(self,**kwargs):
    def get(self, request) :
        context = {}
        
        # Get Accounts
        invest_accounts = Portfolio.objects.filter(type="investment")
        saving_accounts = Portfolio.objects.filter(type="saving")
        if not invest_accounts:
            portfolio = Portfolio(name="Default", cash=0.00)
            portfolio.save()
            invest_accounts = [portfolio]
        
        # Track Investment Running Totals
        investment_list = []
        invest_total_book = 0
        invest_total_market = 0
        invest_total_cash = 0

        # Track Savings Running Totals
        saving_list = []
        total_cash = 0
        saving_cash = 0

        # Saving Account
        for account in saving_accounts:
            saving_list.append(account)
            saving_cash += account.cash
            total_cash += account.cash
            account.cash = "{:,}".format(round(account.cash,2))

        # Investment Account
        df_total = pd.DataFrame()
        for account in invest_accounts:
            asset_set = account.asset_set.all()
            
            # Plot Account Balance History
            plot_div = None
            acct_series = account_balance_series(account)
            if not acct_series.empty:
                fig = plot_acct_balance(acct_series, acct_series.name)
                plot_div = plotly.offline.plot(fig, output_type='div')
                df_total = pd.concat([df_total, acct_series], axis=1 )
            
            # Calculate running total of investments 
            invest_total_book += float(account.bookval) 
            invest_total_cash += float(account.cash) 
            invest_total_market += float(account.marketval) 

            investment_list.append( {"account":account, "assets":asset_set, "plot_div":plot_div}  )
            
        

        # Account & Asset Details 
        context["savings_list"] = saving_list
        context["investment_list"] = investment_list

        # Net Investment Accounts 
        total = round((invest_total_market + (invest_total_cash - invest_total_book) ), 2)
        context["invest_total"] = total

        # Total Net Worth
        total_cash = float(total_cash) + invest_total_cash - invest_total_book
        total_net = round(total_cash + invest_total_market,2)
        context["net_total"] = total_net

        # Plot Total Accounts Balance History
        df_total.fillna(method='ffill', inplace=True)
        col_names =list(df_total)
        df_total["total"] = df_total[col_names].sum(axis=1)
        df_total["total"] = df_total["total"] + float(saving_cash) # Add Saving Cash
        fig_total = plot_acct_balance(df_total, "total")
        fig_total['data'][0]['line']['color']='rgb(6, 23, 1)'
        fig_total['data'][0]['line']['width']=2
        plot_div_total = plotly.offline.plot(fig_total, output_type='div')
        context["plot_div_total"] = plot_div_total
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        refresh_asset_quotes()
        refresh_portfolio_quotes()
        return redirect(self.success_url)


def plot_acct_balance(df, col):
    """
    Create figure of portfolio performance
    
    :param df: Dataframe of accounts
    :param col: account name
    :return fig: Figure depicting plot
    """
    fig = px.line(df, x=df.index, y=col)
    fig.update_layout(title_text='')
    fig.update_xaxes(title_text='')
    fig.update_yaxes(title_text='')
    return fig  

def account_balance_series(account):
    """
    Create Series depicting historical value of account

    :param account: Account name
    :return df[name]: Series depicting historical value of account
    """
    # Dataframe to track historical Account Balance
    df = pd.DataFrame()

    # Get Options PNL - No price history available
    options = account.asset_set.filter(Q(type="option"))
    option_pnl = 0 
    if options:
         option_pnl = sum((float(option.current_price) - float(option.entry_price))*float(option.size)*100 for option in options)

    # Get Equity/Crypto to fetch historical price data 
    assets = account.asset_set.filter(Q(type="equity")| Q(type="crypto")).order_by('purchase_date')
    if assets:
        
        # Fix Crypto name for API Call      
        name_list = []
        for asset in assets: 
            if asset.type == "crypto":
                fix_name = asset.name.replace("USD","-USD")
                asset.name = fix_name
            name_list.append(asset.name)
        
        # Fetch istorical price data 
        # NOTE: Have to use yahoo given AlphaVantage api limit resitricitons
        df = web.DataReader(name_list, 'yahoo', start=assets[0].purchase_date, end=datetime.datetime.today().strftime('%Y-%m-%d'))
        df = df["Close"]

        # Add begining cash balance and track running
        df["acct_balance"] = float(account.cash)
        running_balance = float(account.cash) 

        # Calculate and store value of assets + cash per day
        for asset in assets:
            df.loc[:asset.purchase_date, asset.name] = 0
            size = df.loc[asset.purchase_date:, asset.name] * float(asset.size)
            df.loc[asset.purchase_date:, asset.name] = size
            running_balance = float(running_balance) - float(asset.bookval)
            df.loc[asset.purchase_date + datetime.timedelta(days=1):, "acct_balance"] =  running_balance
        
        # Forward fill NA with prev value (Occurs because of holidays given equity+crypto)
        df.fillna(method='ffill', inplace=True)
        
        # Calculate total account value (includes pnl)
        name = account.name + "_balance"
        col_names =list(df)
        df[name] = df[col_names].sum(axis=1)
        df[name] = df[name] + option_pnl

    return df[name]



def refresh_asset_quotes():
    """
    Fetch current price of assets and update model in DB
    """

    portfolios = Portfolio.objects.all() 

    for portfolio in portfolios:
        crypto_equity_set = portfolio.asset_set.filter(Q(type="crypto") | Q(type="equity"))
        option_set = portfolio.asset_set.filter(type="option")

        # Refresh Equity and Crypto Prices - Alph Vantage
        for asset in crypto_equity_set:
            try:
                # API Call Logic
                querystring = {"function":"GLOBAL_QUOTE","symbol":asset.name,"apikey":key}
                response = requests.request("GET", url, params=querystring)
                data = response.json() 
                price = round(float(data["Global Quote"]['05. price']),2)
                print("Asset:{}  Price:{}".format(asset.name, price))
               
               # Populate asset fields and save
                asset.current_price = price
                asset = populate_asset_fields(asset)
                asset.save()
            except requests.exceptions.HTTPError as e:
                print("Failed to update ASSET Price for {}".format(asset.name) )
                print (e.response.text)
        
        # Refresh Option Prices - yahoo_fin
        for asset in option_set:
            try:
                # API Call Logic
                ticker = asset.name
                expiry_date = asset.option_expiry.strftime('%m/%d/%y')
                chain = options.get_options_chain(ticker, expiry_date)
                option_type = asset.option_type
                price = chain[option_type][chain[option_type]['Strike'] == asset.option_strike]["Last Price"]
                print("Asset:{} Option Price:{}".format(ticker, price))
                
                # Populate asset fields and save
                asset.current_price = round(price.item(),2)
                asset = populate_asset_fields(asset)
                asset.save()
            except requests.exceptions.HTTPError as e:
                print("Failed to update OPTION Price for {}".format(asset.name) )
                print (e.response.text)

def refresh_portfolio_quotes():
    """
    Update portfolio summary quotes in DB using up-to-date asset prices
    NOTE: Function is called after refresh_asset_quotes
    """

    portfolios = Portfolio.objects.filter(type="investment")
    for account in portfolios:

        # Calculate Account quote
        asset_set = account.asset_set.all()
        account_book = sum(float(asset.bookval) for asset in asset_set)
        account_market = sum(float(asset.marketval) for asset in asset_set)
        begin_balance = float(account.cash)
        account_total = (account_market + (begin_balance - account_book))

        # Set Account fields and Save
        account.marketval = round(account_market,2)
        account.bookval =  round(account_book,2)
        account.net_cash = round(begin_balance - account_book,2)
        account.c_yield= round((account_market - account_book), 2)
        account.total = round(account_total, 2)
        if account_book > 0:
            account.p_yield= round((account_total/begin_balance -1) * 100, 2)
        else: 
            account.p_yield = 0 
        account.save()


def populate_asset_fields(asset):
    """
    Update asset fields

    :param asset: asset object
    :return asset: asset object
    """
    
    # Adjust for option. Contract = 100 shares
    adj = 1
    if (asset.type == "option"):
        adj = 100

    # Calculate and populate asset fields
    current_price  = float(asset.current_price)
    size = float(asset.size)
    entry_price = float(asset.entry_price)
    book_value = round(entry_price * (size*adj),2)
    market_value = round(current_price * (size*adj),2)    
    asset.profit = round(market_value - book_value,2)
    asset.marketval = market_value
    asset.bookval = book_value

    return asset

class AssetCreate(CreateView):
    """
    Create Asset View - asset_form.html
    """
    model = Asset
    form_class = AssetForm
    success_url = reverse_lazy('home:all')


class AssetUpdate(UpdateView):
    """
    Update Asset View - asset_form.html
    """
    model = Asset
    form_class = AssetForm
    success_url = reverse_lazy('home:all')

class AssetDelete(DeleteView):
    """
    Delete Asset View - asset_confirm_delete.html
    """
    model = Asset
    fields = '__all__'
    success_url = reverse_lazy('home:all')

class PortfolioCreate(CreateView):
    """
    Create Portfolio(account) View - portfolio_form.html
    """
    model = Portfolio
    form_class = PortfolioForm
    success_url = reverse_lazy('home:all')

class PortfolioUpdate(UpdateView):
    """
    Update Portfolio(account) View - portfolio_form.html
    """
    model = Portfolio
    form_class = PortfolioForm
    success_url = reverse_lazy('home:all')

class PortfolioDelete(DeleteView):
    """
    Delete Portfolio(account) View - portfolio_confirm_delete.html
    """
    model = Portfolio
    fields = '__all__'
    success_url = reverse_lazy('home:all')
 