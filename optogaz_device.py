import sys
import time
import datetime
from datetime import datetime
import os
import serial
import socket
import telebot
import telebot_config


class Optogaz_device:
    def __init__(self):
        self.develop = False ## flag True for develop stage
        self.verbose = True  ## flag True for print a lot of information
        self.bot_flag = True ## 
        self.test_mode = False
        
        ##  telegram config
        self.telebot_token   = telebot_config.token
        self.telebot_channel = telebot_config.channel  
        
        ##  COM port properties
        self.portName = 'COM3'
        self.BPS      = 9600
        self.PARITY   = serial.PARITY_NONE
        self.STOPBITS = serial.STOPBITS_ONE
        self.BYTESIZE = serial.EIGHTBITS
        self.TIMEX    = 1
        
        ##  ----------------------------------
        ##  run init procedures
        self.get_separator()
        self.get_local_ip()
        
        ##  read config file
        self.device_name = None
        self.datadir = "."       ## data directory name
        self.configfilename  = "optogaz_config.py"
        if self.read_config_file(): 
            sys.exit(10)  ## errors in read config file
        if self.verbose:
            self.print_params()
        
        ##  for data files
        self.datafilename_suff   = '_data.csv'
        self.logfilename_suff    = '_log.txt'
        self.rawfilename_suff    = '_raw.txt'
        self.datafilename    = '_optogaz_data.csv'
        self.logfilename     = '_optogaz_log.txt'
        self.rawfilename     = '_optogaz_raw.txt'
        self.datafile_header = "datatime;timestamp;DevDatetime;CO [ppm];CO2 [ppm]"   
        
        ##  prepare dirs and files for data and logs        
        self.logdirname    = f"{self.datadir}{self.sep}log{self.sep}"
        self.rawdirname    = f"{self.datadir}{self.sep}raw{self.sep}"
        self.tabledirname  = f"{self.datadir}{self.sep}table{self.sep}"
        self.prepare_dirs()
    

    ##  ----------------------------------------------------------------  
    ##  ----------------------------------------------------------------
    ##   Make dirs and filenames to save data
    ##  ----------------------------------------------------------------
    def prepare_dirs(self):
        dirs = [self.datadir, self.tabledirname, self.logdirname, self.rawdirname]
        for path in dirs:
            if not os.path.exists(path):   
                os.system("mkdir " + path)
        
        if not self.filenames_are_ok():
            self.create_filenames()


    ##  ----------------------------------------------------------------
    ##   Check output filenames content current month
    ##  ----------------------------------------------------------------
    def filenames_are_ok(self):
        ## get current datatime
        tt = datetime.now()
        timestamp = f"{tt.year}_{tt.month:02}"

        if ((timestamp in self.datafilename) and 
            (timestamp in self.logfilename) and
            (timestamp in self.rawfilename) and
            (self.device_name.split()[0].lower() in self.datafilename)
            ):
            return True  ##  OK -
        
        return False


    ##  ----------------------------------------------------------------
    ##   Create filenames to save data
    ##  ----------------------------------------------------------------
    def create_filenames(self):
        ## get current datatime
        tt = datetime.now()
        timestamp = f"{tt.year}_{tt.month:02}"
          
        devicename = self.device_name.split()[0].lower()
          
        ##  name for log files
        self.logfilename = f"{self.logdirname}{timestamp}_{devicename}{self.logfilename_suff}"
        
        ##  name for raw files
        self.rawfilename = f"{self.rawdirname}{timestamp}_{devicename}{self.rawfilename_suff}"
        
        ##  name for data files
        self.datafilename = f"{self.tabledirname}{timestamp}_{devicename}{self.datafilename_suff}"
        ##  create data file
        if not os.path.lexists(self.datafilename):
            with open(self.datafilename, "w") as fdata:
                fdata.write(self.datafile_header + '\n')
            text = f"New file {self.datafilename.split(self.sep)[-1]} created"
            self.write_to_bot(text)  ## write to bot
       
        ##  print messages      
        if self.verbose:
            print(self.datafilename)
            print(self.logfilename)
            print(self.rawfilename)


    ## ----------------------------------------------------------------
    ##  
    ## ----------------------------------------------------------------
    def get_local_ip(self):
        self.hostname = socket.gethostname()
        self.local_ip = socket.gethostbyname(self.hostname)


    ## ----------------------------------------------------------------
    ##  определить разделитель в полном пути в операционной системе 
    ## ----------------------------------------------------------------
    def get_separator(self):
        self.sep = '/' if 'ix' in os.name else '\\' 


    ## ----------------------------------------------------------------
    ##  Print message to bot or to logfile
    ## ----------------------------------------------------------------
    def print_info(self, text):
        if self.bot_flag:
            self.write_to_bot(text)
        else:
            self.print_message(text)


    ## ----------------------------------------------------------------
    ##  Print message to logfile
    ## ----------------------------------------------------------------
    def print_message(self, message, end=''):
        text = f"{str(datetime.now()).split('.')[0]}: {message}{end}"
        
        ##  print to screen
        if self.verbose:
            print(text)  

        ##  write to log file
        if not text.endswith('\n'):
            text += '\n'
        with open(self.logfilename,'a') as flog:
            flog.write(text)


    ## ----------------------------------------------------------------
    ##  write message to bot
    ## ----------------------------------------------------------------
    def write_to_bot(self, text):
        text = f"{self.hostname} ({self.local_ip}): {self.device_name}: {text}"
        if not self.test_mode:
            try:
                bot = telebot.TeleBot(self.telebot_token, parse_mode=None)
                bot.send_message(self.telebot_channel, text)
                self.print_message(text)
            except Exception as err:
                ##  напечатать строку ошибки
                text = f": ERROR in writing {text} to bot: {err}"
                self.print_message(text)  ## write to log file
        else:
            self.print_message(text)        


    ## ----------------------------------------------------------------
    ## read config params from configfile optogaz_config.py as a python module
    ## ----------------------------------------------------------------
    def read_config_file(self):
        # check file
        try:
            import optogaz_config as config
        except:
            print(f"\n!!! read_config_file Error!! No file 'optogaz_config.py' to read config!!!\n\n")
            return -1

        self.portName    = config.COM
        self.datadir     = config.datapath
        self.device_name = config.device_name
    
        try:
            self.develop = config.develop
            if self.develop:
                print("--------------------------------------------")
                print("   Warning!   Run in emulation mode!    ")
                print("--------------------------------------------")
        except:
            pass
        
        #self.write_config_file()


    ## ----------------------------------------------------------------
    ## save config to bak file
    ## ----------------------------------------------------------------
    def write_config_file(self):
        ##  rename current config file
        tt = datetime.now() ## get current datatime
        timestamp = f"{tt.year}{tt.month:02}{tt.day:02}_{tt.hour:02}{tt.minute:02}"
        os.system(f"copy {self.configfilename} {self.configfilename}_{timestamp}")
                
        ##  save configuration to new config.py
        filename = self.configfilename  ## + ".bak"
        with open(filename, 'w') as f:
            f.write("# Attention! Write with python sintax!!!!\n")

            f.write("#\n# Directory for DATA:\n")
            f.write(f"datapath = \"{self.datadir}\"\n")

            f.write("#\n# Optogaz:   Device name:\n")
            f.write(f'device_name = "{self.device_name}"\n')
            
            f.write("#\n# Optogaz:   Serial Port:\n")
            f.write(f"COM = \"{self.portName}\"\n")
            
            f.write("#\n# Optogaz:   Develop mode:\n")
            f.write(f"develop = {self.develop}\n")


    ##  ----------------------------------------------------------------
    ##  Print params 
    ##  ----------------------------------------------------------------
    def print_params(self):
        print("Directory for DATA: ", self.datadir)
        print("portName = ", self.portName)
        print("BPS = ",      self.BPS)
        print("STOBITS = ",  self.STOPBITS)
        print("PARITY = ",   self.PARITY)
        print("BYTESIZE = ", self.BYTESIZE)
        print("TIMEX = ",    self.TIMEX)


    ##  ----------------------------------------------------------------
    ##  Open COM port
    ##  ----------------------------------------------------------------
    def connect(self):
        ##  print info line
        print(f"Connection to COM port {self.portName} ...", end='')
        if self.develop:
            print("   simulation")
            return 2  ## Simulation mode
        print()

        ##  Open COM Port
        try:
            self.ser = serial.Serial(
                    port =     self.portName,
                    baudrate = self.BPS,       # 115200,
                    parity =   self.PARITY,    # serial.PARITY_NONE,
                    stopbits = self.STOPBITS,  # serial.STOPBITS_ONE,
                    bytesize = self.BYTESIZE,  # serial.EIGHTBITS
                    #timeout  = self.timeout
                    )
        except Exception as err: ##  напечатать строку ошибки
            text = f"ERROR in {self.portName} connect(): {err}" 
            self.print_message(text)  ## write to log file
            #self.write_bot(text)
            return -1 ## Error in opening
        
        ##  Check result of opening
        try:
            if (self.ser.isOpen()):
                text = f"{self.portName} port open success"
                self.write_to_bot(text)
        except Exception as err:
            text = f"ERROR: {self.portName} port open failed: {err}" 
            self.print_message(text)  ## write to log file
            return -2  ## Error in checking
        
        return 0  ## OK          
        

    ##  ----------------------------------------------------------------
    ##  Close COM port
    ##  ----------------------------------------------------------------
    def unconnect(self):
        print(f"Close COM port {self.portName} ... ", end='')
        if self.develop:
            print("...   simulation")
            return 2
        self.ser.close() # Закройте порт    


    ##  ----------------------------------------------------------------
    ##  Send request to COM port
    ##  ----------------------------------------------------------------
    def request(self):
        #time.sleep(20)
        ##  read byte number of data in port
        try:
            n = self.ser.in_waiting
        except Exception as err:
            ##  напечатать строку ошибки
            text = f"ERROR in serial port reading: {err}"
            self.print_message(text)  ## write to log file
            return 1
       
        ##  read data to dataline
        dataline = ''
        while self.ser.in_waiting: ## читает кол-во байт в порте
            ##  прочитать один байт из порта
            try:
                line = self.ser.read() ## читает один байт из порта
                #print(line)
            except Exception as err:
                ##  напечатать строку ошибки
                text = f": ERROR in serial reading: {err}"
                self.print_message(text)  ## write to log file  
            ##  decode 
            if (line):
                try:
                    line = str(line.decode())
                    dataline = dataline + line
                except Exception as err:               
                    ##  напечатать ошибочный байт                  
                    text = f"Cant decode byte: {str(ord(line))} from ||{str(line)}||-"
                    self.print_message(text)  ## write to log file
                line = ""
            else:  ## невозможное условие
                text = "Error: no line in read() in request() :: is open failed. Происходит что-то ужасное!\n"
                #self.print_message(text)  ## write to log file
                self.write_to_bot(text)
                break
        
        if len(dataline) < 10:
            return  

        dataline = dataline.replace('\r', '')
        
        ##  write dataline to raw file
        with open(self.rawfilename, 'a') as fraw:
            fraw.write(dataline) 

        ##  select one record
        dataline = [record for record in dataline.strip().split("\n") if len(record) >=30][-1]
        
        ##  replace spaces
        dataline = ";".join(dataline.strip().split())
        dataline = dataline.replace(';', ' ', 1)
        
        ##  add timestamp and current datetime to dataline
        dataline = f"{str(datetime.now()).split('.')[0]};{int(datetime.now().timestamp())};{dataline}\n"
        
        ##  check datafile name with new device name and actual datetime
        if not self.filenames_are_ok():
            self.create_filenames()
        
        ## write dataline to datafile
        print(dataline)
        with open(self.datafilename, 'a') as fdata:
            fdata.write(dataline) 


    ##  ----------------------------------------------------------------
    ##  ----    ---- --- ----   ----------------------------------------
    ##  ---- -------  -- ---- -- ---------------------------------------
    ##  ----    ---- - - ---- --- --------------------------------------
    ##  ---- ------- --  ---- -- ---------------------------------------
    ##  ----    ---- --- ----   ----------------------------------------
    ##  ----------------------------------------------------------------

