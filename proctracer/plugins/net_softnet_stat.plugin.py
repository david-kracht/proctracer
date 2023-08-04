from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

class net_softnet_stat(ProcTracerBase):

    def __init__(self,config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/net/softnet_stat',
            key='cpu',
            header_in='packet_process packet_drop time_squeeze cpu_collision received_rps flow_limit_count softnet_backlog_len cpu',
            first_line=0,
            patterns=''
            )
    '''
    https://insights-core.readthedocs.io/en/latest/shared_parsers_catalog/softnet_stat.html
    Column-01: packet_process: Packet processed by each CPU.
    Column-02: packet_drop: Packets dropped.
    Column-03: time_squeeze: net_rx_action.
    Column-09: cpu_collision: collision occur while obtaining device lock while transmitting.
    Column-10: received_rps: number of times cpu woken up received_rps.
    Column-11: flow_limit_count: number of times reached flow limit count.
    Column-12: softnet_backlog_len: Backlog status
    Column-13: index: core id owning this softnet_data
    '''
    
    def mapper(self, sample):
        new_sample={}
        for k,entry in sample.items():
          
            k=int(k,16)
            
            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'packet_process' : int(entry['packet_process'],16),
                'packet_drop': int(entry['packet_drop'],16),
                'time_squeeze': int(entry['time_squeeze'],16),
                'cpu_collision' : int(entry['cpu_collision'],16),
                'received_rps' : int(entry['received_rps'],16),
                'flow_limit_count': int(entry['flow_limit_count'],16),
                'softnet_backlog_len' : int(entry['softnet_backlog_len'],16),
                'cpu': int(entry['cpu'],16) ,
                'packet_drop-per-sec' : 0.0
                }

            if k in self.sample_old:
                new_sample[k]['packet_drop-per-sec'] = 1.0*( new_sample[k]['packet_drop'] - self.sample_old[k]['packet_drop'] ) / ( new_sample[k]['time'] - self.sample_old[k]['time'] )
                if new_sample[k]['packet_drop-per-sec'] < 0:
                    new_sample[k]['packet_drop-per-sec']=0
                    
        return new_sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()
        # Creating figure
        cm = 1/2.54                                         # centimeters in inches
        fig, axs = plt.subplots(3, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:
            
            pivot_table=[]
            
            ######### 
            maxV=0
            for value in 'packet_process'.split():
                pivot_table = self.data_frame.pivot_table(index='time', columns=['cpu'], values=value)
                pivot_table -= pivot_table.iloc[0].values.squeeze() # relative count wrt. start time
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for i in pivot_table.columns:
                    axs[0].plot( pivot_table[[i]].dropna(), label="%s , %s" % (i, value ) )
                
            if not pivot_table.columns.empty:
                axs[0].legend(fontsize='xx-small', loc= 'upper right')
                 
            axs[0].set_ylabel('Packets [count]')
            axs[0].grid()
            axs[0].set_xlim(0,maxT)
            axs[0].set_ylim(0,maxV*1.05+0.01)

            ######### 
            maxV=0
            for value in ['packet_drop']:
                pivot_table = self.data_frame.pivot_table(index='time', columns=['cpu'], values=value)
                pivot_table -= pivot_table.iloc[0].values.squeeze() # relative count wrt. start time
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for i in pivot_table.columns:
                    axs[1].plot( pivot_table[[i]].dropna(), label=i )
            
            if not pivot_table.columns.empty:
                axs[1].legend(fontsize='xx-small', loc= 'upper right')
            
            axs[1].set_ylabel('Packet Drops [count]')
            axs[1].grid()
            axs[1].set_xlim(0,maxT)
            axs[1].set_ylim(0,maxV*1.05+0.01)
            
            #########
            maxV=0
            for value in ['flow_limit_count', 'softnet_backlog_len']:
                pivot_table = self.data_frame.pivot_table(index='time', columns=['cpu'], values=value)
                pivot_table = pivot_table.loc[:, (pivot_table > 0).any()]
                maxV=max(maxV, pivot_table.max(axis=1).max(axis=0))
                
                for i in pivot_table.columns:
                    axs[2].plot( pivot_table[[i]].dropna(), label=i )

            if not pivot_table.columns.empty:
                axs[2].legend(fontsize='xx-small', loc= 'upper right')

            axs[2].set_xlabel('Time t [s]')
            axs[2].set_ylabel('Counts / Length ')
            axs[2].grid()
            axs[2].set_xlim(0,maxT)
            axs[2].set_ylim(0,maxV*1.05+0.01)

        pdf.savefig(fig)