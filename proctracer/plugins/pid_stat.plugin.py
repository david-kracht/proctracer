import os
import glob
import re

from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

MS_PER_JIFFY = os.sysconf( os.sysconf_names['SC_CLK_TCK'] )
PAGESIZE = os.sysconf( os.sysconf_names['SC_PAGESIZE'] )

class pid_stat(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/pid/stat',
            key='pid',
            header_in='pid comm state ppid pgrp session tty_nr tpgid flags minflt cminflt majflt cmajflt utime stime cutime cstime priority nice num_threads itrealvalue starttime vsize rss rsslim startcode endcode startstack kstkesp kstkeip signal blocked sigignore sigcatch wchan nswap cnswap exit_signal processor rt_priority policy delayacct_blkio_ticks guest_time cguest_time start_data end_data start_brk arg_start arg_end env_start env_end exit_code',
            first_line=0,
            patterns=''
            )
        self.new_pid_map = {}
        self.parent_pid = os.getppid()
        self.blacklist_cmd_patterns='sleep'.split()
    
    def pre_parsing_step(self, line):
        # remove cells with blanks, i.e. "comm" field
        return re.sub(r'\(.*?\)', '()', line)

    def mapper(self, sample):
        new_sample={}
        for k, entry in sample.items():
        
            k=int(k) #new key
            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'rss': int(entry['rss']),
                'ppid': int(entry['ppid']),
                'pgrp': int(entry['pgrp']),
                'session': int(entry['session']),
                'utime': int(entry['utime']),
                'stime': int(entry['stime']),
                'total': sum([int(entry[i]) for i in 'utime stime'.split() ]) , # process in user and kernel modes ; add cutime cstime (for from children processes)
                'load' : 0.0,
                 }

            #use last sample for current value
            if k in self.sample_old:
                new_sample[k]['load'] = 1.0 * ( new_sample[k]['total'] - self.sample_old[k]['total'] ) / MS_PER_JIFFY / ( new_sample[k]['time'] - self.sample_old[k]['time'] )

        return new_sample
    
        
    def sample(self):

        sample={}

        for proc_path in glob.glob('/proc/[0-9]*'):

            pid = proc_path.rsplit("/")[-1]
            pid = int(pid)
            
            if pid not in self.new_pid_map or "cmdline" not in self.new_pid_map:

                proc_data = self.proc_reader('/proc/%s/cmdline' % pid)
                    
                if pid not in self.new_pid_map:
                    self.new_pid_map[pid] = {}
                    
                self.new_pid_map[pid]["cmdline"]= proc_data[:-1].replace('\0', ' ').strip()
            
            if not self.new_pid_map[pid]["cmdline"]:
                continue
            
            skip = False 
            for pattern in self.blacklist_cmd_patterns:
                if pattern in self.new_pid_map[pid]["cmdline"]:
                    skip=True
                    break
            
            if skip:
                continue

            sub_sample = self.parser("/proc/%s/stat" % pid)

            if sub_sample:
            
                sub_sample = self.mapper(sub_sample)

                #if sub_sample[pid]["session"] != self.parent_pid:
                #    continue

                if pid not in self.new_pid_map:
                    self.new_pid_map[pid] = {}
                elif "ppid" not in self.new_pid_map[pid]:
                    self.new_pid_map[pid]["ppid"] = sub_sample[pid]["ppid"]
                    self.new_pid_map[pid]["pgrp"] = sub_sample[pid]["pgrp"]
                
                sample[pid] = sub_sample[pid]
                
        return sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()
        # Creating figure
        cm = 1/2.54                                         # centimeters in inches
        fig, axs = plt.subplots(2, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:

            pivot_table_1 = self.data_frame.pivot_table(index='time', columns=[self.key], values='load')
            pivot_table_1 = pivot_table_1.loc[:, (pivot_table_1 > 0).any()]
            
            pivot_table_2 = self.data_frame.pivot_table(index='time', columns=[self.key], values='rss')
            pivot_table_2 = pivot_table_2.loc[:, (pivot_table_2 > 0).any()]
            
            for i in pivot_table_1.columns:

                if i not in self.new_pid_map:
                    continue

                axs[0].plot( pivot_table_1[[i]].dropna() * 100.0, label="%s/%s/%s : %s" % (i,self.new_pid_map[i]['ppid'],self.new_pid_map[i]['pgrp'], self.new_pid_map[i]['cmdline'][0:99] ) )
                axs[0].set_ylabel("Process Load [%]")
                axs[0].legend(title="pid/ppid/pgrp: cmdline", fontsize='xx-small', loc= 'upper right')
                axs[0].grid()
                axs[0].set_xlim(0,maxT)
                axs[0].set_ylim(0,105.0)

                MB_per_page =  0.000001 * PAGESIZE

                axs[1].plot( pivot_table_2[[i]].dropna() * MB_per_page, label="%s/%s/%s : %s" % (i,self.new_pid_map[i]['ppid'],self.new_pid_map[i]['pgrp'], self.new_pid_map[i]['cmdline'][0:99] ) )
                axs[1].set_xlabel("Time t [s]")
                axs[1].set_ylabel("Process Memory [MB]")
                axs[1].grid()
                axs[1].set_xlim(0,maxT)
                axs[1].set_ylim(0,105.0)

        pdf.savefig(fig)