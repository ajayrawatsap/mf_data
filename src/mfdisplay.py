
import random
import pandas as pd

import src.constants as ct

from plotly.subplots import make_subplots
from plotly import graph_objects as go


def format_amount_cols(df:pd.DataFrame, amount_cols:list[str])->pd.DataFrame:
  # Format amounts to  Rupee symbol, comma seperator and 2 decimals
  for col in amount_cols:    
    df[col] = df[col].map('\u20B9{:,.2f}'.format)
  return df

def format_unit_perc_cols(df:pd.DataFrame, columns:list[str])->pd.DataFrame:
  # Format amounts to  Rupee symbol, comma seperator and 2 decimals
  for col in columns:    
    df[col] = df[col].map('{:,.2f}'.format)
  return df

def convert_date_object_to_string(df:pd.DataFrame, columns:list[str])->pd.DataFrame:
    #Since dates are of type datetime.date need to convert to str and then to datetime 
    df[columns] =  df[columns].astype(str).apply(pd.to_datetime, format = ct.DATE_FORMAT_EXT)
    for col in columns:        
      df[col]  = df[col].dt.strftime(ct.DATE_FORMAT)
    return df


def get_hdr_data_to_display(hdr_df_in:pd.DataFrame)->pd.DataFrame:
    hdr_df = hdr_df_in
    hdr_df = hdr_df.drop(columns = ['folio_no', 'isin', 'amc','scheme_code'])


    amount_cols = ['invested_amt', 'ltcg', 'stcg', 'current_amt', 'target_ltcg', 'target_amt']
    hdr_df  = format_amount_cols(hdr_df, amount_cols)


    date_cols = ['latest_nav_date']
    hdr_df = convert_date_object_to_string(hdr_df, date_cols)


    unit_perc_cols = ['latest_nav',		'gf_nav',	'units', 'perc_gain',	'target_units']
    hdr_df = format_unit_perc_cols(hdr_df, unit_perc_cols)
    return hdr_df

def get_trans_data_to_display(trans_df_in:pd.DataFrame)->pd.DataFrame:
    trans_df = trans_df_in
    trans_df  = trans_df.drop(columns = ['folio_no', 'isin', 'units_balance', 'amc','scheme_code'])


    amount_cols = ['invested_amt', 'ltcg', 'stcg', 'cumil_ltcg', 'current_amt']
    trans_df  = format_amount_cols(trans_df, amount_cols)

    date_cols = ['trans_date', 'latest_nav_date']
    trans_df = convert_date_object_to_string(trans_df, date_cols)

    unit_perc_cols = ['latest_nav',		'gf_nav', 'new_purch_nav', 'units', 'purch_nav', 'perc_gain', 'cumil_units']
    trans_df = format_unit_perc_cols(trans_df, unit_perc_cols)
    return trans_df

def get_trans_for_single_scheme(trans_df:pd.DataFrame, scheme_name:str = None)->pd.DataFrame:
    if not scheme_name:
        schemes = list(set(trans_df.scheme_name.to_list()))
        random_idx= random.randint(0, len(schemes)-1)
        scheme_name = schemes[random_idx]    
    
    return trans_df[trans_df.scheme_name == scheme_name]


def group_by_mf_type(mf_hdr_df:pd.DataFrame)->pd.DataFrame:
    agg = { 'Invested Amount': pd.NamedAgg(column= 'invested_amt', aggfunc = 'sum'),
            'Current Amount': pd.NamedAgg(column= 'current_amt', aggfunc= 'sum'),
            'Total LTCG': pd.NamedAgg(column = 'ltcg', aggfunc= 'sum'),
            'Total STCG': pd.NamedAgg(column= 'stcg', aggfunc= 'sum')
            }


    mf_totals_grp =  mf_hdr_df.groupby('type').agg(**agg).reset_index() 
    mf_totals_grp['Total Gain']  = mf_totals_grp['Current Amount'] - mf_totals_grp['Invested Amount']
    mf_totals_grp['Gain Percent'] = (mf_totals_grp['Total Gain'] /  mf_totals_grp['Invested Amount']) * 100


    columns = mf_totals_grp.columns.tolist()
    columns.remove('type') 

    mf_totals_grp[columns] = mf_totals_grp[columns].astype(float).round(2)
    return mf_totals_grp


