'''
    Adding event handing for properly closing the application when 
    clicking the close button

    Features 
    - Real time values
    - Database Connectivity
    - Realtime Graphs
    - Settings configuration 

'''

import pyodbc
from tkinter import *
from tkinter import messagebox, OptionMenu, StringVar, Toplevel
import time
import datetime
from pymodbus.client import ModbusSerialClient as ModbusClient
#from pymodbus.client.sync import ModbusSerialClient as ModbusClient
import threading
stop_event = threading.Event()

#graph plotting dependencies
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import(FigureCanvasTkAgg, NavigationToolbar2Tk)
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.dates import DateFormatter
from tkinter import Toplevel, StringVar, Label, Entry, Button, OptionMenu, messagebox
import datetime

#for reading saved COM port
import json
#from tkinter import messagebox

#for accessing the system available COM ports
import serial.tools.list_ports

#For temp queue
import queue
from queue import Queue

#GLOBAL VARIABLES 
global settings_password
settings_password  = "20061111"

global tempQueue
tempQueue = Queue()

qT2Temp = None
qT3Temp = None
qT4Temp = None 
qT5Temp = None  

global qT2TempQueue 
global qT3TempQueue 
global qT4TempQueue 
global qT5TempQueue 

qT2TempQueue = Queue()
qT3TempQueue = Queue()
qT4TempQueue = Queue()
qT5TempQueue = Queue()


#dump to SQL Database
#connection string
conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=10.7.228.186;" #Add host IP to which SQL Server is connected here
    "Port=1433;"  # add the port no. to which sql server listens
    "Database=QuenchTank;"  #database name
    "UID=jack;"  # Replace with your SQL Server username
    "PWD=jack123;"  # Replace with your SQL Server password
)
    
def insert_temperature_to_db(conn_str,qT2Temp,qT3Temp,qT4Temp,qt5Temp):
    try:
        with pyodbc.connect(conn_str, timeout=5) as conn:
            database_connection_label.configure(text="Database Connection: CONNECTED", foreground='green')
            cursor = conn.cursor()

            # Replace None with 0 for all temperature variables
            #all the temp values will be 0 if no value is read.
            qT2Temp = 0 if qT2Temp is None else qT2Temp
            qT3Temp = 0 if qT3Temp is None else qT3Temp
            qT4Temp = 0 if qT4Temp is None else qT4Temp
            qt5Temp = 0 if qt5Temp is None else qt5Temp

            sql_query = "INSERT INTO quenchTanksTemp(QT2,QT3,QT4,QT5,date_time) VALUES (?,?,?,?,GETDATE())"
            params = (qT2Temp, qT3Temp, qT4Temp, qt5Temp)
            #print(sql_query)
            cursor.execute(sql_query, params)
            conn.commit()
        #conn.close()
    except Exception as e:
        print(e)
        database_connection_label.configure(text="Database Connection: DISCONNECTED", foreground='red')

def get_saved_com_port():
    try: 
        with open('settings.json','r') as json_file:
            settings = json.load(json_file)
            #print(settings)
            return settings.get('ComPort','COM1')
        
    except FileNotFoundError:
            messagebox.showinfo("Settings not found", "Please select the COM port manually.")
            return ""

def get_available_comports():
    ports = serial.tools.list_ports.comports()
    available_ports = [port.device for port in ports]
    return available_ports

