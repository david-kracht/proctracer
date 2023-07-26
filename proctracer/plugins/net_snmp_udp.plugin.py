from matplotlib import pyplot as plt

from plugin_proc_tracer_base import ProcTracerBase

class net_snmp_udp(ProcTracerBase):

    def __init__(self, config_yaml):
        super().__init__(
            config_yaml=config_yaml,
            file='/proc/net/snmp',
            key='Protocol',
            header_in='Protocol InDatagrams NoPorts InErrors OutDatagrams RcvbufErrors SndbufErrors InCsumErrors IgnoredMulti MemErrors',
            patterns='Udp:',
            anti_patterns='InDatagrams'
            )

    def mapper(self, sample):
        new_sample={}
        for k,entry in sample.items():
            new_sample[k] = {
                self.key : k,
                'time': entry['time'],
                'InDatagrams': int(entry['InDatagrams']),
                'NoPorts': int(entry['NoPorts']),
                'InErrors': int(entry['InErrors']),
                'RcvbufErrors': int(entry['RcvbufErrors']),
                'OutDatagrams': int(entry['OutDatagrams']),
                'SndbufErrors': int(entry['SndbufErrors']),
                'InSum' : int(entry['InDatagrams']) + int(entry['InErrors']),
                'InErrorRate' : 0.0
                }
                 
            if k in self.sample_old:
                if new_sample[k]['InSum'] != self.sample_old[k]['InSum']:
                    new_sample[k]['InErrorRate'] = 1.0*( new_sample[k]['InErrors'] - self.sample_old[k]['InErrors'] ) / ( new_sample[k]['InSum'] - self.sample_old[k]['InSum'] )      
                 
                 
        return new_sample

    def add_diagrams(self, pdf, maxT):

        plt.clf()

        # Creating figure
        cm = 1/2.54                                                     # inches per centimeters
        fig, axs = plt.subplots(3, dpi=72, figsize=(29.7*cm,21.0*cm))   # for landscape DIN A4

        fig.suptitle('%s' % self.file )

        if not self.data_frame.empty:

            self.data_frame.set_index('time',inplace=True)
            del self.data_frame[self.key]

            ######### Ratio 1
            #x=self.data_frame[["InErrors","RcvbufErrors"]].div(self.data_frame.InDatagrams, axis=0) # relative count wrt. start time
            x=self.data_frame[["InErrorRate"]] # 

            axs[1].plot( x *100.0, label= "InErrorRate")
            axs[1].legend()
                
            axs[1].set_ylabel('Ratio [%]')
            axs[1].grid()
            axs[1].set_xlim(0,maxT)
            axs[1].set_ylim(0,None)

            ######### Ratio 2
            x=self.data_frame[["SndbufErrors"]].div(self.data_frame.OutDatagrams, axis=0) # relative count wrt. start time

            axs[2].plot( x *100.0 , label= "SndbufErrors")
            axs[2].legend()
                
            axs[2].set_ylabel('Ratio [%]')
            axs[2].grid()
            axs[2].set_xlim(0,maxT)
            axs[2].set_ylim(0,None)

            ######### Counts
            self.data_frame -= self.data_frame.iloc[0].values.squeeze() # relative count wrt. start time
            
            axs[0].plot( self.data_frame , label= self.data_frame.columns)
            axs[0].legend()
                
            axs[0].set_ylabel('Datagrams [count]')
            axs[0].grid()
            axs[0].set_xlim(0,maxT)
            axs[0].set_ylim(0,None)

        pdf.savefig(fig)