def display_summary(mf_totals_grp)-> None:
    total_invested_amt = mf_totals_grp['Invested Amount'].sum()
    total_current_amt = mf_totals_grp['Current Amount'].sum()
    total_gain = mf_totals_grp['Total Gain'].sum()
    # perc_gain = round((total_gain / total_invested_amt) * 100, 2)

    total_amounts = [total_invested_amt, total_current_amt , total_gain]
    amount_names = ['Invested Amount','Current Amount', 'Gain/Loss']
    fig = go.Figure( data = [

                            go.Bar( name = f"Current Amount ({ct.RUPEEE_SYMBOL})",  x =  total_amounts ,  y=  amount_names, orientation = 'h',
                                    text =  total_amounts , textposition='outside', texttemplate='%{text:.2s}'
                                    ),
                            
                            
                            ])

    fig.update_layout(         
                  
                    height=350,
                    title = 'Portfolio Summary'
                    )
    fig.show()  


def display_equity_vs_debt(mf_totals_grp:pd.DataFrame)->pd.DataFrame:


     totals_df = mf_totals_grp
     mf_types = totals_df.type.to_list()


     fig = make_subplots(rows=2, cols=2, 
                         specs=[
                              [{"type": "bar"}, {"type": "bar"}],
                              [{"type": "pie"}, {"type": "bar"}]
                              ],
                         subplot_titles=("Portfolio Amounts", "Capital Gains (LTCG/STCG)", " ", "Gain % (Absolute)"))

     # Subplot1: Invested Anount, Current Amount, Gain
     invested_amount = totals_df['Invested Amount']
     current_amount = totals_df['Current Amount']
     gain =  totals_df['Total Gain']


     fig.add_trace(
          go.Bar(name= f"Current Amount ({ct.RUPEEE_SYMBOL})",x = current_amount, y=mf_types, orientation = 'h',  legendgroup = '1',
                                        text = current_amount, textposition='outside', texttemplate='%{text:.2s}'),
     row=1,
     col=1,
     
     )


     fig.add_trace(
          go.Bar(name=  f"Invested Amount ({ct.RUPEEE_SYMBOL})", x= invested_amount, y= mf_types, orientation = 'h',  legendgroup = '1',
                                   text = invested_amount, textposition='outside', texttemplate='%{text:.2s}' ),
     
          row = 1,
          col = 1,
     
     )


     fig.add_trace(
          
          go.Bar(name=  f"Gain/Loss ({ct.RUPEEE_SYMBOL})", x= gain, y= mf_types, orientation = 'h',  legendgroup = '1',
                                   text = gain, textposition='outside', texttemplate='%{text:.2s}' ),
          row = 1,
          col = 1,
     
     )


     # Subplot2:LTCG and STCG
     ltcg = totals_df['Total LTCG']
     stcg = totals_df['Total STCG']

     fig.add_trace(
          
          go.Bar(name= f"Total LTCG ({ct.RUPEEE_SYMBOL})",x = ltcg, y=mf_types, orientation = 'h',  legendgroup = '2',
                                        text = ltcg, textposition='outside', texttemplate='%{text:.2s}'),
          row = 1,
          col = 2,
          

     )

     fig.add_trace(    
          
          go.Bar(name=  f"Total STCG ({ct.RUPEEE_SYMBOL})", x= stcg, y= mf_types, orientation = 'h', legendgroup = '2',
                                   text = stcg, textposition='outside', texttemplate='%{text:.2s}' ),
          
          row = 1,
          col = 2,

     )

     #Subplot3: Debt Vs Equity Ratio
     fig.add_trace(

               go.Pie(labels = mf_types, 
                         values = current_amount,
                         legendgroup = '3',
                         textinfo='label+percent',
                         showlegend=False,
                         insidetextorientation='radial'),

               row = 2,
               col = 1,

               )




     #Subplot4; Show Gain Percent
     fig.add_trace(
          
          go.Bar(name= f"Gain Percent",x = totals_df['Gain Percent'], y=mf_types, orientation = 'h',  legendgroup = '4', showlegend=False,
                                        text = totals_df['Gain Percent'], textposition='outside', texttemplate='%{text:.2s}'),
          row = 2,
          col = 2,
          

     )

     fig.update_layout(height=700,  legend_tracegroupgap = 50)
     fig.show()