def create_settings_window():
    settings_window = Toplevel(root)
    settings_window.configure(background="black")
    settings_window.title("Settings")
    settings_window.resizable(False, False)
    settings_window.geometry("600x300")

    settings_window.columnconfigure(0, weight=1)
    settings_window.columnconfigure(1, weight=3)

    for i in range(7):
        settings_window.rowconfigure({i})
        
    #Settings window heading
    settings_title_label = Label(settings_window, text="Settings", background="orange",font=('Arial','30','bold'), foreground="black")
    settings_title_label.grid(row=0, column=0, sticky='nsew', columnspan=2)

    comport_set_label = Label(settings_window, text="COM PORT: ", background="black",font=('Arial','15','bold'), foreground="white")
    comport_set_label.grid(row=2, column=0, sticky="w", pady=20, padx=20)

    settings_password_label = Label(settings_window, text="Password: ",font=('Arial','15','bold'), background="black", foreground="white")
    settings_password_label.grid(row=4, column=0, sticky="w", pady=20, padx=20)

    settings_password_input = Entry(settings_window, width=11, show="*")
    settings_password_input.grid(row=4, column=0, sticky="e")
    
    #Invalid password label
    
    invalid_password_label = Label(settings_window, text="", background="black")
    invalid_password_label.grid(row=6, column=0, sticky="w", padx=20)

    #Read the available COM Ports from system
    com_drop_options_list = get_available_comports()
    
    com_drop_clicked = StringVar()

    settings_apply_button = Button(settings_window, text="Apply", font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: apply_settings(settings_password_input.get(), invalid_password_label, com_drop_clicked))
    settings_apply_button.grid(row=6, column=1, sticky="w", padx=   20)
    #selected_com_port = com_drop_clicked.get() #access the selected com port value using this

    com_drop_clicked.set(com_drop_options_list[0])
    com_dropdown = OptionMenu(settings_window, com_drop_clicked, *com_drop_options_list)

    com_dropdown.configure(background='light blue', highlightthickness=0)
    com_dropdown.grid(row=2, column=0, sticky="e")

def apply_settings(password, invalid_password_label, com_drop_clicked):
        if password != settings_password:
            invalid_password_label.config(text="Invalid Password!", font=('Arial','12','bold'), foreground="red", background="white")
            return
        else:
            selected_com_port = com_drop_clicked.get()
            invalid_password_label.config(text="Settings Applied", font=('Arial','12','bold'), foreground="green", background="white")
            with open('settings.json', 'w') as json_file:
                json.dump({'ComPort': selected_com_port}, json_file)
                update_modbus_config_label(selected_com_port)
                #print(selected_com_port)


# Function to check user credentials
def check_credentials():
    username = username_entry.get()
    password = password_entry.get()
    
    if username == "admin" and password == "123":
        messagebox.showinfo("Login Successful", f"Welcome, {username}!")
        open_dashboard()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password.")

# Function to handle the selection of the Quenchtank option
def select_qt():
    selected_value = Qt_drop_clicked.get()
    print("Selected value:", selected_value)
    open_offsetwindow()

# Functions to increment or decrement the offset value
def add_number():
    value1 = float(inc.get())
    value1 += 0.10
    inc.set(f"{value1:.2f}")# Update the StringVar 

def subtract_number():
    value1 = float(inc.get())
    value1 -= 0.10
    inc.set(f"{value1:.2f}")# Update the StringVar 

# Function to apply changes and show a message
def apply_changes():
    offset_value = inc.get()
    if Qt_drop_clicked.get() == "qT2Temp":
        qT2TempQueue.set(offset_value)
    elif Qt_drop_clicked.get() == "qT3Temp":
        qT3TempQueue.set(offset_value)
    elif Qt_drop_clicked.get() == "qT4Temp":
        qT4TempQueue.set(offset_value)
    else:
        qT5TempQueue.set(offset_value)
        
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    messagebox.showinfo("Offset Changed", f"Offset changed successfully of {Qt_drop_clicked.get()} from {temp_inc} to {offset_value} by {username_entry.get()} at {current_time}")

