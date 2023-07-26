import time
import copy

import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

from plugin_base import PluginBase

class ProcTracerBase(PluginBase):

    t0=time.time()

    @classmethod
    def t(cls):
        return time.time()-cls.t0

    @classmethod
    def consolidate(cls):

        #wait for thread to end
        for p in cls.instances:
           cls.instances[p].thread["instance"].join()

        t=cls.t()

        with PdfPages("%s/%s.pdf" % (cls.config_yaml['report_output_path'], cls.config_yaml['report_name']) ) as pdf:
            for p in cls.instances:
                cls.instances[p].add_diagrams(pdf, t)

    def __init__(self, config_yaml, file, key, header_in, first_line=0, last_line=None, patterns='', anti_patterns=''):
        super().__init__(config_yaml)
        self.file=file
        self.key=key
        self.header_in = header_in
        self.first_line=first_line
        self.last_line=last_line
        self.patterns=patterns.split()
        self.anti_patterns=anti_patterns.split()
        self.header_in = self.header_in.split()
        self.diff_on = ''
        self.proc_fds={}
        self.sample_old={}
        self.data_frame = pd.DataFrame()
        self.retry_read_counter = 5

    def start(self):
        #print("started:", self.name, "with config", self.plugin_yaml)
        pass

    def run(self):
        #print("%s (t=%s)" % (self.name, self.t() ))
        self.collect()

    def end(self):
        #print("ended:", self.name)
        pass

    def proc_reader(self, file):
        result=""

        if file not in self.proc_fds:
            try:
                self.proc_fds[file] = open(file, 'r')
            except FileNotFoundError:
                self.retry_read_counter -= 1
                time.sleep(1)
                
                if self.retry_read_counter == 0:
                    self.thread["pill2kill"].set()
                    self.file = "Not available: %s" % self.file
                    
                return result

        try:
            result=self.proc_fds[file].read()
            self.proc_fds[file].seek(0)
        except IOError:
            return result

        return result
    
    def pre_parsing_step(self, line):
        return line
    
    def parser(self, file):
        sample={}

        t= self.t()
        proc_data = self.proc_reader(file)

        if proc_data:

            for line in proc_data.splitlines()[self.first_line:self.last_line]:
                
                #blacklist
                if ( len(self.anti_patterns) != 0 ):
                    to_be_collected=True
                    for pattern in self.anti_patterns:
                        if pattern in line:
                            to_be_collected = False
                            break
                
                    if not to_be_collected:
                        continue
                
                #whitelist
                to_be_collected = ( len(self.patterns) == 0 )

                if not to_be_collected:
                    for pattern in self.patterns:
                        if pattern in line:
                            to_be_collected = True
                            break
                
                if to_be_collected:
                    line=self.pre_parsing_step(line)
                    
                    entry = { k: v for k, v in zip(self.header_in, line.split() ) }
                    entry['time']= t
                    sample[entry[self.key]] = entry

        return sample

    def mapper(self, sample):
        return sample

    def collect(self):
        sample=self.sample()
        if sample:
            sample = self.mapper(sample)

            for k in list(sample.keys()) + list(self.sample_old.keys()):

                if k in self.sample_old and k in sample:

                    is_different = False

                    diff_on = sample[k].keys() if not self.diff_on else self.diff_on.split()

                    for key in diff_on:
                        if self.sample_old[k][key] != sample[k][key]:
                            is_different = True
                            break

                    if is_different:
                        self.data_frame = pd.concat([self.data_frame, pd.DataFrame(self.sample_old[k], index=[k] )] )
                        self.data_frame = pd.concat([self.data_frame, pd.DataFrame(sample[k], index=[k] )] )

                if k not in self.sample_old:
                    self.data_frame = pd.concat([self.data_frame, pd.DataFrame(sample[k], index=[k] )] )

                if k in sample:
                    self.sample_old[k] = copy.deepcopy(sample[k])
                else:
                    self.data_frame = pd.concat([self.data_frame, pd.DataFrame(self.sample_old[k], index=[k] )] )
                    del self.sample_old[k]

    def sample(self):
        return self.parser(self.file)

    def add_diagram(self, pdf, maxT):
        pass