def display_target_units_amt(hdr_df:pd.DataFrame):
        # Show graph with sorted order of current amount
        hdr_df = hdr_df.sort_values(by = ['target_amt'], ascending= False)

    
        scheme_names = [ name.split('Fund')[0].strip() for name in hdr_df.scheme_name.to_list()]

        fig = go.Figure( data = [
                                go.Bar( name = f"Target Units",
                                        x =  scheme_names,
                                        y= hdr_df.target_units.values,                                   
                                        text = hdr_df.comments.to_list(),
                                        hovertemplate = "%{text}"
                                        ),                             
                                    
                                ])

        fig.update_layout( 
                
                        height=600,
                        title = 'Mutual Funds Target Units/Amount ',
                    
                        )
        fig.update_yaxes(title_text='Target Units')
        fig.show() 


def display_mf_scheme_amounts(mf_hdr_df:pd.DataFrame)->None:
    hdr_df = mf_hdr_df
    # Show graph with sorted order of current amount
    hdr_df = hdr_df.sort_values(by = ['current_amt'], ascending= False)

    #Shorten the MF names 
    scheme_names = [ name.split('Fund')[0].strip() for name in hdr_df.scheme_name.to_list()]
    gain_loss =  hdr_df.current_amt.values - hdr_df.invested_amt.values
    # gain_loss =  hdr_df.amount.values- hdr_df.current_amt.values 
    fig = go.Figure( data = [

                            go.Bar( name = f"Current Amount ({ct.RUPEEE_SYMBOL})",  x =  scheme_names, y= hdr_df.current_amt.values, 
                                    text = hdr_df.current_amt.values, textposition='outside', texttemplate='%{text:.2s}'
                                    ),
                            go.Bar( name = f"Invested Amount ({ct.RUPEEE_SYMBOL})", x = scheme_names, y= hdr_df.invested_amt.values,
                                    text = hdr_df.invested_amt.values, textposition='outside', texttemplate='%{text:.2s}'),
                    
                                  
                            go.Bar( name = f"Gain/Loss ({ct.RUPEEE_SYMBOL})",  x =  scheme_names, y= gain_loss, 
                                    text = gain_loss, textposition='outside', texttemplate='%{text:.2s}')
                                    
                            
                            ])

    fig.update_layout( barmode='group',
                    height=600,
                    title = 'Mutual Funds Scheme Valuation'
                    )
    fig.show() 

def display_unrealised_ltcg_stcg(mf_hdr_df:pd.DataFrame):
    hdr_df = mf_hdr_df.sort_values(by = ['ltcg'], ascending= False)
    scheme_names = [ name.split('Fund')[0].strip() for name in hdr_df.scheme_name.to_list()]

    fig = go.Figure( data = [

                            go.Bar( name = f"LTCG ({ct.RUPEEE_SYMBOL})",  x =  scheme_names, y= hdr_df.ltcg.values, 
                                    text =   hdr_df.ltcg.values, textposition='outside', texttemplate='%{text:.2s}'
                                    ),

                            go.Bar( name = f"STCG ({ct.RUPEEE_SYMBOL})", x = scheme_names, y= hdr_df.stcg.values,
                                    text = hdr_df.stcg.values, textposition='outside', texttemplate='%{text:.2s}'),
                    
                            ])

    fig.update_layout( barmode='group',
                    height=600,
                    #    width = 800,
                    title = 'Unrealised LTCG and STCG'
                    )
    fig.show()  


def display_mf_scheme_pie_chart(mf_hdr_df:pd.DataFrame)->None:
    hdr_df = mf_hdr_df.sort_values(by = ['current_amt'], ascending= False)
    scheme_names = [ name.split('Fund')[0].strip() for name in hdr_df.scheme_name.to_list()]
    fig = go.Figure(data = [go.Pie(labels = scheme_names, 
                                values = hdr_df.current_amt,
                                textinfo='label+percent',
                                insidetextorientation='radial',
                                
                                )])

    fig.update_layout(
                    # height=600,
                    title = 'Mutual Funds Allocation'
                        )                              
    fig.show()