# Function to open the offset window and initialize widgets
def open_offsetwindow():
    global inc, temp_inc, offset_window, value1
    offset_window = Toplevel(root)
    offset_window.configure(background="black")
    offset_window.title("Offset")
    offset_window.resizable(False, False)
    offset_window.geometry("600x300")

    # Retrieve the appropriate queue value
    if Qt_drop_clicked.get() == "qT2Temp":
        temp_inc = qT2TempQueue.get()
    elif Qt_drop_clicked.get() == "qT3Temp":
        temp_inc = qT3TempQueue.get()
    elif Qt_drop_clicked.get() == "qT4Temp":
        temp_inc = qT4TempQueue.get()
    else:
        temp_inc = qT5TempQueue.get()

    # Debug output to ensure we have the correct value
    print("temp_inc:", temp_inc)  

    # Initialize the StringVar with the temp_inc value
    inc = StringVar(value=str(temp_inc))  # Ensure temp_inc is a string

    # Configure window grid
    offset_window.columnconfigure(0, weight=1)
    offset_window.columnconfigure(1, weight=3)
    for i in range(9):
        offset_window.rowconfigure(i, weight=1)

    # Title Label
    offset_title_label = Label(offset_window, text="OFFSET", background="orange", font=('Arial', 30, 'bold'), foreground="black")
    offset_title_label.grid(row=0, column=0, sticky='nsew', columnspan=3)

    # Data Read Label
    initial_value_label = Label(offset_window, text="DATA READ: ", background="black", font=('Arial', 15, 'bold'), foreground="white")
    initial_value_label.grid(row=2, column=0, sticky="w", pady=20, padx=20)


    entry1 = Entry(offset_window)
    entry1.insert(0, str(temp_inc))  # Insert temp_inc directly into the Entry widget
    entry1.grid(row=2, column=1, sticky="w", padx=20, pady=20)


    # Buttons to adjust the number
    add_button = Button(offset_window, text="INCREMENT", command=add_number, font=('Arial', 12, 'bold'), background='light blue', foreground='black')
    add_button.grid(row=3, column=0, sticky="w", padx=20, pady=20)

    subtract_button = Button(offset_window, text="DECREMENT", command=subtract_number, font=('Arial', 12, 'bold'), background='light blue', foreground='black')
    subtract_button.grid(row=3, column=1, sticky="w", padx=20, pady=20)

    apply_button = Button(offset_window, text="APPLY", command=apply_changes, font=('Arial', 12, 'bold'), background='light blue', foreground='black')
    apply_button.grid(row=4, column=1, sticky="w", padx=20, pady=20)

    
# Function to open the dashboard window and initialize widgets
def open_dashboard():
    dashboard_window = Toplevel(root)
    dashboard_window.title("Quenchtank")
    dashboard_window.configure(background="black")
    dashboard_window.resizable(False, False)
    dashboard_window.geometry("220x180")

    title = Label(dashboard_window, text="Select", background="orange", font=('Arial', 30, 'bold'), foreground="black")
    title.grid(row=0, column=0, sticky='nsew', columnspan=2)
    
    username_label = Label(dashboard_window, text="Quenchtank:", font=('Arial', 15, 'bold'), background="black", foreground="white")
    username_label.grid(row=2, column=0, padx=10, pady=10)
    
    global Qt_drop_clicked
    Qt_drop_options_list = ["qT2Temp", "qT3Temp", "qT4Temp", "qT5Temp"]
    
    Qt_drop_clicked = StringVar()
    Qt_drop_clicked.set(Qt_drop_options_list[0])
    
    Qt_dropdown = OptionMenu(dashboard_window, Qt_drop_clicked, *Qt_drop_options_list)
    Qt_dropdown.configure(background='light blue', highlightthickness=0)
    Qt_dropdown.grid(row=2, column=1, sticky="e")
    
    select_button = Button(dashboard_window, text="Select", command=select_qt, font=('Arial', 12, 'bold'), background='light blue', foreground='black')
    select_button.grid(row=4, columnspan=2, padx=20, pady=20)

# Function to create the main window
def create_offset_window():
    global root, username_entry, password_entry, qT2TempQueue, qT3TempQueue, qT4TempQueue, qT5TempQueue

    # Dummy data for queues
    qT2TempQueue = StringVar(value="35.0")
    qT3TempQueue = StringVar(value="36.0")
    qT4TempQueue = StringVar(value="37.0")
    qT5TempQueue = StringVar(value="38.0")

    # Create the main window
    root = Tk()
    root.title("Login")
    root.configure(background="black")
    root.resizable(False, False)

    authetication_title_label = Label(root, text="Login", background="orange", font=('Arial', 30, 'bold'), foreground="black")
    authetication_title_label.grid(row=0, column=0, sticky='nsew', columnspan=2)
    
    username_label = Label(root, text="Username:", font=('Arial', 15, 'bold'), background="black", foreground="white")
    username_label.grid(row=1, column=0, padx=10, pady=10)
    
    username_entry = Entry(root)
    username_entry.grid(row=1, column=1, padx=10, pady=10)

    password_label = Label(root, text="Password:", font=('Arial', 15, 'bold'), background="black", foreground="white")
    password_label.grid(row=2, column=0, padx=10, pady=10)
    
    password_entry = Entry(root, show="*")
    password_entry.grid(row=2, column=1, padx=10, pady=10)

    # Login button
    login_button = Button(root, text="Login", command=check_credentials, font=('Arial', 12, 'bold'), background='light blue', foreground='black')
    login_button.grid(row=3, columnspan=2, padx=10, pady=10)



