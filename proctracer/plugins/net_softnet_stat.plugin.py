from math import sqrt
from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

class net_softnet_stat(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/net/softnet_stat',
            key='index',
            header_in='processed dropped time_squeeze -c4- -c5- -c6- -c7- -c8- -c9- received_rps flow_limit_count softnet_backlog_len index',
            patterns=''
            )
    '''
    https://insights-core.readthedocs.io/en/latest/shared_parsers_catalog/softnet_stat.html
    sd->processed, is the number of network frames processed. This can be more than the total number of network frames received if you are using ethernet bonding. There are cases where the ethernet bonding driver will trigger network data to be re-processed, which would increment the sd->processed count more than once for the same packet.
    sd->dropped, is the number of network frames dropped because there was no room on the processing queue. More on this later.
    sd->time_squeeze, is (as we saw) the number of times the net_rx_action loop terminated because the budget was consumed or the time limit was reached, but more work could have been. Increasing the budget as explained earlier can help reduce this.
    The next 5 values are always 0.
    sd->cpu_collision, is a count of the number of times a collision occurred when trying to obtain a device lock when transmitting packets. This article is about receive, so this statistic will not be seen below.
    sd->received_rps, is a count of the number of times this CPU has been woken up to process packets via an Inter-processor Interrupt
    flow_limit_count, is a count of the number of times the flow limit has been reached. Flow limiting is an optional Receive Packet Steering feature that will be examined shortly.
    '''
    
    def mapper(self, sample):
        new_sample={}
        for k,entry in sample.items():

            k=int(entry['index'],16)
            
            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'processed' : int(entry['processed'],16),
                'dropped': int(entry['dropped'],16),
                'time_squeeze': int(entry['time_squeeze'],16),
                'received_rps' : int(entry['received_rps'],16),
                'flow_limit_count': int(entry['flow_limit_count'],16),
                'softnet_backlog_len' : int(entry['softnet_backlog_len'],16),
                }
                    
        return new_sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()
        # Creating figure
        cm = 1/2.54                                         # centimeters in inches
        fig, axs = plt.subplots(6, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:
            
            pivot_table=[]
            i=0
            values = 'processed dropped time_squeeze received_rps flow_limit_count softnet_backlog_len'.split()
            for value in values:
           
                maxV=0
                pivot_table = self.data_frame.pivot_table(index='time', columns=['index'], values=value)
                if i == 0:
                    pivot_table -= pivot_table.iloc[0].values.squeeze() # relative count wrt. start time
                
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for j in pivot_table.columns:
                    axs[i].plot( pivot_table[[j]].dropna(), label="cpu%s" % j )
                
                if axs[i].lines:
                    axs[i].legend(title="cpu", ncol=int(sqrt(len(pivot_table.columns))) , fontsize='xx-small', loc= 'upper right')
                axs[i].set_ylabel('%s' % value, fontsize='x-small', rotation=0)
                axs[i].grid()
                
                if (i+1)<len(values):
                    axs[i].set_xticklabels([])
                else:
                    axs[i].set_xlabel("Time t [s]")
                
                
                axs[i].set_yscale('log')
                axs[i].set_xlim(0,maxT)
                axs[i].set_ylim(None,maxV*1.05+0.01)
                
                i+=1

        pdf.savefig(fig)