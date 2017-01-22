from __future__ import absolute_import, division, print_function, unicode_literals
import numpy as np
import pandas as pd
import os
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib import style
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as mtick

try:
    import Tkinter as tk
    import ttk
    import tkFont
    import tkMessageBox
except:
    import tkinter as tk
    from tkinter import ttk
    from tkinter import font as tkFont
    from tkinter import messagebox as tkMessageBox

from auquanToolbox.metrics import metrics, baseline
from auquanToolbox.dataloader import data_available

def loadgui(back_data, exchange, base_index, budget,logger):

	######################
	# Setup data
	######################

	position = back_data['POSITION']
	close = back_data['CLOSE']

	#position as % of total portfolio

	long_position = 100*(position*close).div(back_data['VALUE'], axis = 0)
	short_position = long_position.copy()
	long_position[long_position < 0]= 0
	short_position[short_position > 0]= 0

	daily_pnl = back_data['DAILY_PNL']*100/budget
	total_pnl = back_data['TOTAL_PNL']*100/budget

	baseline_data = baseline(exchange, base_index, total_pnl.index, logger)
	stats = metrics(daily_pnl, total_pnl, baseline_data)

	daily_return = daily_pnl.sum(axis=1)
	total_return = total_pnl.sum(axis=1)
	long_exposure = long_position.sum(axis=1)
	short_exposure = short_position.sum(axis=1)
	zero_line = np.zeros(daily_pnl.index.size)

	#print to logger
	for x in stats.keys():
		logger.info('%s : %0.2f'%(x,stats[x]))


	def isDate(val):

		#Function to validate if a given entry is valid date
		try:
		    d = pd.to_datetime(val)
		    if d>daily_pnl.index[0] and d<daily_pnl.index[-1]:
		        return True
		    else:
		        return False
		except ValueError:
		    raise ValueError("Not a Valid Date")
		    return False

	def newselection(event):

		#Function to autoupdate chart on new selection from dropdown
		i = dropdown.current()
		market = ['TOTAL PORTFOLIO'] + daily_pnl.columns.values.tolist()
		plot(daily_pnl, total_pnl, long_position, short_position, baseline_data, market[i],box_value2.get(), box_value3.get())


	def plot(daily_pnl, total_pnl, long_position, short_position, baseline_data, market = 'TOTAL PORTFOLIO',start=daily_pnl.index.format()[0],end=daily_pnl.index.format()[-1]):

		#New plot when custom fields are changed

		plt.clf()

		#plt.style.use("seaborn-whitegrid")
		daily_pnl = daily_pnl.loc[start:end]
		total_pnl = total_pnl.loc[start:end]
		base_pnl = baseline_data['TOTAL_PNL'].loc[start:end]
		long_position = long_position.loc[start:end]
		short_position = short_position.loc[start:end]

		if market == 'TOTAL PORTFOLIO':
		    daily_return = daily_pnl.sum(axis=1)
		    total_return = total_pnl.sum(axis=1)
		    long_exposure = long_position.sum(axis=1)
		    short_exposure = short_position.sum(axis=1)
		else:
		    daily_return = daily_pnl[market]
		    total_return = total_pnl[market]
		    long_exposure = long_position[market]
		    short_exposure = short_position[market]

		zero_line = np.zeros(daily_pnl.index.size)
		#f, plot_arr = plt.subplots(3, sharex=True)

		total_plot = plt.subplot2grid((10,8), (0,0), colspan = 12, rowspan = 4)
		daily_plot = plt.subplot2grid((10,8), (5,0), colspan = 12, rowspan = 2, sharex = total_plot)
		position_plot = plt.subplot2grid((10,8), (8,0), colspan = 12, rowspan = 2, sharex = total_plot)
		ind = np.arange(len(daily_pnl.index))
		      
		total_plot.set_title('Total % PnL')
		total_plot.plot(ind, zero_line, 'k')
		total_plot.plot(ind, total_return.values, 'b',linewidth=0.5, label='strategy')
		total_plot.plot(ind, baseline_data['TOTAL_PNL'], 'g',linewidth=0.5, label='s&p500')
		total_plot.legend(loc='upper left')
		total_plot.autoscale(tight=True)
		plt.setp(total_plot.get_xticklabels(), visible=False)
		total_plot.yaxis.set_major_formatter(mtick.FuncFormatter(format_perc))    
		total_plot.set_ylabel('Cumulative Performance')
		total_plot.legend(bbox_to_anchor=(0.03, 0.97), loc='lower left', borderaxespad=0.)

		daily_plot.set_title('Daily % PnL')
		daily_plot.plot(ind, zero_line, 'k')
		daily_plot.bar(ind, daily_return.values, 0.2, align='center', color='c', label='strategy')
		daily_plot.legend(loc='upper left')
		daily_plot.autoscale(tight=True)
		plt.setp(daily_plot.get_xticklabels(), visible=False)
		daily_plot.yaxis.set_major_formatter(mtick.FuncFormatter(format_perc))
		daily_plot.set_ylabel('Daily Performance')
		daily_plot.legend(bbox_to_anchor=(0.03, 0.97), loc='lower left', borderaxespad=0.)

		position_plot.set_title('Daily Exposure')
		position_plot.plot(ind, zero_line, 'k')
		position_plot.bar(ind, short_exposure.values, 0.3,linewidth=0, align='center', color='r', label='short')
		position_plot.bar(ind, long_exposure.values, 0.3,linewidth=0, align='center', color='b', label='long')
		position_plot.legend(loc='upper left')
		position_plot.autoscale(tight=True)    
		position_plot.xaxis.set_major_formatter(mtick.FuncFormatter(format_date))
		position_plot.yaxis.set_major_formatter(mtick.FuncFormatter(format_perc))    
		position_plot.set_ylabel('Long/Short %')    
		position_plot.legend(bbox_to_anchor=(0.03, 0.97), loc='lower left', borderaxespad=0.)

		plt.gcf().canvas.draw()

	def update_plot():

		#Callback Function for plot button
		try:
		    d1 = pd.to_datetime(box_value2.get())
		    d2 = pd.to_datetime(box_value3.get())
		    if d1>=daily_pnl.index[0] and d2<=daily_pnl.index[-1]:
		        plot(daily_pnl, total_pnl, long_position, short_position, baseline_data, box_value.get(), box_value2.get(), box_value3.get())
		    else:
		    	tkMessageBox.showinfo("Date out of Range", "Please enter a date from %s to %s"%(daily_pnl.index[0].strftime('%Y-%m-%d'),daily_pnl.index[-1].strftime('%Y-%m-%d')))
		except ValueError:
		    raise ValueError("Not a Valid Date")

	def close_window(): 

		#Callback function for Quit Button
		GUI.destroy()
		GUI.quit()

	def format_date(x, pos=None):

		#Format axis ticklabels to dates
		thisind = np.clip(int(x + 0.5), 0, len(daily_pnl.index) - 1)
		return daily_pnl.index[thisind].strftime('%b-%y')

	def format_perc(y, pos=None):

		#Format axis ticklabels to %
		return '%0.0f%%'%y


	######################
	## GUI mainloop
	######################

	#Create widget
	GUI = tk.Tk()
	GUI.title('Backtest Results')

	#Create dropdown for market

	Label_1 = tk.Label(GUI, text="Trading Performance:")
	Label_1.grid(row = 0, column = 0, sticky = tk.EW)

	box_value = tk.StringVar()
	dropdown = ttk.Combobox(GUI, textvariable  = box_value, state = 'readonly')
	dropdown['values'] = ['TOTAL PORTFOLIO'] + daily_pnl.columns.values.tolist()
	dropdown.grid(row=0, column=1,sticky=tk.EW)
	dropdown.current(0)
	dropdown.bind('<<ComboboxSelected>>',newselection)

	#Create entry field for start date

	Label_2 = tk.Label(GUI, text="Start Date")
	Label_2.grid(row = 0, column = 2, sticky = tk.EW)

	box_value2 = tk.StringVar(GUI, value=daily_pnl.index.format()[0])
	start = tk.Entry(GUI, textvariable  = box_value2, validate='key', validatecommand=(GUI.register(isDate),'%P'))
	start.grid(row=0, column=3,sticky=tk.EW)

	#Create entry field for end date

	Label_3 = tk.Label(GUI, text="End Date")
	Label_3.grid(row = 0, column = 4, sticky = tk.EW)

	box_value3 = tk.StringVar(GUI, value=daily_pnl.index.format()[-1])
	end = tk.Entry(GUI, textvariable  = box_value3, validate='key', validatecommand=(GUI.register(isDate),'%P'))
	end.grid(row=0, column=5,sticky=tk.EW)

	#Create Plot button to reload chart

	button1 = tk.Button(GUI, text='PLOT', command=update_plot)
	button1.grid(row = 0, column = 6, sticky = tk.EW)

	#Create text widget with backtest results

	customFont1 = tkFont.Font(family="Helvetica", size=9, weight="bold")
	customFont2 = tkFont.Font(family="Helvetica", size=12)

	text = tk.Text(GUI,height=3, width=50, wrap=tk.WORD,bd=5, padx = 10, pady=5)
	text.grid(row=1,column=0, columnspan = 7, sticky=tk.EW)
	for x in stats.keys():
	    text.insert(tk.END, x + '\t\t')
	text.insert(tk.END,'\n')
	for x in stats.values():
	    text.insert(tk.END, '%0.2f'%x + '\t\t')
	text.tag_add("keys", "1.0", "1.end")
	text.tag_config("keys", font = customFont1)
	text.tag_add("values", "2.0", "2.end")
	text.tag_config("values", foreground="red", font = customFont2)

	#Create canvas to plot chart

	f = plt.figure(figsize = (16,8))
	canvas = FigureCanvasTkAgg(f, master=GUI)
	canvas.get_tk_widget().grid(row=2,column=0,columnspan = 7, rowspan = 1, sticky=tk.NSEW)
	toolbar_frame = tk.Frame(GUI) 
	toolbar_frame.grid(row=4,column=0,columnspan=7) 
	toolbar = NavigationToolbar2TkAgg( canvas, toolbar_frame )

	#plot 3 subplots for total position, daily position and exposure

	plt.style.use("seaborn-whitegrid")
	total_plot = plt.subplot2grid((10,8), (0,0), colspan = 12, rowspan = 4)
	daily_plot = plt.subplot2grid((10,8), (5,0), colspan = 12, rowspan = 2, sharex = total_plot)
	position_plot = plt.subplot2grid((10,8), (8,0), colspan = 12, rowspan = 2, sharex = total_plot)
	ind = np.arange(len(daily_pnl.index))
	      
	total_plot.set_title('Total % PnL')
	total_plot.plot(ind, zero_line, 'k')
	total_plot.plot(ind, total_return.values, 'b',linewidth=0.5, label='strategy')
	total_plot.plot(ind, baseline_data['TOTAL_PNL'], 'g',linewidth=0.5, label='s&p500')
	total_plot.legend(loc='upper left')
	total_plot.autoscale(tight=True)
	plt.setp(total_plot.get_xticklabels(), visible=False)
	total_plot.yaxis.set_major_formatter(mtick.FuncFormatter(format_perc))    
	total_plot.set_ylabel('Cumulative Performance')
	total_plot.legend(bbox_to_anchor=(0.03, 0.97), loc='lower left', borderaxespad=0.)

	daily_plot.set_title('Daily % PnL')
	daily_plot.plot(ind, zero_line, 'k')
	daily_plot.bar(ind, daily_return.values, 0.2, align='center', color='c', label='strategy')
	daily_plot.legend(loc='upper left')
	daily_plot.autoscale(tight=True)
	plt.setp(daily_plot.get_xticklabels(), visible=False)
	daily_plot.yaxis.set_major_formatter(mtick.FuncFormatter(format_perc))
	daily_plot.set_ylabel('Daily Performance')
	daily_plot.legend(bbox_to_anchor=(0.03, 0.97), loc='lower left', borderaxespad=0.)

	position_plot.set_title('Daily Exposure')
	position_plot.plot(ind, zero_line, 'k')
	position_plot.bar(ind, short_exposure.values, 0.3,linewidth=0, align='center', color='r', label='short')
	position_plot.bar(ind, long_exposure.values, 0.3,linewidth=0, align='center', color='b', label='long')
	position_plot.legend(loc='upper left')
	position_plot.autoscale(tight=True)    
	position_plot.xaxis.set_major_formatter(mtick.FuncFormatter(format_date))
	position_plot.yaxis.set_major_formatter(mtick.FuncFormatter(format_perc))    
	position_plot.set_ylabel('Long/Short')    
	position_plot.legend(bbox_to_anchor=(0.03, 0.97), loc='lower left', borderaxespad=0.)

	plt.gcf().canvas.draw()

	#Create Quit Button

	button2 = tk.Button(GUI, text='QUIT', command=close_window)
	button2.grid(row = 4, column = 6, sticky = tk.EW)

	GUI.mainloop()