def readTemperature(modbus_client):
    global qT2Temp
    global qT3Temp
    global qT4Temp
    global qT5Temp
    qT2Temp = qT3Temp = qT4Temp = qT5Temp = None
    global tempQueue
    global qT2TempQueue 
    global qT3TempQueue 
    global qT4TempQueue 
    global qT5TempQueue 
    while not stop_event.is_set(): 
        try:
            #print("Connecting to the server...")
            connection = modbus_client.connect()
            if(connection==True):
                moxa_connection_label.config(text=str("MOXA: CONNECTED..! IP: 10.7.228.186"), foreground="Green")
            
                #Quench Tank 2 Temperature
                try:
                    inpReg2 = modbus_client.read_input_registers(0x06,1,unit=2)
                    qT2Temp = (inpReg2.registers[0]/10)
                    QT2_temp_label.config(text=str(qT2Temp)+"°C",background="blue",font=('Arial','50','bold'))
                    qT2TempQueue.put(qT2Temp)
                except Exception as e:
                    qT2Temp=0
                    QT2_temp_label.config(text="PID Disconnected", background="red", font=('Arial','20','bold'))
                    qT2TempQueue.put(qT2Temp)
                
                #Quench Tank 3 Temperature
                try:
                    inpReg3 = modbus_client.read_input_registers(0x06,1,unit=3)
                    qT3Temp = (inpReg3.registers[0]/10)
                    QT3_temp_label.config(text=str(qT3Temp)+"°C",background="blue",font=('Arial','50','bold'))
                    qT3TempQueue.put(qT3Temp)
                except Exception as e:
                    qT3Temp=0
                    QT3_temp_label.config(text="PID Disconnected", background="red", font=('Arial','20','bold'))
                    qT3TempQueue.put(qT3Temp)
                
                #Quench Tank 4 Temperature
                try:
                    inpReg4 = modbus_client.read_input_registers(0x06,1,unit=4)
                    qT4Temp = (inpReg4.registers[0]/10)
                    QT4_temp_label.config(text=str(qT4Temp)+"°C",background="blue",font=('Arial','50','bold'))
                    qT4TempQueue.put(qT4Temp)
                except Exception as e:
                    qT4Temp=0
                    QT4_temp_label.config(text="PID Disconnected", background="red", font=('Arial','20','bold'))
                    qT4TempQueue.put(qT4Temp)
                
                #Quench Tank 5 Temperature
                try:
                    inpReg5 = modbus_client.read_input_registers(0x06,1,unit=5)
                    qT5Temp = (inpReg5.registers[0]/10)
                    QT5_temp_label.config(text=str(qT5Temp)+"°C",background="blue",font=('Arial','50','bold'))
                    qT5TempQueue.put(qT5Temp)
                except Exception as e:
                    qT5Temp=0
                    QT5_temp_label.config(text="PID Disconnected", background="red", font=('Arial','20','bold'))
                    qT5TempQueue.put(qT5Temp)

                tempQueue.put((qT2Temp, qT3Temp, qT4Temp, qT5Temp))
                #close the modbus connection
                modbus_client.close()
                root.update()
                time.sleep(2)
                
            else:
                QT2_temp_label.config(text="Moxa Disconnected", background="red", font=('Arial','20','bold'))
                QT3_temp_label.config(text="Moxa Disconnected", background="red", font=('Arial','20','bold'))
                QT4_temp_label.config(text="Moxa Disconnected", background="red", font=('Arial','20','bold'))
                QT5_temp_label.config(text="Moxa Disconnected", background="red", font=('Arial','20','bold'))
                raise Exception(moxa_connection_label.config(text=str("MOXA: DISCONNECTED..! IP: 10.7.228.186"),foreground="red"))
            if stop_event.is_set():
                break
        except Exception as e:
            #raise this exception if the DP 9 Connecter is disconnected from MOXA.(Failed to read the registers)
            print(e)
            time.sleep(2)  # Wait before trying to reconnect

