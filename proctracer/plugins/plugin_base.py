import os
import signal
import traceback
import random
import time
import threading

class PluginBase:

    plugins = {}
    instances = {}
    config_yaml = {}

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.plugins[cls.__name__] = cls

    @classmethod
    def start_plugins(cls, config):
        cls.config_yaml = config

        for p in config['plugins'].keys():
            if p in cls.plugins and config['plugins'][p]['active']:
                if p not in cls.instances:
                    cls.instances[p]=cls.plugins[p](config)

    @classmethod
    def terminate_plugins(cls):
        for p in cls.instances:
            cls.instances[p].terminate()

    @classmethod
    def register_signal_handlers(cls):
        for s in [signal.SIGINT, signal.SIGHUP, signal.SIGTERM, signal.SIGABRT, signal.SIGUSR1, signal.SIGUSR2, signal.SIGQUIT, signal.SIGCHLD]:
            signal.signal(s, cls.signal_handler)

    @classmethod
    def signal_handler(cls, sig, frame):
        cls.terminate_plugins()

    def __init__(self, config_yaml):
        self.name = self.__class__.__name__
        self.plugin_yaml=self.config_yaml['plugins'][self.name]

        #only one thread per plugin
        if self.name not in self.instances:

            pill2kill = threading.Event()
            self.thread =  {
                "pill2kill":pill2kill,
                "instance": threading.Thread(name=self.name, target=self.task, args=( pill2kill, self.plugin_yaml['period'], [], {} ))
                }
            self.thread["instance"].daemon = True
            self.thread["instance"].start()

    def terminate(self):
        self.thread["pill2kill"].set()
        self.thread["instance"].join()

    def task(self,stopEvent,period,args,kwargs):
        try:

            self.start(*args, **kwargs)

            #set uniform phase of period
            stopEvent.wait(random.uniform(0, period))

            while not stopEvent.is_set():
                tic=time.time()
                self.run(*args, **kwargs)
                latency=time.time()-tic

                #slotted time approach
                delay = period-latency
                while delay<=0:
                   delay+=period

                #add flag to switch slotted mode or max throughput
                stopEvent.wait( delay )

            self.end(*args, **kwargs)

        except Exception as e:
            errrorString = "An exception occurred (task,%s::%s): %s\n%s" %(self.name,e,traceback.format_exc() )
            print( errrorString )
            stopEvent.set()

    # mathods in task loop
    def start(self):
        pass

    def run(self):
        pass

    def end(self):
        pass