def dump_to_db():
    # Initialize the temperature variables
    global tempQueue
    global qt2_graph_temp, qt3_graph_temp, qt4_graph_temp, qt5_graph_temp
    while not stop_event.is_set():
        try:
            qT2Temp, qT3Temp, qT4Temp, qT5Temp = tempQueue.get(timeout=5)
        except queue.Empty:
            continue 

        qt2_graph_temp = qT2Temp
        qt3_graph_temp = qT3Temp
        qt4_graph_temp = qT4Temp
        qt5_graph_temp = qT5Temp
        
        print(f"{qT2Temp},{qT3Temp},{qT4Temp},{qT5Temp}")
        insert_temperature_to_db(conn_str, qT2Temp,qT3Temp,qT4Temp,qT5Temp)
        if stop_event.is_set():
                break
        time.sleep(5)

def open_graph_window(tempQueue, graph_name):
    
    plt.style.use('dark_background')
    graph_window = Toplevel(root)
    graph_window.resizable(False, False)
    graph_window.title(graph_name)

    #Initialize Tkinter and Matplotlib Figure
    fig_graph, axis_graph = plt.subplots()

    #the x and y values will be stored in the following
    # global x_vals, y_vals
    x_vals = []
    y_vals = []
    
    def animate(i):
        tempVal = Non
        if not tempQueue.empty():
            tempVal = tempQueue.get()
        try:
            #with pyodbc.connect(conn_str, timeout=5) as conn:
            conn = pyodbc.connect(conn_str, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT CURRENT_TIMESTAMP")
        except Exception as e:
            messagebox.showinfo("Database not connected."," Unable to fetch server date and time")
        row = cursor.fetchone()

        if row and tempVal is not None:
            x_vals.append(row[0])
            y_vals.append(tempVal)

        #clear axis
        plt.cla()
        axis_graph.plot(x_vals, y_vals, color='orange', linewidth=2)

        if len(x_vals) > 10:
            axis_graph.set_xlim(left=x_vals[-10], right=x_vals[-1])
        axis_graph.set_title('REAL TIME TREND')

        if y_vals:
            axis_graph.set_ylim([0, max(y_vals) + 10])
        else:
            axis_graph.set_xlim([0, 10])

        axis_graph.set_xlabel('DATE & TIME')
        axis_graph.set_ylabel('TEMP IN °C')
        #axis_graph.plot(x_vals,y_vals)

        date_format = DateFormatter('%Y-%m-%d %H:%M')
        axis_graph.xaxis.set_major_formatter(date_format)
        
        for label in axis_graph.get_xticklabels():
            label.set_rotation(45)
            label.set_fontsize(8)

        # Add padding to the y-axis
        plt.margins(y=0.2) 
        conn.commit()

    #call to animate function
    ani = FuncAnimation(plt.gcf(), animate, interval=1000)

    #Tkinter Application Window
    frame = Frame(graph_window)
    frame.grid(sticky='ew')  # Use grid for frame

    label = Label(frame, text = graph_name, font=('Arial','32','bold'), background="orange", foreground="black")  # Add label to frame
    label.pack(fill='both', expand=True)  # Use grid for label

    #create canvas
    canvas = FigureCanvasTkAgg(fig_graph, master=graph_window)
    canvas.get_tk_widget().grid(sticky='nsew')  # Use grid for canvas

    # Increase bottom padding
    plt.subplots_adjust(bottom=0.3)

    #Create Toolbar
    # Create custom toolbar
    class CustomToolbar(NavigationToolbar2Tk):
        def set_message(self, s):
            s = s.replace('x', 'Date & Time').replace('y', 'Temp in °C')
            super().set_message(s)
    # Create toolbar frame 
    toolbar_frame = Frame(graph_window)
    toolbar_frame.grid()  # Use grid for toolbar_frame
    
    # Create custom toolbar
    toolbar = CustomToolbar(canvas, toolbar_frame)
    toolbar.update()
    toolbar.grid(sticky='w')
     
    canvas.draw()

    def close_graph_window():
        plt.close(fig_graph)
        graph_window.destroy()
    graph_window.protocol("WM_DELETE_WINDOW", close_graph_window)

    graph_window.mainloop()

#for properly closing the application
def on_closing():
    stop_event.set()
    root.destroy()
    
    

root = Tk()
root.configure(background="black")
root.title("Quenching Tank Temperature Monitoring")
root.geometry("1280x720")

#display label
heading_label = Label(root, text="QUENCHING TANK TEMPERATURE MONITORING", background="orange", font=('Arial','30','bold'), foreground="black")
QT2_label = Label(root, text='Quenching Tank 2', background="skyblue",font=('Arial','30','bold'), foreground="black")
QT3_label = Label(root, text='Quenching Tank 3', background="skyblue", font=('Arial','30','bold'), foreground="black")
QT4_label = Label(root, text='Quenching Tank 4', background="skyblue", font=('Arial','30','bold'), foreground="black")
QT5_label = Label(root, text='Quenching Tank 5', background="skyblue", font=('Arial','30','bold'), foreground="black")

#temperature values
QT2_temp_label = Label(root, background="blue", font=('Arial', '50','bold'), foreground="white")
QT3_temp_label = Label(root, background="blue", font=('Arial', '50','bold'), foreground="white")
QT4_temp_label = Label(root, background="blue", font=('Arial', '50','bold'), foreground="white")
QT5_temp_label = Label(root, background="blue", font=('Arial', '50','bold'), foreground="white")

#MODBUS PID configuration
QT2_Modbus_COM_port_label = Label(root, text="SLAVE ID: 1", font=('Arial','12','bold'), foreground="black")
QT3_Modbus_COM_port_label = Label(root, text="SLAVE ID: 2", font=('Arial','12','bold'), foreground="black")
QT4_Modbus_COM_port_label = Label(root, text="SLAVE ID: 3", font=('Arial','12','bold'), foreground="black")
QT5_Modbus_COM_port_label = Label(root, text="SLAVE ID: 4", font=('Arial','12','bold'), foreground="black")

#MODBUS Configuration
def update_modbus_config_label(com_port):
    modbus_config_label = Label(root, text=f"METHOD = RTU / STOPBITS = 1 / DATA BITS = 8 / PARITY = NONE / BAUDRATE=9600 /{com_port}", font=('Arial bold italic', '9'), foreground="white", background="black")
    modbus_config_label.grid(row=13, column=1, sticky="w",columnspan=3)

# Initially create the label without com_port
modbus_config_label = Label(root,text=f"METHOD = RTU / STOPBITS = 1 / DATA BITS = 8 / PARITY = NONE / BAUDRATE=9600 /", font=('Arial bold italic', '9'), foreground="white", background="black")
modbus_config_label.grid(row=13, column=1, sticky="w",columnspan=3)

#MOXA Connetion Label
moxa_connection_label= Label(root, font=('Arial Bold Italic', '9'), foreground="white", background="black")

#database Connection Label
database_connection_label = Label(root, text="Database Connection: CONNECTING", font=('Arial bold italic', '9'), foreground="white", background="black")

#credits labels
credits_label = Label(root, text="Developed By: YASH PAWAR & RISHIKUMAR PATEL", font=('Arial Bold Italic','9'),foreground="white", background="black")

#Mentor label
mentor_label = Label(root, text="Guided By: SUNIL SINGH", font=('Arial Bold Italic','9'),foreground="white", background="black")

#grid definition

#configuring the number of columns
root.columnconfigure(0, weight = 1)
root.columnconfigure(1, weight = 2)
root.columnconfigure(2, weight = 1) 
root.columnconfigure(3, weight = 2)
root.columnconfigure(4, weight = 1)  

#configuring the number of rows
for i in range(16):
    root.rowconfigure({i},weight=1)

#WIDGET PLACEMENT 
#place heading widget
heading_label.grid(row=0, column=0, sticky="nsew", columnspan=8, pady=(0,30))

#place QT Label widget
QT2_label.grid(row=2,column=1, sticky="nsew")
QT3_label.grid(row=2,column=3, sticky="nsew")
QT4_label.grid(row=7,column=1, sticky="nsew")
QT5_label.grid(row=7,column=3, sticky="nsew")

#place temperature widget
QT2_temp_label.grid(row=3, column=1, sticky="nsew")
QT3_temp_label.grid(row=3, column=3, sticky="nsew")
QT4_temp_label.grid(row=8, column=1, sticky="nsew")
QT5_temp_label.grid(row=8, column=3, sticky="nsew")

#place Modbus PID configuration widget
QT2_Modbus_COM_port_label.grid(row=4, column=1, sticky="nsew")
QT3_Modbus_COM_port_label.grid(row=4, column=3, sticky="nsew")
QT4_Modbus_COM_port_label.grid(row=9, column=1, sticky="nsew")
QT5_Modbus_COM_port_label.grid(row=9, column=3, sticky="nsew")

#place database uplink label
database_connection_label.grid(row=11, column=1, columnspan=3, sticky="w")

#place MOXA Connection Label
moxa_connection_label.grid(row=12, column=1, sticky="w",columnspan=3)

#place the credits label
credits_label.grid(row=12, column=3, sticky ='e')

#place the mentor label
mentor_label.grid(row=13, column=3, sticky ='e')

#place the graph buttons
#graph buttons
frame1 = Frame(root)
frame1.grid(row=5, column=1, pady=10)
QT2_Graph = Button(frame1, text="QT2 GRAPH", width=20, height=2, font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: open_graph_window(tempQueue=qT2TempQueue,graph_name="QT2 GRAPH")).grid(row=0, column=0)

frame2 = Frame(root)
frame2.grid(row=5, column=3, pady=10)
QT3_Graph = Button(frame2, text="QT3 GRAPH", width=20, height=2, font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: open_graph_window(tempQueue=qT3TempQueue, graph_name="QT3 GRAPH")).grid(row=0, column=0)

frame3 = Frame(root)
frame3.grid(row=10, column=1, pady=10)
QT4_Graph = Button(frame3, text="QT4 GRAPH", width=20, height=2, font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: open_graph_window(tempQueue=qT4TempQueue, graph_name="QT4 GRAPH")).grid(row=0, column=0)

frame4 = Frame(root)
frame4.grid(row=10, column=3, pady=10)
QT5_Graph = Button(frame4, text="QT5 GRAPH", width=20, height=2, font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: open_graph_window(tempQueue=qT5TempQueue, graph_name="QT5 GRAPH")).grid(row=0, column=0)

#add settings button
settings_frame = Frame(root)
settings_frame.grid(row=12, column=2)
settings_button = Button(settings_frame, text="SETTINGS", width=10, height=2, font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: create_settings_window()).pack(expand=True)

#add offset button
offset_frame = Frame(root)
offset_frame.grid(row=12, column=4)
offset_button = Button(settings_frame, text="OFFSET", width=10, height=2, font=('Arial','12','bold'), background='light blue', foreground='black', command=lambda: create_offset_window()).pack(expand=True)
 
#main loop of the program
def main():
    
    com_port = get_saved_com_port()
    update_modbus_config_label(com_port)

    modbus_client = ModbusClient(method = 'rtu', port=com_port, stopbits = 1, bytesize = 8, parity = 'N' , baudrate= 9600)
    #global read_temp_thread
    read_temp_thread = threading.Thread(target=readTemperature, args=(modbus_client,))
    read_temp_thread.daemon = True
    read_temp_thread.start()

    # global dump_to_db_thread
    dump_to_db_thread = threading.Thread(target=dump_to_db)
    dump_to_db_thread.daemon = True
    dump_to_db_thread.start()

if __name__ == "__main__":
    main()
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
